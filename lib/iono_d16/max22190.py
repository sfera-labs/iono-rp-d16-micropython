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
from iono_d16.utils import *
from iono_d16.spi import *

class Max22190:
    _REG_WB = const(0x00)
    _REG_FAULT1 = const(0x04)
    _REG_FAULT2 = const(0x1C)
    _REG_FLT1 = const(0x06)
    _REG_FAULT2EN = const(0x1E)

    def _crc(data2, data1, data0):
        length = 19          # 19-bit data
        crc_init = 0x07      # 5-bit init word, constant, 00111
        crc_poly = 0x35      # 6-bit polynomial, constant, 110101
        crc_step = 0
        tmp = 0

        datainput = (data2 << 16) + (data1 << 8) + data0
        datainput = (datainput & 0xffffe0) + crc_init
        tmp = ((datainput & 0xfc0000) >> 18) & 0xff
        if tmp & 0x20 == 0x20:
            crc_step = (tmp ^ crc_poly) & 0xff
        else:
            crc_step = tmp

        for i in range(length - 1):
            tmp = (((crc_step & 0x1f) << 1) + ((datainput >> (length - 2 - i)) & 0x01)) & 0xff
            if tmp & 0x20 == 0x20:
                crc_step = (tmp ^ crc_poly) & 0xff
            else:
                crc_step = tmp

        return crc_step & 0x1f

    def __init__(self, pinCs):
        self._pinCs = MPin(pinCs, MPin.OUT, None)
        self._pinCs(1)
        self._error = False
        self._inputs = 0
        self._wb = 0
        self._fault1 = 0
        self._fault2 = 0
        self._cfgFlt = [0] * 8
        self._faultMemWb = 0
        self._faultMemAlrmT1 = 0
        self._faultMemAlrmT2 = 0
        self._faultMemOtshdn = 0

    def init(self):
        return self._writeReg(_REG_FAULT2EN, 0x3f)

    def _spiTransaction(self, data1, data0):
        crc = Max22190._crc(data1, data0, 0)
        for i in range(3):
            if (i != 0):
                DEBUG("max22190 repeat")
            with Spi.mutex:
                r1, r0, rcrc = Spi.transaction(self._pinCs, data1, data0, crc)
            if ((rcrc & 0x1f) == Max22190._crc(r1, r0, rcrc)):
                return (r1, r0)
        raise Exception("max22190 i2c error")

    def _readReg(self, regAddr):
        DEBUG(f"max22190 {self._pinCs} read reg={regAddr}")
        try:
            data1, data0 = self._spiTransaction(regAddr, 0)
            self._error = False
            self._inputs = data1
            return data0
        except Exception as e:
            self._error = True
            raise e

    def _writeReg(self, regAddr, val):
        DEBUG(f"max22190 {self._pinCs} write reg={regAddr} val=0x{val:x}")
        self._spiTransaction(0x80 | regAddr, val)
        return self._readReg(regAddr) == val

    def mode(self, idx, wb):
        regAddr = _REG_FLT1 + (idx * 2)
        self._cfgFlt[idx] = (self._cfgFlt[idx] & 0x0f) | (0x10 if wb else 0x00)
        return self._writeReg(regAddr, self._cfgFlt[idx])

    def updateWb(self):
        self._wb = self._readReg(_REG_WB)
        self._faultMemWb |= self._wb

    def updateFault1(self):
        self._fault1 = self._readReg(_REG_FAULT1)
        self._faultMemAlrmT1 |= 0xff if getBit(self._fault1, 3) else 0x00
        self._faultMemAlrmT2 |= 0xff if getBit(self._fault1, 4) else 0x00

    def updateFault2(self):
        if getBit(self._fault1, 5):
            self._fault2 = self._readReg(_REG_FAULT2)
            self._faultMemOtshdn |= 0xff if getBit(self._fault2, 4) else 0x00
