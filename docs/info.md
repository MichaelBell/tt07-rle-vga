<!---

This file is used to generate your project datasheet. Please fill in the information below and delete any unused
sections.

You can also include images in this folder and reference them in the markdown. Each image must be less than
512 kb in size, and the combined size of all images must be less than 1 MB.
-->

## How it works

A 6bpp run length encoded image or video is read from a W25Q128JV or similar QSPI flash, and output to 640x480 VGA.

This is perfect for displaying the Bad Apple music video.
![A frame from Bad Apple, rendered by the FPGA version of this design](badapple.jpg)

## How to test

Create a RLE binary file (docs/scripts to do this TBD) and load onto the flash.  The pinout matches the [QSPI PMOD](https://github.com/mole99/qspi-pmod).  Connect that to the bidi pins.  Note the flash must support the h6B Fast Read Quad Output command, with 8 dummy cycles between address and data.

Connect the [Tiny VGA PMOD](https://github.com/mole99/tiny-vga) to the output pins.

Inputs 2-0 set the read latency for the SPI in half clock cycles, it's likely that will need to be set to 2 (set input 1 high and inputs 0 and 2 low).  This latency depends on the total round trip time through the mux and out to the flash and back.  Valid values are 0 to 4.

Run with a 25MHz clock (or ideally 25.175MHz).

## External hardware

* [QSPI PMOD](https://github.com/mole99/qspi-pmod)
* [Tiny VGA PMOD](https://github.com/mole99/tiny-vga)
