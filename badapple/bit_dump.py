#!/usr/bin/env python3

import struct
from PIL import Image

out_file = open("badapple640x480.bin", "wb")

for i in range(1,6957):
    img = Image.open("frames/badapple%04d.png" % (i,)).resize((640,480))

    data = img.load()

    for y in range(0,480):
        span_len = 0
        span_colour = 0
        for x in range(640):
            if data[x, y][0] > 170: colour =   0b111111
            elif data[x, y][0] > 100: colour = 0b101010
            elif data[x, y][0] > 45: colour =  0b010101
            else: colour = 0
            if colour != span_colour:
                if span_len > 0:
                    out_file.write(struct.pack('>H', (span_len << 6) + span_colour))
                span_len = 1
                span_colour = colour
            else:
                span_len += 1
        out_file.write(struct.pack('>H', (span_len << 6) + span_colour))
    print("Frame %d" % (i,))