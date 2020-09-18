import ms5607
import time

s = ms5607.MS5607()

while True:
    # Do the batteries-included version, optionally specifying an OSR.
    press, temp = s.read(pressure_osr=512)
    print("quick'n'easy pressure={} mBar, temperature={} C".format(press, temp))

    altitude = s.read_altitude()
    print("quick'n'easy altitude={} meters".format(altitude))

    # You can get the altimeter setting from the METAR data provided by your local airport.
    # At least for the United States, https://www.aviationweather.gov/ can provide this data.
    # Go to https://www.aviationweather.gov/taf/data and enter the ICAO airport code, select Decoded format,
    # and check "Include METAR".
    #
    # You want the number that has the sea level pressure from the altimeter setting.
    # [Sea level pressure: 1023.4 mb]
    #
    # The full output will look something like this.
    # Data at: 2257 UTC 18 Sep 2020
    #
    # METAR for:	KMCI (Kansas City Intl, MO, US)
    # Text:	KMCI 182253Z 08007KT 10SM CLR 21/11 A3023 RMK AO2 SLP234 T02110111
    # Temperature:	21.1°C ( 70°F)
    # Dewpoint:	11.1°C ( 52°F) [RH = 53%]
    # Pressure (altimeter):	30.23 inches Hg (1023.8 mb) [Sea level pressure: 1023.4 mb]
    # Winds:	from the E (80 degrees) at 8 MPH (7 knots; 3.6 m/s)
    # Visibility:	10 or more sm (16+ km)
    # Ceiling:	at least 12,000 feet AGL
    # Clouds:	sky clear below 12,000 feet AGL
    #
    # TAF for:	KMCI (Kansas City Intl, MO, US) issued at 1728 UTC 18 Sep 2020
    # Text:	KMCI 181728Z 1818/1918 08006KT P6SM FEW250
    # Forecast period:	1800 UTC 18 September 2020 to 1400 UTC 19 September 2020
    # Forecast type:	FROM: standard forecast or significant change
    # Winds:	from the E (80 degrees) at 7 MPH (6 knots; 3.1 m/s)
    # Visibility:	6 or more sm (10+ km)
    # Ceiling:	at least 12,000 feet AGL
    # Clouds:	few clouds at 25000 feet AGL
    # Text:	FM191400 14010KT P6SM SCT250
    # Forecast period:	1400 to 1800 UTC 19 September 2020
    # Forecast type:	FROM: standard forecast or significant change
    # Winds:	from the SE (140 degrees) at 12 MPH (10 knots; 5.1 m/s)
    # Visibility:	6 or more sm (10+ km)
    # Ceiling:	at least 12,000 feet AGL
    # Clouds:	scattered clouds at 25000 feet AGL

    # On September 18th 2020 at 22:57 UTC the sea level pressure at Kansas City International was 1023.4 millibars.
    altitude = s.read_altitude(sea_level_pressure=1023.4)
    print("advanced altitude={} meters".format(altitude))

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
