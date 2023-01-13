# Iono RP D16 - MicroPython SDK

MicroPython library and examples for Iono RP D16.

For details on how to set up the MicroPython environment, refer to the [Raspberry Pi Pico Python SDK documentation](https://datasheets.raspberrypi.org/pico/raspberry-pi-pico-python-sdk.pdf).

## Quick start

Follow these steps to run the MicroPython example using the Thonny IDE from your host computer connected to Iono RP D16 via USB.

- Download and install [Thonny](https://thonny.org/)
- Download the content of this repository to your computer
- Open Thonny and from the Files view (menu *View* > *Files*) navigate to the downloaded folder
- Click on the bottom-right corner of the Thonny window to select "MicroPython (Raspberry Pi Pico)" as interpreter, if not available select "Configure interpreter..." and then select it from the window that will open
- Unplug Iono RP D16 from any power source (main power supply and USB cable)
- Connect the USB cable to Iono RP D16 while holding the BOOTSEL button, then release the BOOTSEL button
- Click on the Stop sign button in the top bar of Thonny
- A pop-up will ask you to install MicroPython, go ahead and proceed with the installation
- In the Files view you will now see a "Raspberry Pi Pico" section showing the files uploaded to Iono RP D16
- From the Files view right-click on the "lib" folder, select "Upload to /" and wait for the upload to finish
- Double-click on the "example.py" file to open it in the main editor
- Press on the "Play" (&#9658;) button in the top bar of Thonny to run the example on your Iono RP D16

![iono-rp-d16-thonny](https://user-images.githubusercontent.com/6586434/212291237-a13b62cd-4f60-40a7-a36d-49861c4b102c.png)

## Module `iono_d16` documentation

The `iono_d16` module provides the `Iono` object

### `Iono` methods

#### `Iono.init()`
Call this function before using any other functionality of the library. It initializes the used pins and peripherals.
#### Returns
`True` upon success.

<br/>

#### `Iono.ready()`
Useful for synchronization between the two cores.
#### Returns
whether or not the `Iono.init()` method has been executed.

<br/>

#### `Iono.process()`
Call this function periodically, with a maximum interval of 20ms. It performs the reading of the input/output peripherals' state, moreover it checks for fault conditions, enables safety routines and updates the outputs' watchdog. It is recommended to reserve one core of the RP2040 for calling this function, while performing your custom logic on the other core.

<br/>

#### `Iono.d_pins()`
Returns a list containing the `Iono.D1` ... `Iono.D16` pin objects (see below)

<br/>

### DT<n> Pins

The `Iono` object has the `DT1` ... `DT4` attributes corresponding to the 4 TTL-level I/O lines. They are instances of the [`Pin`](https://docs.micropython.org/en/latest/library/machine.Pin.html) class.

#### `Iono.DT<n>.init(mode)`
Initializes the pin as input or output. To be called before any other operation on the same pin.
##### Parameters
**`mode`**:
- `Iono.PIN_MODE_IN`: use pin as input
- `Iono.PIN_MODE_OUT`: use pin as output

<br/>

All other methods are those of the [`Pin`](https://docs.micropython.org/en/latest/library/machine.Pin.html) class.

<br/>

### D<n> Pins

The `D1` ... `D16` attributes represent the high voltage inputs and outputs.

#### `Iono.D<n>.init(mode, wb_ol=False)`
Initializes the pin as input or output. To be called before any other operation on the same pin.
##### Parameters
**`mode`**:
- `Iono.PIN_MODE_IN`: use pin as input
- `Iono.PIN_MODE_OUT_HS`: use pin as high-side output
- `Iono.PIN_MODE_OUT_PP`: use pin as push-pull output

**`wb_ol`**: enable (`True`) or disable (`False`) wire-break (for inputs) or open-load (for high-side outputs) detection
#### Returns
`True` upon success.

<br/>

#### `Iono.D<n>.joinPair(join=True)`
Joins this high-side output to its pair neighbour, to be used as a single output. Outputs can be joined in specific pairs: `D1`-`D2`, `D3`-`D4`, ..., `D15`-`D16`.
When a pair is joined, the other pair of the same group of four is also joined, e.g. joining `D3`-`D4` results in `D1`-`D2` being joined too if used as outputs.
Therefore, joining a pair requires the pins of the other pair of the same group of four to be initialized as `PIN_MODE_OUT_HS` or `PIN_MODE_IN`. In the latter case the two pins can be used as independent inputs.
##### Parameters
**`join`**: `True` to join, `False` to un-join
#### Returns
`True` upon success.

<br/>

#### `Iono.D<n>.value([x])`
This method allows to set and get the value of the pin, depending on whether the argument `x` is supplied or not.

If the argument is omitted then this method gets the digital logic level of the pin, returning `0` or `1` corresponding to low and high voltage signals respectively. The returned value corresponds to the reading performed during the latest `Iono.process()` call.

If the argument is supplied then this method sets the digital logic level of the pin. The argument `x` can be anything that converts to a boolean. If it converts to `True`, the pin is set to state high, otherwise it is set to state low.    
When setting the value this method returns `True` upon success or `False` if an error occurred.

<br/>

#### `Iono.D<n>.__call__([x])`
`Iono.D<n>` objects are callable (e.g. `Iono.D1() or Iono.D3(1)`). The call method provides a shortcut to set and get the value of the pin. It is equivalent to `Iono.D<n>.value([x])`.

<br/>

#### `Iono.D<n>.on()`
Equivalent to `Iono.D<n>.value(1)`

<br/>

#### `Iono.D<n>.off()`
Equivalent to `Iono.D<n>.value(0)`

<br/>

#### `Iono.D<n>.pwm(freq, duty_u16)`
Sets a soft-PWM on a push-pull output.    
The maximum frequency is determined by the frequency of `iono_process()` calls.
##### Parameters
**`freq`**: frequency in Hz

**`duty_u16`**: duty cycle as a ratio `dutyU16 / 65535`
#### Returns
`True` upon success.

<br/>

#### `Iono.D<n>.wire_break()`
Returns the wire-break fault state of an input pin with wire-break detection enabled.    
The fault state is updated on each `Iono.process()` call and set to `1` when detected. It is cleared (set to `0`) only after calling this method.
#### Returns
`1` if wire-break detected, `0` if wire-break not detected.

<br/>

#### `Iono.D<n>.open_load()`
Returns the open-load fault state of an input pin with open-load detection enabled.    
The fault state is updated on each `Iono.process()` call and set to `1` when detected. It is cleared (set to `0`) only after calling this method.
#### Returns
`1` if open-load detected, `0` if open-load not detected.

<br/>

#### `Iono.D<n>.over_voltage()`
Returns the over-voltage fault state of a pin.    
The fault state is updated on each `Iono.process()` call and set to `1` when detected. It is cleared (set to `0`) only after calling this method.
#### Returns
`1` if over-voltage detected, `0` if over-voltage not detected.

<br/>

#### `Iono.D<n>.over_voltage_lock()`
Returns whether or not an output pin is temporarily locked due to an over-voltage condition.    
The output cannot be set when locked.    
The fault state is updated on each `Iono.process()` call and set to `1` when detected. It is cleared (set to `0`) only after calling this method.
#### Returns
`1` if locked, `0` if not locked.

<br/>

#### `Iono.D<n>.thermal_shutdown()`
Returns the thermal shutdown fault state of a pin.    
The fault state is updated on each `Iono.process()` call and set to `1` when detected. It is cleared (set to `0`) only after calling this method.
#### Returns
`1` if thermal shutdown active, `0` if thermal shutdown not active.

<br/>

#### `Iono.D<n>.thermal_shutdown_lock()`
Returns whether or not an output pin is temporarily locked due to a thermal shutdown condition.    
The output cannot be set when locked.    
The fault state is updated on each `Iono.process()` call and set to `1` when detected. It is cleared (set to `0`) only after calling this method.
#### Returns
`1` if locked, `0` if not locked.

<br/>

#### `Iono.D<n>.alarm_t1()`
Returns whether or not the temperature alarm 1 threshold has been exceeded on the input peripheral the pin belongs to.    
The fault state is updated on each `Iono.process()` call and set to `1` when detected. It is cleared (set to `0`) only after calling this method.
#### Returns
`1` if threshold exceeded, `0` if threshold not exceeded.

<br/>

#### `Iono.D<n>.alarm_t2()`
Returns whether or not the temperature alarm 2 threshold has been exceeded on the input peripheral the pin belongs to.    
The fault state is updated on each `Iono.process()` call and set to `1` when detected. It is cleared (set to `0`) only after calling this method.
#### Returns
`1` if threshold exceeded, `0` if threshold not exceeded.

<br/>

### LED

#### `Iono.LED.value([x])`
This method allows to set and get the state of the blue 'ON' LED, depending on whether the argument `x` is supplied or not.

If the argument is omitted then this method gets the LED's state, returning `True` or `False` corresponding to ON and OFF respectively.

If the argument is supplied then this method sets the LED's state. The argument `x` can be anything that converts to a boolean. If it converts to `True`, the LED is turned ON, otherwise it is turned OFF.

<br/>

#### `Iono.LED.__call__([x])`
`Iono.LED` is callable (e.g. `Iono.LED() or Iono.LED(True)`). The call method provides a shortcut to set and get the state of the LED. It is equivalent to `Iono.LED.value([x])`.

<br/>

#### `Iono.LED.on()`
Equivalent to `Iono.LED.value(True)`

<br/>

#### `Iono.LED.off()`
Equivalent to `Iono.D<n>.value(False)`

<br/>

### RS-485

The `Iono` object has the `RS485` attribute, which is a wrapper of the [UART](https://docs.micropython.org/en/latest/library/machine.UART.html) instance connected to Iono's RS-485 interface.

The available methods are those of the [UART class](https://docs.micropython.org/en/latest/library/machine.UART.html#methods), plus the `txen(enable)`: method which controls the TX-enable line. Call `RS485.txen(True)` before writing data and call `RS485.txen(False)` before incoming data is expected.

#### `Iono.RS485.txen(enable)`
Controls the TX-enable line of the RS-485 interface.    
Call `Iono.RS485.txen(True)` before writing data. Call `Iono.RS485.txen(False)` before incoming data is expected. Good practice is to call `Iono.RS485.txen(False)` as soon as data has been written and flushed to the UART.
##### Parameters
**`enable`**: `True` to enable the TX-enable line, `False` to disable it
