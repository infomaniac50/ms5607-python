import ms5607

s = ms5607.MS5607()
old_altitude = 0.0

while True:
    # Reading the sensor and calculating the altitude takes a significant amount of time,
    # so no call to time.sleep is included here.
    altitude = s.read_altitude(samples=10, pressure_osr=4096, temperature_osr=256)
    # Limit altitude to 20cm increments.
    altitude = int(altitude * 5) / 5

    print("altitude={} meters".format(altitude))

    # Calculate climb rate by taking the difference from the current altitude by the old altitude.
    # Convert altitude to centimeters
    climb_rate = round((altitude - old_altitude) * 100)

    print("climb rate={} cm/sec".format(climb_rate))

    old_altitude = altitude
