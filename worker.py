from DataCollector import ConvertRaw
from DataCollector import Sampler
import pigpio
import RPi.GPIO as GPIO
import time

CLK_PIN = 4


def configure_pins():
    pi = pigpio.pi()
    pi.hardware_PWM(18, 10000, 30000)
    pi.hardware_clock(4, 250000)
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(2, GPIO.IN)

if __name__ == "__main__":
    configure_pins()
    Sampler.start(10)
    time.sleep(1)
    ConvertRaw.convert("/home/pi/log", "/home/pi/log_cleaned")