# Iono RP D16 - MicroPython SDK

MicroPython library and examples for Iono RP D16.

For details on how to set up the MicroPython environment, refer to the [Raspberry Pi Pico Python SDK documentation](https://datasheets.raspberrypi.org/pico/raspberry-pi-pico-python-sdk.pdf).

## Quick start

Follow these steps to run the MicroPython examples using the Thonny IDE from your host computer connected to Iono RP via USB.

- Download and install [Thonny](https://thonny.org/)
- Download the content of this repository to your computer
- Open Thonny and from the Files view (menu *View* > *Files*) navigate to the downloaded "micropython" folder
- Click on the bottom-right corner of the Thonny window to select "MicroPython (Raspberry Pi Pico)" as interpreter
- Unplug Iono RP from any power source (main power supply and USB cable)
- Connect the USB cable to Iono RP while holding the BOOTSEL button, then release the BOOTSEL button
- Click on the Stop sign button in the top bar of Thonny
- A pop-up will ask you to install MicroPython, go ahead and proceed with the installation
- In the Files view you will now see a "Raspberry Pi Pico" section showing the files uploaded to Iono RP
- From the Files view right-click on the "lib" folder, select "Upload to /" and wait for the upload to finish
- Double-click on one of the example files to open it in the main editor
- Press on the "Play" (&#9658;) button in the top bar of Thonny to run the example on your Iono RP
