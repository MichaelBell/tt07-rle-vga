# SPDX-FileCopyrightText: © 2024 Michael Bell
# SPDX-License-Identifier: MIT

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, FallingEdge, RisingEdge, Timer


@cocotb.test()
async def test_sync(dut):
    dut._log.info("Start")

    # Set the clock period to 40 ns (25 MHz)
    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())

    # Reset
    dut._log.info("Reset")
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.spi_miso.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 2)
    assert dut.uio_oe.value == 0
    await ClockCycles(dut.clk, 2)
    dut.rst_n.value = 1

    dut._log.info("Test sync")

    await Timer(1, "ns")
    assert dut.uio_oe.value == 0b11001001

    await ClockCycles(dut.clk, 1)

    for i in range(16):
        vsync = 0 if i in (10, 11) else 1
        for j in range(16):
            assert dut.vsync.value == vsync
            assert dut.hsync.value == 1
            await ClockCycles(dut.clk, 1)
        for j in range(96):
            assert dut.vsync.value == vsync
            assert dut.hsync.value == 0
            await ClockCycles(dut.clk, 1)
        for j in range(48+640):
            assert dut.vsync.value == vsync
            assert dut.hsync.value == 1
            await ClockCycles(dut.clk, 1)

async def expect_read_cmd(dut, addr):
    assert dut.spi_cs.value == 1
    await FallingEdge(dut.spi_cs)

    assert dut.spi_mosi.value == 0
    
    cmd = 0x6B
    for i in range(8):
        await ClockCycles(dut.spi_clk, 1)
        assert dut.spi_mosi.value == (1 if cmd & 0x80 else 0)
        assert dut.spi_cs.value == 0
        assert dut.uio_oe.value == 0b11001011
        cmd <<= 1

    for i in range(24):
        await ClockCycles(dut.spi_clk, 1)
        assert dut.spi_mosi.value == (1 if addr & 0x800000 else 0)
        assert dut.spi_cs.value == 0
        assert dut.uio_oe.value == 0b11001011
        addr <<= 1

    for i in range(8):
        await ClockCycles(dut.spi_clk, 1)
        assert dut.spi_cs.value == 0
        assert dut.uio_oe.value == 0b11001001

    await FallingEdge(dut.spi_clk)

def spi_send_rle(dut, length, colour, latency):
    data = (length << 6) + colour

    return spi_send_data(dut, data, latency)

async def spi_send_data(dut, data, latency):
    assert dut.spi_cs.value == 0

    for j in range(latency//2):
        await FallingEdge(dut.spi_clk)
        assert dut.uio_oe.value == 0b11001001


    for i in range(4 - latency//2):
        if latency & 1:
            await RisingEdge(dut.spi_clk)
        await Timer(1, "ns")
        dut.spi_miso.value = (data >> 12) & 0xF
        assert dut.uio_oe.value == 0b11001001
        assert dut.spi_cs.value == 0
        await FallingEdge(dut.spi_clk)
        data <<= 4

    if latency & 1:
        await Timer(20, "ns")
    await Timer(1, "ns")

    for j in range(latency//2):
        dut.spi_miso.value = (data >> 12) & 0xF
        assert dut.uio_oe.value == 0b11001001
        await Timer(40, "ns")
        data <<= 4

async def generate_colours(dut, frames, latency=1):
    for f in range(frames):
        await expect_read_cmd(dut, 0)
        addr = 0

        for colour in range(64):
            await spi_send_rle(dut, 320, colour, latency)
            await spi_send_rle(dut, 2, 1, latency)
            await spi_send_rle(dut, 2, 2, latency)
            await spi_send_rle(dut, 316, colour, latency)
        addr += 8 * 64

        colour = 20
        for i in range(2, 640, 2):
            await spi_send_rle(dut, i, colour, latency)
            colour += 1
            if colour == 64: colour = 0
            await spi_send_rle(dut, 640-i, colour, latency)
            colour += 1
            if colour == 64: colour = 0
        addr += 4 * 319

        for i in range(480-64-319):
            for j in range(640//8):
                await spi_send_rle(dut, 8, j & 0x3f, latency)
            await spi_send_data(dut, 0xf800 + 480-64-319-1, latency)
            
            if (i != 480-64-319-1):
                await RisingEdge(dut.spi_cs)
                await expect_read_cmd(dut, addr)

        await spi_send_rle(dut, 0x3ff, 0, latency)
        await RisingEdge(dut.spi_cs)

async def generate_colours_continuous(dut, frames, latency=1, repeat=True):
    addr = 0
    for f in range(frames):
        if f == 0 or ((f & 1) == 1 and repeat):
            dut._log.info(f"Start data at: {addr:06x}")
            await expect_read_cmd(dut, addr)
        next_addr = addr

        for colour in range(64):
            await spi_send_rle(dut, 640, colour, latency)
        next_addr += 2 * 64

        colour = 20
        for i in range(2, 640, 2):
            await spi_send_rle(dut, i, colour, latency)
            colour += 1
            if colour == 64: colour = 0
            await spi_send_rle(dut, 640-i, colour, latency)
            colour += 1
            if colour == 64: colour = 0
        next_addr += 4 * 319

        rep_addr = next_addr
        for i in range(480-64-319):
            for j in range(640//8):
                await spi_send_rle(dut, 8, j & 0x3f, latency)
            await spi_send_data(dut, 0xf800 + 480-64-319-1, latency)
            
            if (i != 480-64-319-1):
                await RisingEdge(dut.spi_cs)
                await expect_read_cmd(dut, rep_addr)
        next_addr += (640//8 + 1) * 2

        if ((f & 1) == 0 and repeat):
            await spi_send_rle(dut, 640, 0, latency)
            await RisingEdge(dut.spi_cs)
        else:
            addr = next_addr

@cocotb.test()
async def test_colour(dut):
    dut._log.info("Start")

    # Set the clock period to 40 ns (25 MHz)
    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())

    # Reset
    dut._log.info("Reset")
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.spi_miso.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1

    colour_gen = cocotb.start_soon(generate_colours(dut, 3))

    await ClockCycles(dut.hsync, 1)

    for i in range(3):
        await ClockCycles(dut.hsync, 10+2+33)

        for colour in range(64):
            await ClockCycles(dut.clk, 49)
            for i in range(320):
                assert dut.colour.value == colour
                await ClockCycles(dut.clk, 1)
            for i in range(2):
                assert dut.colour.value == 1
                await ClockCycles(dut.clk, 1)
            for i in range(2):
                assert dut.colour.value == 2
                await ClockCycles(dut.clk, 1)
            for i in range(316):
                assert dut.colour.value == colour
                await ClockCycles(dut.clk, 1)
            await ClockCycles(dut.hsync, 1)

        colour = 20
        for i in range(2, 640, 2):
            await ClockCycles(dut.clk, 49)
            for j in range(640):
                assert dut.colour.value == (colour if j < i else colour + 1)
                await ClockCycles(dut.clk, 1)
            await ClockCycles(dut.hsync, 1)
            colour += 2
            if colour == 64: colour = 0

        for i in range(64+319, 480):
            await ClockCycles(dut.clk, 49)
            for j in range(640//8):
                for k in range(8):
                    assert dut.colour.value == j & 0x3f
                    await ClockCycles(dut.clk, 1)
            await ClockCycles(dut.hsync, 1)

    await colour_gen

@cocotb.test()
async def test_repeat(dut):
    dut._log.info("Start")

    # Set the clock period to 40 ns (25 MHz)
    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())

    # Reset
    dut._log.info("Reset")
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.spi_miso.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1
    dut.ui_in.value = 8

    colour_gen = cocotb.start_soon(generate_colours_continuous(dut, 5))

    await ClockCycles(dut.hsync, 1)

    for i in range(5):
        await ClockCycles(dut.hsync, 10+2+33)

        for colour in range(64):
            await ClockCycles(dut.clk, 49)
            for i in range(640):
                assert dut.colour.value == colour
                await ClockCycles(dut.clk, 1)
            await ClockCycles(dut.hsync, 1)

        colour = 20
        for i in range(2, 640, 2):
            await ClockCycles(dut.clk, 49)
            for j in range(640):
                assert dut.colour.value == (colour if j < i else colour + 1)
                await ClockCycles(dut.clk, 1)
            await ClockCycles(dut.hsync, 1)
            colour += 2
            if colour == 64: colour = 0

        for i in range(64+319, 480):
            await ClockCycles(dut.clk, 49)
            for j in range(640//8):
                for k in range(8):
                    assert dut.colour.value == j & 0x3f
                    await ClockCycles(dut.clk, 1)
            await ClockCycles(dut.hsync, 1)

    await colour_gen

@cocotb.test()
async def test_no_repeat(dut):
    dut._log.info("Start")

    # Set the clock period to 40 ns (25 MHz)
    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())

    # Reset
    dut._log.info("Reset")
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.spi_miso.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1

    colour_gen = cocotb.start_soon(generate_colours_continuous(dut, 3, 2, False))

    await ClockCycles(dut.hsync, 1)

    for i in range(3):
        await ClockCycles(dut.hsync, 10+2+33)

        for colour in range(64):
            await ClockCycles(dut.clk, 49)
            for i in range(640):
                assert dut.colour.value == colour
                await ClockCycles(dut.clk, 1)
            await ClockCycles(dut.hsync, 1)

        colour = 20
        for i in range(2, 640, 2):
            await ClockCycles(dut.clk, 49)
            for j in range(640):
                assert dut.colour.value == (colour if j < i else colour + 1)
                await ClockCycles(dut.clk, 1)
            await ClockCycles(dut.hsync, 1)
            colour += 2
            if colour == 64: colour = 0

        for i in range(64+319, 480):
            await ClockCycles(dut.clk, 49)
            for j in range(640//8):
                for k in range(8):
                    assert dut.colour.value == j & 0x3f
                    await ClockCycles(dut.clk, 1)
            await ClockCycles(dut.hsync, 1)

    await colour_gen

@cocotb.test()
async def test_latency(dut):
    dut._log.info("Start")

    # Set the clock period to 40 ns (25 MHz)
    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())

    for lat in range(1, 5):
        # Reset
        dut._log.info(f"Reset, latency {lat}")
        dut.ena.value = 1
        dut.ui_in.value = lat
        dut.spi_miso.value = 0
        dut.rst_n.value = 0
        await ClockCycles(dut.clk, 10)
        dut.rst_n.value = 1

        colour_gen = cocotb.start_soon(generate_colours(dut, 2, lat))

        await ClockCycles(dut.hsync, 1)

        for i in range(2):
            await ClockCycles(dut.hsync, 10+2+33)

            for colour in range(64):
                await ClockCycles(dut.clk, 49)
                for i in range(320):
                    assert dut.colour.value == colour
                    await ClockCycles(dut.clk, 1)
                for i in range(2):
                    assert dut.colour.value == 1
                    await ClockCycles(dut.clk, 1)
                for i in range(2):
                    assert dut.colour.value == 2
                    await ClockCycles(dut.clk, 1)
                for i in range(316):
                    assert dut.colour.value == colour
                    await ClockCycles(dut.clk, 1)
                await ClockCycles(dut.hsync, 1)

            colour = 20
            for i in range(2, 640, 2):
                await ClockCycles(dut.clk, 49)
                for j in range(640):
                    assert dut.colour.value == (colour if j < i else colour + 1)
                    await ClockCycles(dut.clk, 1)
                await ClockCycles(dut.hsync, 1)
                colour += 2
                if colour == 64: colour = 0

            for i in range(64+319, 480):
                await ClockCycles(dut.clk, 49)
                for j in range(640//8):
                    for k in range(8):
                        assert dut.colour.value == j & 0x3f
                        await ClockCycles(dut.clk, 1)
                await ClockCycles(dut.hsync, 1)

        await colour_gen
