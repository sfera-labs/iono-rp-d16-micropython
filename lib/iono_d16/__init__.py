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

from micropython import const
from machine import Pin as MPin
from machine import UART
from iono_d16.io import *
from iono_d16.max14912 import *
from iono_d16.max22190 import *
from iono_d16.spi import *

__version__ = '1.0.0'

class _RS485:
    PIN_TX = const(16)
    PIN_RX = const(17)
    PIN_TXEN_N = const(14)

    def __init__(self):
        self._txen_n = MPin(PIN_TXEN_N, MPin.OUT)
        self.init()

    def init(self, baudrate=9600, bits=8, parity=None, stop=1, **kwargs):
        self._uart = UART(0, baudrate=baudrate, bits=bits, parity=parity,
                        stop=stop, tx=MPin(PIN_TX), rx=MPin(PIN_RX), **kwargs)

    def __getattr__(self, attr):
        return getattr(self._uart, attr)

    def txen(self, enable):
        self._txen_n(not enable)

class _LED:
    def __init__(self, ctrlD, ctrlClk1, ctrlClk2):
        self._set = True
        self._val = False
        self._ctrlD = ctrlD
        self._ctrlClk1 = ctrlClk1
        self._ctrlClk2 = ctrlClk2

    def _process(self):
        if self._val != self._set:
            with Spi.mutex:
                self._ctrlD(0 if self._set else 1)
                self._ctrlClk1(0)
                Spi.transaction(self._ctrlClk2, 0, 0, 0)
                self._ctrlClk1(1)
                self._ctrlD(1)
            self._val = self._set

    def __call__(self, on=None):
        self.value(on)

    def value(self, on=None):
        if on is None:
            return self._val
        self._set = on

    def on(self):
        self.value(True)

    def off(self):
        self.value(False)

class _Iono:
    PIN_DT1 = const(26)
    PIN_DT2 = const(27)
    PIN_DT3 = const(28)
    PIN_DT4 = const(29)

    PIN_I2C_SDA = const(0)
    PIN_I2C_SCL = const(1)

    PIN_CS_DOL = const(6)
    PIN_CS_DOH = const(5)
    PIN_CS_DIL = const(8)
    PIN_CS_DIH = const(7)

    PIN_MAX14912_WD_EN = const(18)

    PIN_MAX22190_LATCH = const(9)

    LINK_NONE = const(0)
    LINK_FOLLOW = const(1)
    LINK_INVERT = const(2)
    LINK_FLIP_H = const(3)
    LINK_FLIP_L = const(4)
    LINK_FLIP_T = const(5)

    PIN_MODE_IN = PinMode.IN
    PIN_MODE_OUT_HS = PinMode.OUT_HS
    PIN_MODE_OUT_PP = PinMode.OUT_PP
    PIN_MODE_OUT = PinMode.OUT

    def __init__(self):
        self._setupDone = False

    def init(self):
        if self._setupDone:
            return False

        self._maxInL = Max22190(PIN_CS_DIL)
        self._maxInH = Max22190(PIN_CS_DIH)
        self._maxOutL = Max14912(PIN_CS_DOL)
        self._maxOutH = Max14912(PIN_CS_DOH)

        MPin(PIN_MAX14912_WD_EN, MPin.OUT, None).value(1)

        self.RS485 = _RS485()
        self.RS485.txen(False)

        Spi.init()

        self.LED = _LED(self._maxOutL._pinCs,
                    self._maxInL._pinCs, self._maxInH._pinCs)

        self.D1 = MaxIO(self._maxInL, self._maxOutL, 1)
        self.D2 = MaxIO(self._maxInL, self._maxOutL, 2)
        self.D3 = MaxIO(self._maxInL, self._maxOutL, 3)
        self.D4 = MaxIO(self._maxInL, self._maxOutL, 4)
        self.D5 = MaxIO(self._maxInL, self._maxOutL, 5)
        self.D6 = MaxIO(self._maxInL, self._maxOutL, 6)
        self.D7 = MaxIO(self._maxInL, self._maxOutL, 7)
        self.D8 = MaxIO(self._maxInL, self._maxOutL, 8)
        self.D9 = MaxIO(self._maxInH, self._maxOutH, 9)
        self.D10 = MaxIO(self._maxInH, self._maxOutH, 10)
        self.D11 = MaxIO(self._maxInH, self._maxOutH, 11)
        self.D12 = MaxIO(self._maxInH, self._maxOutH, 12)
        self.D13 = MaxIO(self._maxInH, self._maxOutH, 13)
        self.D14 = MaxIO(self._maxInH, self._maxOutH, 14)
        self.D15 = MaxIO(self._maxInH, self._maxOutH, 15)
        self.D16 = MaxIO(self._maxInH, self._maxOutH, 16)

        self.DT1 = DTPin('DT1', PIN_DT1)
        self.DT2 = DTPin('DT2', PIN_DT2)
        self.DT3 = DTPin('DT3', PIN_DT3)
        self.DT4 = DTPin('DT4', PIN_DT4)

        ok = self._maxInL.init()
        ok = self._maxInH.init() and ok

        self._processStep = 0
        self._processTs = 0
        self._setupDone = True

        self.process()

        return ok

    def process(self):
        if not self._setupDone:
            return

        mis = [self._maxInL, self._maxInH]
        mos = [self._maxOutL, self._maxOutH]

        # WB is read always to update the inputs state
        for mi in mis:
            mi.updateWb()

        if time.ticks_diff(time.ticks_ms(), self._processTs) > 20:
            if self._processStep == 0:
                for mi in mis:
                    mi.updateFault1()
                for mi in mis:
                    mi.updateFault2()
            elif self._processStep == 1:
                for mo in mos:
                    mo.updateOl()
            elif self._processStep == 2:
                for mo in mos:
                    mo.updateOv()
            elif self._processStep == 3:
                for mo in mos:
                    mo.refreshOutputs()
            else:
                for mo in mos:
                    mo.updateThsd()
                _processStep = -1

            self._processStep += 1
            self._processTs = time.ticks_ms()

        for d in self.d_pins():
            d._processPwm()

        self.LED._process()

    def ready(self):
        return self._setupDone

    def d_pins(self):
        return MaxIO._list

Iono = _Iono()
