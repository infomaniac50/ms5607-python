import ms5607
import time

s = ms5607.MS5607()
old_altitude = 0.0

while True:
    sense_start = time.time()
    # Reading the sensor and calculating the altitude takes a significant amount of time,
    # so we will also measure how long it takes to calculate.
    altitude = s.read_altitude(samples=10, pressure_osr=4096, temperature_osr=256)
    sense_end = time.time()

    # Limit altitude to 20cm increments.
    altitude = int(altitude * 5) / 5

    print("altitude={} meters".format(altitude))

    # Calculate climb rate by taking the difference from the current altitude by the old altitude.
    # Convert altitude to centimeters
    climb_rate = (altitude - old_altitude) * 100

    # Because the sensor takes so long we need to compensate for this.
    # Our unit is centimeters per second.
    # We need to subtract the time it took to read our measurement from our unit.
    sec_unit = sense_end - sense_start
    true_climb_rate = round(climb_rate * sec_unit)
    print("climb rate={} cm/sec".format(true_climb_rate))

    old_altitude = altitude
