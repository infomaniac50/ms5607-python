import unittest
import ms5607

class MS5607Test(unittest.TestCase):
    '''To run tests simply run "python3 test.py"'''

    def setUp(self):
        self.ms5607 = ms5607.MS5607()

    def test_basic_read(self):
        print("pressure={} mBar, temperature={} C".format(*self.ms5607.read()))

    def test_pressure_reads(self):
        for osr in self.ms5607.OSRs:
            print("raw temp(osr={})={}".format(osr, self.ms5607.read_raw_pressure(osr=osr)))

    def test_temperature_reads(self):
        for osr in self.ms5607.OSRs:
            print("raw temp(osr={})={}".format(osr, self.ms5607.read_raw_temperature(osr=osr)))

    def test_stress(self):
        print("Reading the temperature as quickly as possible...")
        for _ in range(50):
            print("raw temp={}".format(self.ms5607.read_raw_temperature(osr=256)))

    def test_stress_init(self):
        print("Creating 50 sensors as quickly as possible...")
        for _ in range(50):
            print("pressure={} mBar, temperature={} C".format(*self.ms5607.read()))

    def test_conversion(self):
        '''Test with the example values given in figure 2 of the datasheet.'''
        old_coeffs = self.ms5607._coeffs
        self.ms5607._coeffs = 46372, 43981, 29059, 27842, 31553, 28165
        p, t = self.ms5607.convert_raw_readings(6465444, 8077636)
        self.ms5607._coeffs = old_coeffs

        self.assertAlmostEqual(p, 1100.02)
        self.assertAlmostEqual(t, 20.00)

if __name__ == '__main__':
    unittest.main(verbosity=2)
