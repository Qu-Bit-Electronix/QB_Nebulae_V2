# Simple example of reading the MCP3008 analog input channels and printing # them all out.  # Author: Tony DiCola # License: Public Domain 
import time 
# Import SPI library (for hardware SPI) and MCP3008 library.  
import Adafruit_GPIO.SPI as SPI 
import MCP3208 
import RPi.GPIO as GPIO 
# Software SPI configuration: 
#CLK  = 18 
#MISO = 23 
#MOSI = 24 
#CS   = 25 
#mcp = Adafruit_MCP3008.MCP3008(clk=CLK, cs=CS, miso=MISO, mosi=MOSI) 
# Hardware SPI configuration: 
SPI_PORT   = 0 
SPI_DEVICE = 0 
CV_Sel_Pin = 8 
POT_Sel_Pin = 7 
mcp = MCP3208.MCP3208(spi=SPI.SpiDev(SPI_PORT, 0)) 
mcp2 = MCP3208.MCP3208(spi=SPI.SpiDev(SPI_PORT, 1))
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(CV_Sel_Pin, GPIO.OUT)
GPIO.setup(POT_Sel_Pin, GPIO.OUT)


print('Reading MCP3008 values, press Ctrl-C to quit...')
# Print nice channel column headers.
print('| {0:>4} | {1:>4} | {2:>4} | {3:>4} | {4:>4} | {5:>4} | {6:>4} | {7:>4} | {0:>4} | {1:>4} | {2:>4} | {3:>4} | {4:>4} | {5:>4} | {6:>4} | {7:>4} |'.format(*range(8)))
print('-' * 57)
# Main program loop.
GPIO.output(CV_Sel_Pin, True)
while True:
    # Read all the ADC channel values in a list.
    values = [0]*16
    for i in range(8):
        # The read_adc function will get the value of the specified channel (0-7).
        values[i] = mcp.read_adc(i)
        values[i+8] = mcp2.read_adc(i)
    # Print the ADC values.
    print('| {0:>4} | {1:>4} | {2:>4} | {3:>4} | {4:>4} | {5:>4} | {6:>4} | {7:>4} | {8:>4} | {9:>4} | {10:>4} | {11:>4} | {12:>4} | {13:>4} | {14:>4} | {15:>4} |'.format(*values))
    # Pause for half a second.
    time.sleep(0.1)
