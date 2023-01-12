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

class Max14912:
    _REG_IN = const(0)
    _REG_PP = const(1)
    _REG_OL_EN = const(2)
    _REG_WD_JN = const(3)
    _REG_OL = const(4)
    _REG_THSD = const(5)
    _REG_FAULTS = const(6)
    _REG_OV = const(7)

    _CMD_SET_STATE = const(0b0)
    _CMD_SET_MODE = const(0b1)
    _CMD_SET_OL_DET = const(0b10)
    _CMD_SET_CONFIG = const(0b11)
    _CMD_READ_REG = const(0b100000)
    _CMD_READ_RT_STAT = const(0b110000)

    _PROT_OV_LOCK_MS = const(10000)
    _PROT_THSD_LOCK_MS = const(30000)

    def _crcLoop(crc, byte1):
        for i in range(8):
            crc <<= 1
            if crc & 0x80:
                crc ^= 0xB7  # 0x37 with MSBit on purpose
            if byte1 & 0x80:
                crc ^= 1
            byte1 <<= 1
        return crc

    def _crc(byte1, byte2):
        synd = Max14912._crcLoop(0x7f, byte1)
        synd = Max14912._crcLoop(synd, byte2)
        return Max14912._crcLoop(synd, 0x80) & 0x7f

    _readStatCrc = None

    def __init__(self, pinCs):
        if Max14912._readStatCrc is None:
            Max14912._readStatCrc = Max14912._crc(_CMD_READ_RT_STAT, 0)
        self._pinCs = MPin(pinCs, MPin.OUT, None)
        self._pinCs(1)
        self._error = False
        self._outputs = 0
        self._outputsUser = 0
        self._clearFaults = False
        self._ovProtEn = False
        self._ol = 0
        self._olRT = 0
        self._ovRT = 0
        self._thsd = 0
        self._thsdRT = 0
        self._cfgModePP = 0
        self._cfgModePPUser = 0
        self._cfgOlDet = 0
        self._cfgJoin = 0
        self._ovLock = 0
        self._thsdLock = 0
        self._faultMemOl = 0
        self._faultMemOv = 0
        self._faultMemThsd = 0
        self._lockTs = [0] * 8

    def _spiTransaction(self, wr, data1, data0):
        zBit = 0x80 if self._clearFaults else 0x00
        crc = Max14912._crc(zBit | data1, data0)
        for i in range(3):
            if i != 0:
                DEBUG("max14912 repeat")
            with Spi.mutex:
                r1, r0, rcrc = Spi.transaction(
                                    self._pinCs, zBit | data1, data0, crc)
                if (rcrc & 0x80) == 0x80:
                    # CRC check of previous transaction
                    DEBUG("max14912 CRC prev err")
                if wr:
                    r1, r0, rcrc = Spi.transaction(
                                        self._pinCs, _CMD_READ_RT_STAT,
                                        0, Max14912._readStatCrc)
                    if (rcrc & 0x80) == 0x80:
                        DEBUG("max14912 CRC err")
                        continue
            if (rcrc & 0x7f) == Max14912._crc(r1, r0):
                if zBit == 0x80:
                    self._clearFaults = False
                return (r1, r0)
        raise Exception("max14912 i2c error")

    def _readReg(self, regAddr):
        DEBUG(f"max14912 {self._pinCs} read reg={regAddr}")
        try:
            dataA, dataQ = self._spiTransaction(True, _CMD_READ_REG, regAddr)
            self._error = False
            return (dataA, dataQ)
        except Exception as e:
            self._error = True
            raise e

    def _cmd(self, cmd, data):
        DEBUG(f"max14912 {self._pinCs} cmd={cmd} data=0x{data:x}")
        try:
            self._spiTransaction(False, cmd, data)
            return True
        except:
            return False

    def _config(self, cmd, checkRegAddr, val):
        DEBUG(f"max14912 {self._pinCs} cfg cmd={cmd} chReg={checkRegAddr} val=0x{val:x}")
        if not self._cmd(cmd, val):
            return False
        _, cfg = self._readReg(checkRegAddr)
        if cfg != val:
            return False
        return True

    def _outputSet(self, idx, val):
        self._outputs = setBit(self._outputs, idx, val)
        return self._cmd(_CMD_SET_STATE, self._outputs)

    def _modePPSet(self, idx, val):
        self._cfgModePP = setBit(self._cfgModePP, idx, val)
        return self._config(_CMD_SET_MODE, _REG_PP, self._cfgModePP)

    def _overVoltProt(self):
        for oi in range(8):
            if getBit(self._ovRT, oi) and not getBit(self._cfgModePP, oi):
                self._ovLock = setBit(self._ovLock, oi, True)
                if not getBit(self._outputs, oi) and not getBit(self._thsdLock, oi):
                    self._outputSet(oi, True)
                self._lockTs[oi] = time.ticks_ms()
            elif getBit(self._ovLock, oi):
                if time.ticks_diff(time.ticks_ms(), self._lockTs[oi]) > _PROT_OV_LOCK_MS:
                    if not getBit(self._thsdLock, oi):
                        self._outputSet(oi, getBit(self._outputsUser, oi))
                    self._ovLock = setBit(self._ovLock, oi, False)

    def _thermalProt(self):
        for oi in range(8):
            if getBit(self._thsdRT, oi):
                self._thsdLock = setBit(self._thsdLock, oi, True)
                if getBit(self._cfgModePP, oi):
                    self._modePPSet(oi, False)
                if getBit(self._outputs, oi):
                    self._outputSet(oi, False)
                self._lockTs[oi] = time.ticks_ms()
            elif getBit(self._thsdLock, oi):
                if time.ticks_diff(time.ticks_ms(), self._lockTs[oi]) > _PROT_THSD_LOCK_MS:
                    self._modePPSet(oi, getBit(self._cfgModePPUser, oi))
                    self._outputSet(oi, getBit(self._outputsUser, oi))
                    self._thsdLock = setBit(self._thsdLock, oi, False)

    def modeProtected(self, idx, pp, ol):
        self._cfgOlDet = setBit(self._cfgOlDet, idx, ol)
        if not self._config(_CMD_SET_OL_DET, _REG_OL_EN, self._cfgOlDet):
            return False
        self._cfgModePPUser = setBit(self._cfgModePPUser, idx, pp)
        if getBit(self._ovLock, idx) or getBit(self._thsdLock, idx):
            return False
        return self._modePPSet(idx, pp)

    def writeProtected(self, idx, val):
        self._outputsUser = setBit(self._outputsUser, idx, val)
        if getBit(self._ovLock, idx) or getBit(self._thsdLock, idx):
            return False
        return self._outputSet(idx, val)

    def join(self, idx, join):
        bitIdx = 2 if (idx <= 3) else 3
        self._cfgJoin = setBit(self._cfgJoin, bitIdx, join)
        if not self._config(_CMD_SET_CONFIG, _REG_WD_JN, self._cfgJoin):
            return False
        return True

    def updateOl(self):
        self._olRT, self._ol = self._readReg(_REG_OL)
        self._faultMemOl |= self._olRT

    def updateOv(self):
        self._ovRT, _ = self._readReg(_REG_OV)
        self._faultMemOv |= self._ovRT
        if self._ovProtEn:
            self._overVoltProt()

    def refreshOutputs(self):
        self._cmd(_CMD_SET_STATE, self._outputs)

    def updateThsd(self):
        self._thsdRT, self._thsd = self._readReg(_REG_THSD)
        self._faultMemThsd |= self._thsdRT
        self._thermalProt()
