#!/bin/bash

mpremote connect /dev/ttyACM0 + mount . + exec "import os; os.chdir('/'); import flash_prog; flash_prog.program('/remote/badapple640x480.bin')"
