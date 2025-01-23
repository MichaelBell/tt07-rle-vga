import time
import sys
import rp2
import machine
from machine import UART, Pin, PWM, SPI

from ttcontrol import *

import flash_prog

@rp2.asm_pio(autopush=True, push_thresh=32, in_shiftdir=rp2.PIO.SHIFT_RIGHT)
def pio_capture():
    in_(pins, 8)
    
def run(query=True, stop=True):
    machine.freq(100_000_000)

    select_design(969)
    
    enable_ui_in(True)
    ui_in[0].on()
    ui_in[1].off()
    ui_in[2].off()
    ui_in[3].on()

    if query:
        input("Reset? ")

    clk = Pin(GPIO_PROJECT_CLK, Pin.OUT, value=0)
    rst_n = Pin(GPIO_PROJECT_RST_N, Pin.OUT, value=1)

    clk.off()
    rst_n.on()
    time.sleep(0.001)
    rst_n.off()

    clk.on()
    time.sleep(0.001)
    clk.off()
    time.sleep(0.001)

    for i in range(10):
        clk.off()
        time.sleep(0.001)
        clk.on()
        time.sleep(0.001)

    rst_n.on()
    time.sleep(0.001)
    clk.off()

    sm = rp2.StateMachine(1, pio_capture, 50_000_000, in_base=Pin(21))

    capture_len=1024
    buf = bytearray(capture_len)

    rx_dma = rp2.DMA()
    c = rx_dma.pack_ctrl(inc_read=False, treq_sel=5) # Read using the SM0 RX DREQ
    sm.restart()
    sm.exec("wait(%d, gpio, %d)" % (1, GPIO_UIO[3]))
    rx_dma.config(
        read=0x5020_0024,        # Read from the SM1 RX FIFO
        write=buf,
        ctrl=c,
        count=capture_len//4,
        trigger=True
    )
    sm.active(1)

    if query:
        input("Start? ")

    time.sleep(0.001)
    clk = PWM(Pin(GPIO_PROJECT_CLK), freq=25_000_000, duty_u16=32768)

    # Wait for DMA to complete
    while rx_dma.active():
        time.sleep_ms(1)
        
    sm.active(0)
    del sm

    if not stop:
        return

    if query:
        input("Stop? ")

    del clk
    rst_n.init(Pin.IN, pull=Pin.PULL_DOWN)
    clk = Pin(GPIO_PROJECT_CLK, Pin.IN, pull=Pin.PULL_DOWN)

    if True:
        for j in range(8):
            print("%02d: " % (j+21,), end="")
            for d in buf:
                print("-" if (d & (1 << j)) != 0 else "_", end = "")
            print()

        print("SD: ", end="")
        for d in buf:
            nibble = ((d >> 1) & 1) | ((d >> 1) & 2) | ((d >> 2) & 0x4) | ((d >> 2) & 0x8)
            print("%01x" % (nibble,), end="")
        print()

def execute(filename):
    flash_prog.program(filename)
    run(query=False, stop=False)
