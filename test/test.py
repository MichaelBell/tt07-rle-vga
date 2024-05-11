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
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1

    dut._log.info("Test sync")

    assert dut.uio_oe.value == 0b11001011

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
    
    cmd = 3
    for i in range(8):
        await ClockCycles(dut.spi_clk, 1)
        assert dut.spi_mosi.value == (1 if cmd & 0x80 else 0)
        assert dut.spi_cs.value == 0
        cmd <<= 1

    for i in range(24):
        await ClockCycles(dut.spi_clk, 1)
        assert dut.spi_mosi.value == (1 if addr & 0x800000 else 0)
        assert dut.spi_cs.value == 0
        addr <<= 1

    await FallingEdge(dut.spi_clk)

async def spi_send_rle(dut, length, colour, latency):
    data = (length << 6) + colour

    assert dut.spi_cs.value == 0

    for j in range(latency//2):
        await FallingEdge(dut.spi_clk)


    for i in range(16 - latency//2):
        if latency & 1:
            await RisingEdge(dut.spi_clk)
        await Timer(1, "ns")
        dut.spi_miso.value = (1 if data & 0x8000 else 0)
        assert dut.spi_cs.value == 0
        await FallingEdge(dut.spi_clk)
        data <<= 1

    if latency & 1:
        await Timer(20, "ns")
    await Timer(1, "ns")

    for j in range(latency//2):
        dut.spi_miso.value = (1 if data & 0x8000 else 0)
        await Timer(40, "ns")
        data <<= 1

async def generate_colours(dut, frames, latency=0):
    for f in range(frames):
        await expect_read_cmd(dut, 0)

        for colour in range(64):
            await spi_send_rle(dut, 640, colour, latency)

        colour = 20
        for i in range(2, 640, 2):
            await spi_send_rle(dut, i, colour, latency)
            colour += 1
            if colour == 64: colour = 0
            await spi_send_rle(dut, 640-i, colour, latency)
            colour += 1
            if colour == 64: colour = 0

        for i in range(480-64-319):
            for j in range(640//20):
                await spi_send_rle(dut, 20, j, latency)

        await spi_send_rle(dut, 0x3ff, 0, latency)
        await RisingEdge(dut.spi_cs)

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
            for j in range(640//20):
                for k in range(20):
                    assert dut.colour.value == j
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
                for j in range(640//20):
                    for k in range(20):
                        assert dut.colour.value == j
                        await ClockCycles(dut.clk, 1)
                await ClockCycles(dut.hsync, 1)

        await colour_gen
