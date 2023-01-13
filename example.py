'''
Iono RP D16 library usage example

    Copyright (C) 2022-2023 Sfera Labs S.r.l. - All rights reserved.

    For information, see:
    http://www.sferalabs.cc/

This code is free software; you can redistribute it and/or
modify it under the terms of the GNU Lesser General Public
License as published by the Free Software Foundation; either
version 2.1 of the License, or (at your option) any later version.
See file LICENSE.txt for further informations on licensing terms.
'''

from iono_d16 import Iono
import time
import _thread

# task for the second core of the RP2040
def core1_task():
    if not Iono.init():
        print("Init error")

    while True:
        Iono.process()
        time.sleep_ms(1)

_thread.start_new_thread(core1_task, ())

# Make sure Iono.init() is complete
while not Iono.ready():
    time.sleep_ms(100)

print("Ready!")

# Setup D1 as push-pull output
if not Iono.D1.init(mode=Iono.PIN_MODE_OUT_PP):
    print("D1 setup error")

# Setup D2 as high-side output with open-load detection enabled
if not Iono.D2.init(mode=Iono.PIN_MODE_OUT_HS, wb_ol=True):
    print("D2 setup error")

# Setup D3 as input with wire-break detection enabled
if not Iono.D3.init(mode=Iono.PIN_MODE_IN, wb_ol=True):
    print("D3 setup error")

# Setup D5 as high-side output
if not Iono.D5.init(mode=Iono.PIN_MODE_OUT_HS):
    print("D5 setup error")

# Setup D6 as high-side output
if not Iono.D6.init(mode=Iono.PIN_MODE_OUT_HS):
    print("D6 setup error")

# Setup D7 as input (required for joining D5-D6 below)
if not Iono.D7.init(mode=Iono.PIN_MODE_IN):
    print("D7 setup error")

# Setup D8 as input (required for joining D5-D6 below)
if not Iono.D8.init(mode=Iono.PIN_MODE_IN):
    print("D8 setup error")

# Join D5 and D6 to be used as single output
if not Iono.D5.joinPair():
    print("D5/D6 join error")

# Setup DT1 as output
Iono.DT1.init(mode=Iono.PIN_MODE_OUT)

# Setup DT2 as input
Iono.DT2.init(mode=Iono.PIN_MODE_IN)

# Setup D4 as push-pull output
# with 1Hz frequency, 50% duty-cycle PWM
if not Iono.D4.init(mode=Iono.PIN_MODE_OUT_PP):
    print("D4 setup error")

if not Iono.D4.pwm(freq=1, duty_u16=(65535 // 2)):
    print("D4 PWM setup error")

print("I/O setup done.")

# Init RS-485 interface
Iono.RS485.init(9600, bits=8, parity=None, stop=1, timeout=0, timeout_char=50)
Iono.RS485.txen(False)

flip = True

while True:
    time.sleep_ms(500)

    flip = not flip

    print("------------ {}".format(flip))

    Iono.LED(flip)

    if not Iono.D1(1 if flip else 0):
        print("D1 write error")

    # Setting D5 will drive D6 too
    if not Iono.D5.value(1 if flip else 0):
        print("D5-D6 write error")

    if flip:
        Iono.DT1.on()
    else:
        Iono.DT1.off()

    time.sleep_ms(10)

    for pin in Iono.d_pins():
        print(
            "{} = {}\tWB = {}\tOL = {}\tOV = {}\tOVL = {}\tTS = {}\tTSL = {}\tAT1 = {}\tAT2 = {}".format(
                    pin.name(),
                    pin.value(),
                    pin.wire_break(),
                    pin.open_load(),
                    pin.over_voltage(),
                    pin.over_voltage_lock(),
                    pin.thermal_shutdown(),
                    pin.thermal_shutdown_lock(),
                    pin.alarm_t1(),
                    pin.alarm_t2()
                )
            )

    print("DT1 =", Iono.DT1())
    print("DT2 =", Iono.DT2.value())

    # Check RS-485 for incoming data
    line = Iono.RS485.readline()
    if line:
        # If available, echo it back
        # driving the TX-enble line
        Iono.RS485.txen(True)
        Iono.RS485.write("Echo: ")
        Iono.RS485.write(line)
        Iono.RS485.txen(False)
