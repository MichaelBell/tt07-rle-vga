#!/usr/bin/env python3

import sys
import struct
from PIL import Image

out_file = open("ttlogo.bin", "wb")

img = Image.open("ttlogo_3000.png").resize((480,480))

data = img.load()
last_spans = []
repeat_count = 0
max_span_len = 8

for y in range(479):
    spans = []
    span_len = 80
    span_colour = 0
    for x in range(480):
        colour = 0
        if data[x, y][0] > 170:   colour = colour | 0b110000
        elif data[x, y][0] > 100: colour = colour | 0b100000
        elif data[x, y][0] > 45:  colour = colour | 0b010000
        if data[x, y][1] > 170:   colour = colour | 0b001100
        elif data[x, y][1] > 100: colour = colour | 0b001000
        elif data[x, y][1] > 45:  colour = colour | 0b000100
        if data[x, y][2] > 170:   colour = colour | 0b000011
        elif data[x, y][2] > 100: colour = colour | 0b000010
        elif data[x, y][2] > 45:  colour = colour | 0b000001

        if colour != span_colour:
            if span_len > 1:
                spans.append([span_len, span_colour])
                span_len = 0
            span_colour = colour

        span_len += 1

    if True:
        if span_colour != 0:
            spans.append([span_len, span_colour])
            span_colour = 0
            span_len = 80
        else:
            span_len += 80

        spans.append([span_len, span_colour])
    else:
        if span_len > 1:
            spans.append([span_len, span_colour])
        else:
            spans[-1][0] += 1

    if len(spans) > 3:
        while True:
            shortest_spans = 640
            shortest_idx = 0
            for idx, s in enumerate(spans[1:-1]):
                slen = s[0] + spans[idx][0] + spans[idx+2][0]

                if slen < shortest_spans:
                    shortest_idx = idx + 1
                    shortest_spans = slen
        
            if shortest_spans >= 3 * max_span_len:
                break

            shortest_span, idx = min((a, i) for (i, a) in enumerate([s[0] for s in spans[shortest_idx-1:shortest_idx+2]]))
            shortest_idx += idx - 1

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

            if sum([s[0] for s in spans]) != 640:
                #print(spans)
                print("Error")
                sys.exit(0)

            if len(spans) <= 3:
                break

    if spans == last_spans:
        repeat_count += 1
    else:
        if repeat_count != 0:
            out_file.write(struct.pack('>H', 0xf800 + repeat_count))
        repeat_count = 0
        for span in spans:
            out_file.write(struct.pack('>H', (span[0] << 6) + span[1]))
        last_spans = spans

if repeat_count != 0:
    out_file.write(struct.pack('>H', 0xf800 + repeat_count))

out_file.write(struct.pack('>H', (0x3ff << 6)))