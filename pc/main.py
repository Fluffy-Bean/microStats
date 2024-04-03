import time
import serial
import json
import spotify


if __name__ == "__main__":
    print("connecting to serial device...")
    ser = serial.Serial('/dev/ttyACM0', 115200)
    print(ser.portstr)

    print("connecting to spotify...")
    sp = spotify.Spotify()

    old_track = None
    old_album = None
    old_artist = None
    old_length = None
    old_progress = None
    old_art = None
    while True:
        print("getting track info...")
        try:
            track_name, album_name, artist_name, length, progress, art = sp.get_tracks()
        except spotify.Error.no_track:
            print("No track currently playing")
            time.sleep(5)
            continue

        if (
            track_name == old_track and
            album_name == old_album and
            artist_name == old_artist and
            length == old_length and
            progress == old_progress and
            art == old_art
        ):
            print("No change in track info")
            time.sleep(5)
            continue

        data = {}

        if track_name != old_track or album_name != old_album or artist_name != old_artist or length != old_length:
            data["track"] = {
                "name": track_name,
                "artist": artist_name,
                "album": album_name,
                "length": str(length) + "ms",
            }

        if progress != old_progress and progress:
            data["progress"] = str(progress) + "ms"

        if art != old_art and art:
            data["art"] = art

        print(data)

        old_track = track_name
        old_album = album_name
        old_artist = artist_name
        old_length = length
        old_progress = progress
        old_art = art

        encoded = json.dumps(data).encode()

        hello_data = "#" + str(len(encoded)) + "#"
        ser.write(hello_data.encode())

        while ser.in_waiting <= 0:
            pass
        hello_response = ser.readline().strip()
        print(hello_response)

        if hello_response != b'OK':
            print("Error: Expected OK response from device, got:", hello_response)
            ser.close()
            exit(1)

        print("Sending track info:", encoded)
        for i in range(0, len(encoded), 10):
            print("Sending bytes:", encoded[i:i+10])
            ser.write(encoded[i:i+10])
            ser.flush()
            time.sleep(0.001)

        time.sleep(5)

        while ser.in_waiting <= 0:
            pass

        while ser.in_waiting > 0:
            print(ser.readline())
