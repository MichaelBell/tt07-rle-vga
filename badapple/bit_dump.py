#!/usr/bin/env python3

import sys
import struct
from PIL import Image

out_file = open("badapple640x480.bin", "wb")

for i in range(1,5500):
    img = Image.open("frames/badapple%04d.png" % (i,)).resize((640,480))

    data = img.load()

    for y in range(0,480):
        spans = []
        span_len = 0
        span_colour = 0
        for x in range(640):
            if data[x, y][0] > 170: colour =   0b111111
            elif data[x, y][0] > 100: colour = 0b101010
            elif data[x, y][0] > 45: colour =  0b010101
            else: colour = 0
            if colour != span_colour:
                if span_len > 0:
                    spans.append([span_len, span_colour])
                span_len = 1
                span_colour = colour
            else:
                span_len += 1
        spans.append([span_len, span_colour])

        shortest_span, shortest_idx = min((a, i) for (i, a) in enumerate([s[0] for s in spans]))
        
        while shortest_span < 20:
            #print(shortest_span, shortest_idx, spans)
            if shortest_idx == 0: 
                spans[1][0] += shortest_span
                del spans[0]
            elif shortest_idx == len(spans) - 1: 
                spans[-2][0] += shortest_span
                del spans[-1]
            else:
                if spans[shortest_idx-1][0] < spans[shortest_idx+1][0]:
                    spans[shortest_idx-1][0] += shortest_span
                    del spans[shortest_idx]
                else:
                    spans[shortest_idx+1][0] += shortest_span
                    del spans[shortest_idx]
                if spans[shortest_idx][1] == spans[shortest_idx-1][1]:
                    spans[shortest_idx-1][0] += spans[shortest_idx][0]
                    del spans[shortest_idx]

            shortest_span, shortest_idx = min((a, i) for (i, a) in enumerate([s[0] for s in spans]))

        for span in spans:
            out_file.write(struct.pack('>H', (span[0] << 6) + span[1]))
    print("Frame %d" % (i,))

out_file.write(struct.pack('>H', (0x3ff << 6)))