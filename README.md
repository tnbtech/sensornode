# SensorNode
***Easily add common sensors to Home Assistant home automation systems.***

This code is intended to be used with the SensorNode PC board, which is part of a DIY Kit launched as a [Kickstarter project in Summer 2025](https://www.kickstarter.com/projects/tomberarducci/sensornode-a-diy-sensor-platform-for-home-assistant). 

If you want to buy your own SensorNode you can buy it [here](https://www.tindie.com/products/tnbtechnologiesllc/sensornode-for-home-assistant/?pt=ac_prod_search).

You can access all the SensorNode documentation [here](https://www.tnbtechnologies.com/sensornode/ksbacker2025).

However, you don't need to use the SensorNode board if you don't want to. The code will run on a Raspberry Pi Pico microcontroller without the PC board, albeit with limitations without the PC board circuitry. 

The code is intended to run using CircuitPython. The exact version of CircuitPython (and related libraries) tested with this code is included in this repo. To avoid issues, **please use this version**. The intended target processor is the **Pico 1W**. Pico 2W may work, but it may require upgrades to the version of CircuitPython and libraries. 

# Quick Start

 1. Download a copy of this repo to your computer.
 2. Attach a compatible USB cable to your Pico, and plug it into your computer. If the Pico is new/unprogrammed, it should appear on your computer as a disk drive labeled "RPI-RP2".
 3. Open the folder labeled "circuitpython" in the repo, and drag (or copy/paste) the "uf2" file to your Pico. After the copy completes, the "RPI-RP2" drive should disappear and a new drive called "CIRCUITPY" should appear.
 4. Open the CIRCUITPY drive on your computer, and **DELETE all the files there.** 
 5. Open the folder labeled "code" in the repo, and copy all the files there to the ***root directory*** of your Pico.
 6. Drag (or copy/paste) the ***entire folder*** labeled "lib" to your Pico.
 7. Eject the Pico from your computer. It is now ready to be used as a SensorNode.

## References
If you want to know more about SensorNode, you can check out the Kickstarter project archive [here](https://www.kickstarter.com/projects/tomberarducci/sensornode-a-diy-sensor-platform-for-home-assistant).
If you want to read even more about SensorNode, you can find more info on the TNB Technologies website SensorNode section [here](https://www.tnbtechnologies.com/sensornode).
If you have questions/comments, you can email me at tom@tnbtechnologies.com
Good luck, and thanks for your interest in SensorNode!

Tom Berarducci
