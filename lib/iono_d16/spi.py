'''
Iono RP D16 library

    Copyright (C) 2022-2023 Sfera Labs S.r.l. - All rights reserved.

    For information, see:
    http://www.sferalabs.cc/

This code is free software; you can redistribute it and/or
modify it under the terms of the GNU Lesser General Public
License as published by the Free Software Foundation; either
version 2.1 of the License, or (at your option) any later version.
See file LICENSE.txt for further informations on licensing terms.
'''

from machine import Pin as MPin
from machine import SPI as MSPI
import _thread
import time
from iono_d16.utils import DEBUG

class Spi:
    PIN_SPI_SCK = const(2)
    PIN_SPI_TX = const(3)
    PIN_SPI_RX = const(4)

    def init():
        Spi._spi = MSPI(0, baudrate=1000000, bits=8, firstbit=MSPI.MSB,
                        sck=MPin(PIN_SPI_SCK), mosi=MPin(PIN_SPI_TX),
                        miso=MPin(PIN_SPI_RX))
        Spi.mutex = _thread.allocate_lock()

    def transaction(cs, d2, d1, d0):
        DEBUG(f">>> {cs}: 0x{d2:x} 0x{d1:x} 0x{d0:x}")
        data = bytearray([d2, d1, d0])
        cs(0)
        time.sleep_us(1)
        Spi._spi.write_readinto(data, data)
        time.sleep_us(1)
        cs(1)
        DEBUG(f"<<< {cs}: 0x{data[0]:x} 0x{data[1]:x} 0x{data[2]:x}")
        return tuple(data)
