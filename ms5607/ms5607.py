import smbus
import time

STANDARD_PRESSURE = 1013.25

def convert_altitude(local_pressure, sea_level_pressure=STANDARD_PRESSURE):
    """
    So how does pressure vary with altitude? Or, more usefully, if you know the local air pressure,
    how do you compute your altitude from that? The following formula yields altitude in terms of pressure for the
    troposphere (i.e. from below sea level to 11 km):

                          ┌             0.190264 ┐
   Altitude = 44330.76923 │ 1 - (P / P0)         │
                          └                      ┘
    where Altitude is in meters. P is the local air pressure, and P0 is the pressure at sea level,
    both expressed in the same units, whether millibars, Pascals, or inches of mercury.
    When P0 is set equal to the standard sea level pressure of 1013.25 mb, the altitude yielded by the formula
    is called the "pressure altitude." The actual altitude may be computed by substituting the local air pressure,
    corrected to sea level, for P0.
    """
    return 44330.76923 * (1 - (local_pressure / sea_level_pressure) ** 0.190264)


class MS5607(object):
    """
    MS5607-02BA03 temperature and pressure sensor for Raspberry Pi over i2c.

    This will work for the TE Connectivity MS5607-02BA03 sensor, whose
    datasheet can be found at https://www.te.com/commerce/DocumentDelivery/DDEController?Action=showdoc&DocId=Data+Sheet%7FMS5607-02BA03%7FB2%7Fpdf%7FEnglish%7FENG_DS_MS5607-02BA03_B2.pdf%7FCAT-BLPS0035
    or https://www.parallax.com/sites/default/files/downloads/29124-MS5607-02BA03-Datasheet.pdf.
    This will also work for the Parallax Altimeter Module MS5607 (https://www.parallax.com/product/29124).

    This class allows you to read both the pressure and temperature
    in one simple read() request, or you can use read_raw_pressure(),
    read_raw_temperature(), and convert_raw_readings() functions individually,
    if you need finer-grained control.

    You can read the temp and pressure at different OverSampling Rates (OSR).
    A higher OSR leads to greater resolution/accuracy but requires a longer
    conversion time. The available OSR rates are available in MS5607.OSRs.
    More info on OSR at https://www.cypress.com/file/236481/download.
    """

    # The address of the i2c or SPI device is either 0x76 or 0x77,
    # depending on if the CSB (chip select) pin is pulled high or low.
    # On the SparkFun breakout board it is pulled high, therefore we
    # use this as the default.
    DEFAULT_SENSOR_ADDR = 0x76

    # Command to reset the MS5607, should be sent at startup.
    _CMD_RESET = 0x1E

    # At the factory the sensor is calibrated, with 6 calibration
    # constants written to the sensor's ROM. We read these at device
    # initialization and use them to correct the raw temperature
    # and pressure readings from the sensor.
    # Read pressure sensitivity.
    _CMD_READ_C1 = 0xA2
    # Read pressure offset.
    _CMD_READ_C2 = 0xA4
    # Read temperature coefficient of pressure sensitivity.
    _CMD_READ_C3 = 0xA6
    # Read temperature coefficient of pressure offset.
    _CMD_READ_C4 = 0xA8
    # Read reference temperature.
    _CMD_READ_C5 = 0xAA
    # Read temperature coefficient of the temperature.
    _CMD_READ_C6 = 0xAC

    # Commands to start ADC conversion at different OSR values.
    _CMD_SELECT_PRESSURE_OSR256 = 0x40
    _CMD_SELECT_PRESSURE_OSR512 = 0x42
    _CMD_SELECT_PRESSURE_OSR1024 = 0x44
    _CMD_SELECT_PRESSURE_OSR2048 = 0x46
    _CMD_SELECT_PRESSURE_OSR4096 = 0x48

    # Commands to start ADC conversion at different OSR values.
    _CMD_SELECT_TEMPERATURE_OSR256 = 0x50
    _CMD_SELECT_TEMPERATURE_OSR512 = 0x52
    _CMD_SELECT_TEMPERATURE_OSR1024 = 0x54
    _CMD_SELECT_TEMPERATURE_OSR2048 = 0x56
    _CMD_SELECT_TEMPERATURE_OSR4096 = 0x58

    # After starting a conversion with one of the SELECT commands above and
    # waiting for the conversion to finish, read the value from the ADC.
    _CMD_READ_ADC = 0x00

    # Map from different OSR values to commands.
    _SELECT_PRESSURE_COMMANDS = {
        256: _CMD_SELECT_PRESSURE_OSR256,
        512: _CMD_SELECT_PRESSURE_OSR512,
        1024: _CMD_SELECT_PRESSURE_OSR1024,
        2048: _CMD_SELECT_PRESSURE_OSR2048,
        4096: _CMD_SELECT_PRESSURE_OSR4096,
    }
    _SELECT_TEMPERATURE_COMMANDS = {
        256: _CMD_SELECT_TEMPERATURE_OSR256,
        512: _CMD_SELECT_TEMPERATURE_OSR512,
        1024: _CMD_SELECT_TEMPERATURE_OSR1024,
        2048: _CMD_SELECT_TEMPERATURE_OSR2048,
        4096: _CMD_SELECT_TEMPERATURE_OSR4096,
    }

    # According to the ADC table in the PERFORMANCE SPECIFICATIONS section of
    # the datasheet, the following are the number of seconds we need to
    # wait between making a read request and actually reading a value, for a
    # given OSR value. If we don't wait long enough, the ADC will return 0!
    CONVERSION_TIMES = {
        256: 0.60 / 1000,
        512: 1.17 / 1000,
        1024: 2.28 / 1000,
        2048: 4.54 / 1000,
        4096: 9.04 / 1000,
    }

    # Utility for users of this class.
    OSRs = [256, 512, 1024, 2048, 4096]

    def __init__(self, bus=1, address=None):
        """Create and reset a sensor instance, then read calibration coefficients.

        Keyword arguments:
        bus -- i2c bus. Default is 1.
        address -- i2c address of the sensor. Default is 0x76.
        """
        self.bus = smbus.SMBus(bus)
        if address is None:
            address = MS5607.DEFAULT_SENSOR_ADDR
        self.address = address
        self._write(MS5607._CMD_RESET)
        # We seem to need to give the sensor a chance to reset or reading
        # the coefficients fails. 2ms seems to be the threshold for me, so
        # use 5ms to be safe.
        time.sleep(.005)
        self._coeffs = self._read_calibration_coeffs()

    def read(self, pressure_osr=4096, temperature_osr=4096):
        """Return current (pressure, temperature) in millibars and Celsius.

        Keyword arguments:
        pressure_osr -- passed onwards to read_raw_pressure(osr=pressure_osr).
                        Default is 4096.
        temperature_osr -- passed onwards to read_raw_temperature(osr=temperature_osr)
                           Default is 4096.
        """
        raw_pressure = self.read_raw_pressure(osr=pressure_osr)
        raw_temperature = self.read_raw_temperature(osr=temperature_osr)

        return self.convert_raw_readings(raw_pressure, raw_temperature)

    def read_altitude(self, sea_level_pressure=STANDARD_PRESSURE, samples=48, pressure_osr=4096, temperature_osr=4096):
        accum = 0
        for n in range(0, samples):
            time.sleep(0.001)

            press, temp = self.read(pressure_osr, temperature_osr)
            accum += press

        avg = accum / samples
        return convert_altitude(avg, sea_level_pressure)

    def read_raw_pressure(self, osr=4096):
        """Return the raw pressure value from the sensor.

        The raw reading should be converted with convert_raw_readings().

        Keyword arguments:
        osr -- OverSampling Rate. Default is 4096, the most accurate but slowest.
        """
        self._write(MS5607._SELECT_PRESSURE_COMMANDS[osr])
        time.sleep(MS5607.CONVERSION_TIMES[osr])
        return self._read(MS5607._CMD_READ_ADC, 3)

    def read_raw_temperature(self, osr=256):
        """Return the raw temperature value from the sensor.

        The raw reading should be converted with convert_raw_readings().

        Keyword arguments:
        osr -- OverSampling Rate. Default is 4096, the most accurate but slowest.
        """
        self._write(MS5607._SELECT_TEMPERATURE_COMMANDS[osr])
        time.sleep(MS5607.CONVERSION_TIMES[osr])
        return self._read(MS5607._CMD_READ_ADC, 3)

    def convert_raw_readings(self, raw_pressure, raw_temperature):
        """Convert raw pressure and temperature values to millibars and Celsius.

        Uses the factory-calibrated coefficients retrieved from sensor ROM to
        perform the 2nd order temperature correction described in figure 16
        of the datasheet.
        """

        # It actually is important to use integer division here, or the conversion
        # does not follow the example values in figure 2 of the datasheet.
        C1, C2, C3, C4, C5, C6 = self._coeffs

        # Difference between raw temp and reference temp.
        # dT = D2 - TREF = D2 - C5 * 2^8
        dT = raw_temperature - C5 * 2 ** 8

        # Actual temperature (-40...85C with units of 0.01C).
        # TEMP = 20°C + dT * TEMPSENS = 2000 + dT * C6 / 2^23
        TEMP = 2000 + dT * C6 // 2 ** 23

        # Pressure offset at actual temperature.
        # OFF = OFF_T1 + TCO * dT = C2 * 2^17 + (C4 * dT) / 2^6
        OFF = C2 * 2 ** 17 + (C4 * dT) // 2 ** 6

        # Pressure sensitivity at actual temperature.
        # SENS = SENS_T1 + TCS * dT = C1 * 2^16 + (C3 * dT) / 2^7
        SENS = C1 * 2 ** 16 + (C3 * dT) // 2 ** 7

        # Do second order temperature correction of TEMP, OFF, and SENS.
        if TEMP < 2000:
            # Low temperature
            # TEMP is colder than 20°C

            # T2 = dT^2 / 2^31
            T2 = dT ** 2 // 2 ** 31

            # OFF2 = 61 * (TEMP – 2000)^2 / 2^4
            OFF2 = 61 * (TEMP - 2000) ** 2 // 2 ** 4

            # SENS2 = 2 * (TEMP – 2000)^2
            SENS2 = 2 * (TEMP - 2000) ** 2

            if TEMP < -1500:
                # Very low temperature
                # TEMP is colder than -15°C

                # OFF2 = OFF2 + 15 * (TEMP + 1500)^2
                OFF2 = OFF2 + 15 * (TEMP + 1500) ** 2

                # SENS2 = SENS2 + 8 * (TEMP + 1500)^2
                SENS2 = SENS2 + 8 * (TEMP + 1500) ** 2
        else:
            # High temperature
            T2 = 0
            OFF2 = 0
            SENS2 = 0

        TEMP = TEMP - T2
        OFF = OFF - OFF2
        SENS = SENS - SENS2

        # PMIN = 10mbar
        # PMAX = 1200mbar
        # TMIN = -40°C
        # TMAX = 85°C
        # TREF = 20°C

        # Temperature compensated pressure (10...1200mbar with 0.01mbar resolution)
        # P = D1 * SENS - OFF = (D1 * SENS / 2^21 - OFF) / 2^15
        PRESS = (raw_pressure * SENS // 2 ** 21 - OFF) // 2 ** 15

        # Convert to floating point mbar and degrees celsius.
        pressure = PRESS / 100.0
        temp = TEMP / 100.0

        return pressure, temp

    def _write(self, cmd):
        self.bus.write_byte(self.address, cmd)

    def _read(self, cmd, size):
        """
        Read a |size| byte integer from the sensor after making request |cmd|.

        Individual bytes are returned over i2c most-significant-first,
        so bit shift them into one int.
        """
        bytes = self.bus.read_i2c_block_data(self.address, cmd, size)
        result = 0
        for i, byte in enumerate(bytes):
            shift = ((size - i) - 1) * 8
            result |= byte << shift

        return result

    def _read_calibration_coeffs(self):
        C1 = self._read(MS5607._CMD_READ_C1, 2)
        C2 = self._read(MS5607._CMD_READ_C2, 2)
        C3 = self._read(MS5607._CMD_READ_C3, 2)
        C4 = self._read(MS5607._CMD_READ_C4, 2)
        C5 = self._read(MS5607._CMD_READ_C5, 2)
        C6 = self._read(MS5607._CMD_READ_C6, 2)
        return C1, C2, C3, C4, C5, C6
