package main

import (
	"encoding/json"
	"machine"
	"strconv"
	"time"

	"tinygo.org/x/drivers/ssd1306"
	"tinygo.org/x/tinydraw"
	"tinygo.org/x/tinyfont"
	"tinygo.org/x/tinyfont/proggy"
)

var (
	LedPin  machine.Pin
	Display ssd1306.Device

	CurrentTrack Track
)

func init() {
	// Configure the onboard LED
	LedPin = machine.LED
	LedPin.Configure(machine.PinConfig{Mode: machine.PinOutput})

	// Configure the I2C bus and the OLED display
	machine.I2C0.Configure(machine.I2CConfig{
		Frequency: machine.KHz * 400,
		SDA:       machine.Pin(16),
		SCL:       machine.Pin(17),
	})
	Display = ssd1306.NewI2C(machine.I2C0)
	Display.Configure(ssd1306.Config{
		Address:  ssd1306.Address_128_32,
		VccState: ssd1306.SWITCHCAPVCC,
		Width:    128,
		Height:   64,
	})
}

func main() {
	go drawScreen()
	go scanSerial()

	for {
		// Do nothing forever
		time.Sleep(time.Second * 1)
	}
}

func scanSerial() {
	const (
		sleepTime           = time.Millisecond * 100
		dataTransferTimeout = time.Second * 4
	)

	type track struct {
		Name   string `json:"name"`
		Album  string `json:"album"`
		Artist string `json:"artist"`
		Length string `json:"length"`
	}
	type data struct {
		Track    track  `json:"track,omitempty"`
		Progress string `json:"progress,omitempty"`
		Art      []int  `json:"art,omitempty"`
	}

	for {
		var (
			err       error
			buffer    []byte
			bufferLen int
		)

		// Wait for a byte to be available
		for machine.Serial.Buffered() == 0 {
			time.Sleep(sleepTime)
		}

		// Get initial hello data
		for machine.Serial.Buffered() > 0 {
			readByte, err := machine.Serial.ReadByte()
			if err != nil {
				// Error occurred, meaning json will probably be malformed
				println("Error reading byte: ", err)
				continue
			}
			buffer = append(buffer, readByte)
		}

		// check if data is #numbers# format
		if buffer[0] != '#' && buffer[len(buffer)-1] != '#' {
			println("Hello data not in correct format")
			continue
		}
		bufferLen, err = strconv.Atoi(string(buffer[1 : len(buffer)-1]))
		if err != nil {
			println("Hello does not contain numbers")
			continue
		}

		// Clear buffer and let the master know we're ready
		buffer = nil
		println("OK")

		// Start reading data
		now := time.Now()
		for len(buffer) < bufferLen {
			// Wait a moment for the data to start coming in
			//time.Sleep(time.Millisecond * 1)

			// read all available bytes
			for machine.Serial.Buffered() > 0 {
				readByte, err := machine.Serial.ReadByte()
				if err != nil {
					// Error occurred, meaning json will probably be malformed
					println("Error reading byte: ", err)
					continue
				}
				buffer = append(buffer, readByte)
			}

			if time.Since(now) > dataTransferTimeout {
				break
			}
		}
		if time.Since(now) > dataTransferTimeout {
			println("Timed out data transfer")
			println(string(buffer))
			//continue
		}
		if len(buffer) != bufferLen {
			println("Buffer length does not match expected length, trying anyway")
			//continue
		}

		var parsedTrackData data
		if err := json.Unmarshal(buffer, &parsedTrackData); err != nil {
			println("Error unmarshalling JSON: ", err)
			println(string(buffer))
			continue
		}

		if parsedTrackData.Track != (track{}) {
			println("Setting track data")
			length, err := time.ParseDuration(parsedTrackData.Track.Length)
			if err != nil {
				println("Error parsing duration: ", err)
				continue
			}
			CurrentTrack = NewTrack(parsedTrackData.Track.Name, parsedTrackData.Track.Album, parsedTrackData.Track.Artist, length)
		}

		if parsedTrackData.Progress != "" {
			println("Setting progress data")
			progress, err := time.ParseDuration(parsedTrackData.Progress)
			if err != nil {
				println("Error parsing progress: ", err)
				continue
			}
			CurrentTrack.SetProgress(time.Now().Add(-progress))
		}

		if parsedTrackData.Art != nil {
			println("Setting art data")
			CurrentTrack.SetArt(parsedTrackData.Art)
		}
	}
}

func drawScreen() {
	CurrentTrack = NewTrack("No Music", "Unknown Album", "Nobody", time.Minute*612)

	Display.ClearBuffer()
	Display.ClearDisplay()
	Display.Display()

	for {
		// Get track info
		trackProgress := fmtDuration(time.Since(CurrentTrack.GetProgress()).Round(time.Second))
		trackLength := fmtDuration(CurrentTrack.Length.Round(time.Second))
		lineLength := int16(128 * CurrentTrack.GetProgressFloat())

		Display.ClearBuffer()

		// Album art
		tinydraw.Rectangle(&Display, 0, 0, 45, 45, White)
		for i, b := range CurrentTrack.Art {
			if b == 0 {
				Display.SetPixel(int16(i%45), int16(i/45), Black)
			} else {
				Display.SetPixel(int16(i%45), int16(i/45), White)
			}
		}

		// Track info
		tinyfont.WriteLine(&Display, &proggy.TinySZ8pt7b, 48, 6, CurrentTrack.Name, White)
		tinyfont.WriteLine(&Display, &proggy.TinySZ8pt7b, 48, 6+11, "By "+CurrentTrack.Artist, White)
		tinyfont.WriteLine(&Display, &proggy.TinySZ8pt7b, 48, 6+22, "On "+CurrentTrack.Album, White)

		// GetProgressFloat bar
		tinyfont.WriteLine(&Display, &proggy.TinySZ8pt7b, 0, 55, trackProgress+"/"+trackLength, White)
		tinydraw.FilledRectangle(&Display, 0, 61, lineLength, 3, White)

		// Update buffer
		Display.Display()

		// Delay, too fast and we'll mess up the buffer
		time.Sleep(time.Millisecond * 500)
	}
}
