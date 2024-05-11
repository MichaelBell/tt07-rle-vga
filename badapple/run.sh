#!/bin/bash

mpremote connect /dev/ttyACM0 + mount . + exec "import os; os.chdir('/'); import run_rle; run_rle.run(query=False, stop=False)"
