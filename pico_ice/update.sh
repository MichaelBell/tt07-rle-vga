#!/bin/bash

mpremote connect /dev/ttyACM0 + mount . + exec "import os; os.chdir('/'); import fpga_flash_prog; fpga_flash_prog.program('/remote/rlevga.bin')"
