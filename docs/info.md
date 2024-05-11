<!---

This file is used to generate your project datasheet. Please fill in the information below and delete any unused
sections.

You can also include images in this folder and reference them in the markdown. Each image must be less than
512 kb in size, and the combined size of all images must be less than 1 MB.
-->

## How it works

A 6bpp run length encoded image or video is read from an SPI flash, and output to 640x480 VGA.

## How to test

Create a RLE binary file (docs/scripts to do this TBD) and load onto a flash PMOD (e.g. the [QSPI PMOD](https://github.com/mole99/qspi-pmod)).  Connect that to the bidi pins.

Connect the [Tiny VGA PMOD](https://github.com/mole99/tiny-vga) to the output pins.

Run with a 25MHz clock (or ideally 25.175MHz).

## External hardware

* SPI flash
* [Tiny VGA PMOD](https://github.com/mole99/tiny-vga)
