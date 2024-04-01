package main

import (
	"fmt"
	"image/color"
	"time"
)

var (
	White = color.RGBA{R: 255, G: 255, B: 255, A: 255}
	Black = color.RGBA{A: 255}
)

func fmtDuration(d time.Duration) string {
	m := d / time.Minute
	d -= m * time.Minute
	s := d / time.Second
	return fmt.Sprintf("%02d:%02d", m, s)
}
