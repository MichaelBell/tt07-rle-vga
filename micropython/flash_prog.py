import time
import machine
import gc
from machine import SPI, Pin

from ttcontrol import *

from pio_spi import PIOSPI

def program(filename, addr=0):
    # Select the chip ROM, which should always be present and set the bidirs to all inputs
    # so we can drive them with SPI
    select_design(0)

    flash_sel = Pin(GPIO_UIO[0], Pin.OUT)
    flash_sel.on()
    spi = PIOSPI(2, Pin(GPIO_UIO[1]), Pin(GPIO_UIO[2]), Pin(GPIO_UIO[3]), freq=10000000)

    ram_a_sel = Pin(GPIO_UIO[6], Pin.OUT)
    ram_b_sel = Pin(GPIO_UIO[7], Pin.OUT)

    flash_sel.on()
    ram_a_sel.on()
    ram_b_sel.on()

    def flash_cmd(data, dummy_len=0, read_len=0):
        dummy_buf = bytearray(dummy_len)
        read_buf = bytearray(read_len)
        
        flash_sel.off()
        spi.write(bytearray(data))
        if dummy_len > 0:
            spi.readinto(dummy_buf)
        if read_len > 0:
            spi.readinto(read_buf)
        flash_sel.on()
        
        return read_buf

    def flash_cmd2(data, data2):
        flash_sel.off()
        spi.write(bytearray(data))
        spi.write(data2)
        flash_sel.on()

    def print_bytes(data):
        for b in data: print("%02x " % (b,), end="")
        print()

    CMD_WRITE = 0x02
    CMD_READ = 0x03
    CMD_READ_SR1 = 0x05
    CMD_WEN = 0x06
    CMD_SECTOR_ERASE = 0x20
    CMD_BLOCK_ERASE = 0xD8
    CMD_ID  = 0x90
    CMD_LEAVE_CM = 0xFF

    flash_cmd([CMD_LEAVE_CM])
    id = flash_cmd([CMD_ID], 2, 3)
    print_bytes(id)
    
    gc.collect()
    
    with open(filename, "rb") as f:
    #if False:
        buf_size = 8192
        buf = bytearray(buf_size)
        sector = 0
        while sector < 65536:
            if (sector & 0xF) == 0:
                flash_cmd([CMD_WEN])
                flash_cmd([CMD_BLOCK_ERASE, sector >> 4, 0, 0])

            num_bytes = f.readinto(buf)
            while flash_cmd([CMD_READ_SR1], 0, 1)[0] & 1:
                print("*", end="")
                time.sleep(0.01)
            print(".", end="")

            if num_bytes == 0:
                break

            for i in range(0, num_bytes, 256):
                flash_cmd([CMD_WEN])
                flash_cmd2([CMD_WRITE, sector >> 4, ((sector & 0xF) << 4) + (i >> 8), 0], buf[i:min(i+256, num_bytes)])

                while flash_cmd([CMD_READ_SR1], 0, 1)[0] & 1:
                    pass
                    #print("-", end="")
                    #time.sleep(0.001)
            sector += 2
            print(f". {sector*4}kB")
            
            if num_bytes != buf_size:
                break            
        print("Program done")

    with open(filename, "rb") as f:
        data = bytearray(256)
        i = addr // 256
        while i < 20:
            num_bytes = f.readinto(data)
            if num_bytes == 0:
                break
            
            data_from_flash = flash_cmd([CMD_READ, i >> 8, i & 0xFF, 0], 0, num_bytes)
            for j in range(num_bytes):
                if data[j] != data_from_flash[j]:
                    raise Exception(f"Error at {i:02x}:{j:02x}: {data[j]} != {data_from_flash[j]}")
            i += 1

    print("Verify done")
    data_from_flash = flash_cmd([CMD_READ, 0, 0, 0], 0, 16)
    print_bytes(data_from_flash)
