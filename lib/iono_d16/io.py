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
import time
from iono_d16.utils import *

class PinMode:
    IN = const(1)
    OUT_HS = const(2)
    OUT_PP = const(3)
    OUT = const(4)

class DTPin(MPin):
    def __init__(self, name, pin):
        super().__init__(pin, None, None)
        self._name = name

    def name(self):
        return self._name

    def init(self, mode):
        if mode == PinMode.IN:
            mode = MPin.IN
        elif mode == PinMode.OUT:
            mode = MPin.OUT
        else:
            raise ValueError()
        super().init(mode)

class MaxIO:
    _list = []

    def _joinable(num):
        idx = num - 1
        base4 = (idx // 4) * 4
        mod4 = idx % 4
        if mod4 <= 1:
            idxHs1 = base4
            idxHs2 = base4 + 1
            idxHsOrIn1 = base4 + 2
            idxHsOrIn2 = base4 + 3
        else:
            idxHsOrIn1 = base4
            idxHsOrIn2 = base4 + 1
            idxHs1 = base4 + 2
            idxHs2 = base4 + 3
        if MaxIO._list[idxHs1]._mode != PinMode.OUT_HS:
            DEBUG(f"outs join {num} err 1")
            return False
        if MaxIO._list[idxHs2]._mode != PinMode.OUT_HS:
            DEBUG(f"outs join {num} err 2")
            return False
        if MaxIO._list[idxHsOrIn1]._mode != PinMode.OUT_HS and \
                MaxIO._list[idxHsOrIn1]._mode != PinMode.IN:
            DEBUG(f"outs join {num} err 3")
            return False
        if MaxIO._list[idxHsOrIn2]._mode != PinMode.OUT_HS and \
                MaxIO._list[idxHsOrIn2]._mode != PinMode.IN:
            DEBUG(f"outs join {num} err 4")
            return False
        return True

    def __init__(self, maxIn, maxOut, num):
        self._maxIn = maxIn
        self._maxOut = maxOut
        self._num = num
        self._inIdx = (16 - num) % 8
        self._outIdx = (num - 1) % 8
        self._name = 'D' + str(num)
        self._mode = None
        self._pwmPeriodUs = 0
        MaxIO._list.append(self)

    def _processPwm(self):
        if self._pwmPeriodUs > 0:
            dts = time.ticks_diff(time.ticks_us(), self._pwmStartTs)
            if dts > self._pwmPeriodUs:
                self.on()
                self._pwmStartTs = time.ticks_us()
                self._pwmOn = True
            elif self._pwmOn and dts > self._pwmDutyUs:
                self.off()
                self._pwmOn = False

    def __call__(self, on=None):
        return self.value(on)

    def name(self):
        return self._name

    def init(self, mode, wb_ol=False):
        ok = False
        if mode == PinMode.IN:
            if not self._maxOut.modeProtected(self._outIdx, False, False):
                return False
            if not self._maxOut.writeProtected(self._outIdx, 0):
                return False
            ok = self._maxIn.mode(self._inIdx, wb_ol)
        elif mode == PinMode.OUT_HS or mode == PinMode.OUT_PP:
            if mode ==PinMode.OUT_PP and wb_ol:
                # Open-load detection works in high-side mode only
                return False
            if not self._maxIn.mode(self._inIdx, False):
                return False
            self._maxOut._ovProtEn = True
            ok = self._maxOut.modeProtected(
                                self._outIdx, mode == PinMode.OUT_PP, wb_ol)
        if ok:
            self._mode = mode
        return ok

    def joinPair(self, join=True):
        if join and not MaxIO._joinable(self._num):
            return False
        return self._maxOut.join(self._outIdx, join)

    def pwm(self, freq, duty_u16):
        if self._mode != PinMode.OUT_PP:
            return False
        self._pwmPeriodUs = 0
        if duty_u16 == 0:
            self._maxOut.writeProtected(self._outIdx, 0)
            return True
        self._pwmDutyUs = (1000000 // freq) * duty_u16 // 65535
        self._maxOut.writeProtected(self._outIdx, 1)
        self._pwmStartTs = time.ticks_us()
        self._pwmOn = True
        self._pwmPeriodUs = 1000000 // freq
        return True

    def _read(self):
        return (self._maxIn._inputs >> self._inIdx) & 1

    def _write(self, val):
        if self._mode != PinMode.OUT_HS and self._mode != PinMode.OUT_PP:
            return False
        return self._maxOut.writeProtected(self._outIdx, val)

    def value(self, on=None):
        if on is None:
            return self._read()
        return self._write(on)

    def on(self):
        return self.value(True)

    def off(self):
        return self.value(False)

    def wire_break(self):
        ret = getBit(self._maxIn._faultMemWb, self._inIdx)
        self._maxIn._faultMemWb = \
                setBit(self._maxIn._faultMemWb, self._inIdx, False)
        return ret

    def open_load(self):
        ret = getBit(self._maxOut._faultMemOl, self._outIdx)
        self._maxOut._faultMemOl = \
                setBit(self._maxOut._faultMemOl, self._outIdx, False)
        return ret

    def over_voltage(self):
        ret = getBit(self._maxOut._faultMemOv, self._outIdx)
        self._maxOut._faultMemOv = \
                setBit(self._maxOut._faultMemOv, self._outIdx, False)
        return ret

    def over_voltage_lock(self):
        return getBit(self._maxOut._ovLock, self._outIdx)

    def thermal_shutdown(self):
        if getBit(self._maxOut._faultMemThsd, self._outIdx) or \
                getBit(self._maxIn._faultMemOtshdn, self._inIdx):
            ret = 1
        else:
            ret = 0
        self._maxOut._faultMemThsd = \
                setBit(self._maxOut._faultMemThsd, self._outIdx, False)
        self._maxIn._faultMemOtshdn = \
                setBit(self._maxIn._faultMemOtshdn, self._inIdx, False)
        return ret

    def thermal_shutdown_lock(self):
        return getBit(self._maxOut._thsdLock, self._outIdx)

    def alarm_t1(self):
        ret = getBit(self._maxIn._faultMemAlrmT1, self._inIdx)
        self._maxIn._faultMemAlrmT1 = \
                setBit(self._maxIn._faultMemAlrmT1, self._inIdx, False)
        return ret

    def alarm_t2(self):
        ret = getBit(self._maxIn._faultMemAlrmT2, self._inIdx)
        self._maxIn._faultMemAlrmT2 = \
                setBit(self._maxIn._faultMemAlrmT2, self._inIdx, False)
        return ret

    def clear_outputs_faults(self):
        self._maxOut._clearFaults = True
