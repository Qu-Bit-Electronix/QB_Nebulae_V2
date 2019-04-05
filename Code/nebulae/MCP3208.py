import Adafruit_GPIO as GPIO
import Adafruit_GPIO.SPI as SPI

# Currently the SPI clock is set to 2MHz. The datasheet recommends 1MHz at 2.7Vdd and 2MHz at 5Vdd. 
# We're reading 14 channels of adcs, so if we don't NEED to run it slow, then I don't want to.

class MCP3208(object):

    def __init__(self, clk=None, cs=None, miso=None, mosi=None, spi=None, gpio=None):
        """Initialize MAX31855 device with software SPI on the specified CLK,
        CS, and DO pins.  Alternatively can specify hardware SPI by sending an
        Adafruit_GPIO.SPI.SpiDev device in the spi parameter.
        """
        self._spi = None
        # Handle hardware SPI
        if spi is not None:
            self._spi = spi
        elif clk is not None and cs is not None and miso is not None and mosi is not None:
            # Default to platform GPIO if not provided.
            if gpio is None:
                gpio = GPIO.get_platform_gpio()
            self._spi = SPI.BitBang(gpio, clk, mosi, miso, cs)
        else:
            raise ValueError('Must specify either spi for for hardware SPI or clk, cs, miso, and mosi for softwrare SPI!')
        #self._spi.set_clock_hz(800000)
        #self._spi.set_clock_hz(1000000)
        self._spi.set_clock_hz(1000000)
        self._spi.set_mode(0)
        self._spi.set_bit_order(SPI.MSBFIRST)

    def read_adc(self, adc_number):
        """Read the current value of the specified ADC channel (0-7).  The values
        can range from 0 to 1023 (10-bits).
        """
        assert 0 <= adc_number <= 7, 'ADC number must be a value of 0-7!'
        # Build a single channel read command.
        # For example channel zero = 0b11000000
        #command = 0b11 << 6                  # Start bit, single channel read
        #command |= (adc_number & 0x07) << 3  # Channel number (in 3 bits)
        # Note the bottom 3 bits of command are 0, this is to account for the
        # extra clock to do the conversion, and the low null bit returned at
        # the start of the response.
        #command_a = 0b0000011 | (adc_number & (1 << 2))
        #command_a |= (adc_number & (1 << 2))
        #print "############################"
        #print "ADC Number: " + str(adc_number)
        #print "Send Commands: " + bin(command_a) + " | " + bin(command_b) + " | " + bin(0x0)
        #print "Retr Commands: " + bin(resp[0]) + " | " + bin(resp[1]) + " | " + bin(resp[2])
        #print "Value: " + str(result)
        #print "############################"
        command_a = 0b110 # six 
        if adc_number > 3:
            command_a |= (1 << 0)
        command_b = ((adc_number & 3) << 6)
        resp = self._spi.transfer([command_a, command_b, 0x0])
        result = resp[2] | (resp[1] << 8)
        return result & 0xFFF

