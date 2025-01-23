# Running Bad Apple

Plug the [QSPI Pmod](https://github.com/mole99/qspi-pmod) into the BIDIR port, and the [TinyVGA Pmod](https://github.com/mole99/tiny-vga) into the OUTPUT port on the TT07 demo board.

Plug the TT07 demo board into your computer and upload the 4 python files in this directory:

    mpremote a0 fs cp *.py :

(changing `a0` as appropriate for the tty your device is connected to)

Download the RLE encoded Bad Apple video:

    wget http://lion.rddev.co.uk/tt07-badapple640x480.bin

Program it to the flash 

    mpremote a0 + mount . + exec "import os; os.chdir('/'); import flash_prog ; flash_prog.program('/remote/tt07-badapple640x480.bin')"

This will take a few minutes.

Run the project.  This can either be done through commander (set inputs 0 and 3 high), or using the script:

    mpremote a0 exec "import run_rle ; run_rle.run(False, False)"
