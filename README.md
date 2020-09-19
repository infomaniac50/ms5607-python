![Altimeter Module MS5607- Top View](ms5607-front.png) ![Altimeter Module MS5607- Top View](ms5607-back.png)

# ms5607
Python 3 library for MS5607-02BA03 pressure sensor for Raspberry Pi over i2c.

Based off of [Python 3 library for MS5803-14BA](https://github.com/NickCrews/ms5803py) and parts of [Python i2c interface for the MS5607 altimeter](https://github.com/rsolomon/py-MS5607). Some of the math is complicated when correcting raw readings to actual temperatures and pressures, that math can be verified from the [MS5607-02BA03 datasheet](http://www.te.com/commerce/DocumentDelivery/DDEController?Action=showdoc&DocId=Data+Sheet%7FMS5803-14BA%7FB3%7Fpdf%7FEnglish%7FENG_DS_MS5803-14BA_B3.pdf%7FCAT-BLPS0013).

Supports reading the pressure and temperature values from the sensor at any of the supported OverSampling Rates (OSR). A higher OSR leads to greater resolution/accuracy but requires a longer conversion time. The supported OSR rates are [256, 512, 1024, 2048, 4096], also available at `MS5607.OSRs`.
## Prerequisites

### Pipenv

Read [Pipenv: Python Dev Workflow for Humans](https://docs.pipenv.org/) and (Installing Pipenv](https://docs.pipenv.org/install/#installing-pipenv) for instructions on how to use and install Pipenv.

## Installation
Clone this repository and run
```
pipenv install
```

## Usage
The MS5607 and the RPi use the I2C protocol to communicate, so you need to have I2C set up on your pi, as explained in [this Adafruit tutorial](https://learn.adafruit.com/adafruits-raspberry-pi-lesson-4-gpio-setup/configuring-i2c). After that, the MS5607 needs to be hooked up to the Raspberry Pi as described in [this Adafruit tutorial](https://learn.sparkfun.com/tutorials/ms5803-14ba-pressure-sensor-hookup-guide).

After doing that, you must find the I2C address of your MS5607. To do this, run the following command both before and after plugging in the MS5607. Whatever address shows up is the one you want:
```
sudo i2cdetect -y 1
````
It should be either `0X76` or `0x77`, as described in the [MS5607-02BA03 datasheet](https://www.parallax.com/sites/default/files/downloads/29124-MS5607-02BA03-Datasheet.pdf), depending on if the CSB (Chip Select) pin on the MS5607 is high or low. On the [Altimeter Module MS5607](https://www.parallax.com/product/29124) the I2C address is `0x76`, so I have that set as the default if you don't specify an address when initializing the sensor.

See `python3 example.py` for an example of usage:
```
import ms5607
import time

s = ms5607.MS5607()
while True:
    # Do the batteries-included version, optionally specifying an OSR.
    press, temp = s.read(pressure_osr=512)
    print("quick'n'easy pressure={} mBar, temperature={} C".format(press, temp))

    # Use the raw reads for more control, e.g. you need a faster sample
    # rate for pressure than for temperature. Use a high OverSampling Rate (osr)
    # value for a slow but accurate temperature read, and a low osr value
    # for quick and inaccurate pressure readings.
    raw_temperature = s.read_raw_temperature(osr=4096)
    for i in range(5):
        raw_pressure = s.read_raw_pressure(osr=256)
        press, temp = s.convert_raw_readings(raw_pressure, raw_temperature)
        print("advanced pressure={} mBar, temperature={} C".format(press, temp))
    time.sleep(1)
```
results in:
```
quick'n'easy pressure=990.02 mBar, temperature=27.61 C
advanced pressure=990.19 mBar, temperature=27.61 C
advanced pressure=990.42 mBar, temperature=27.61 C
advanced pressure=989.97 mBar, temperature=27.61 C
advanced pressure=990.19 mBar, temperature=27.61 C
advanced pressure=989.97 mBar, temperature=27.61 C
quick'n'easy pressure=990.1 mBar, temperature=27.62 C
advanced pressure=990.21 mBar, temperature=27.62 C
advanced pressure=990.21 mBar, temperature=27.62 C
advanced pressure=990.44 mBar, temperature=27.62 C
advanced pressure=990.21 mBar, temperature=27.62 C
advanced pressure=990.21 mBar, temperature=27.62 C
...
```
