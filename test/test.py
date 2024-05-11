# SPDX-FileCopyrightText: © 2024 Michael Bell
# SPDX-License-Identifier: MIT

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, FallingEdge, RisingEdge


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
    assert (dut.uio_out.value & 0b11000000) == 0b11000000

    await ClockCycles(dut.clk, 3)

    for i in range(16):
        vsync = 0 if i in (11, 12) else 1
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

async def spi_send_rle(dut, length, colour):
    data = (length << 6) + colour

    assert dut.spi_cs.value == 0

    for i in range(16):
        dut.spi_miso.value = (1 if data & 0x8000 else 0)
        assert dut.spi_cs.value == 0
        await FallingEdge(dut.spi_clk)
        data <<= 1

async def send_row_colours(dut, colours):
    for colour in colours:
        await spi_send_rle(dut, 640, colour)

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

    await expect_read_cmd(dut, 0)

    colour_gen = cocotb.start_soon(send_row_colours(dut, [i for i in range(64)]))

    await ClockCycles(dut.hsync, 12+2+33)

    for colour in range(64):
        await ClockCycles(dut.clk, 49)
        for i in range(640):
            assert dut.colour.value == colour
        await ClockCycles(dut.hsync, 1)

    await colour_gen
    await spi_send_rle(dut, 0, 0)
    await RisingEdge(dut.spi_cs)

