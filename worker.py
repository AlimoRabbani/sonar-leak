from DataCollector import ConvertRaw
import pigpio
import RPI.GPIO as GPIO
import subprocess

CLK_PIN = 4


def configure_pins():
    pi = pigpio.pi()
    pi.hardware_PWM(18, 10000, 30000)
    pi.hardware_clock(4, 250000)
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(2, GPIO.IN)

if __name__ == "__main__":
    configure_pins()
    subprocess.call(["sudo", "pigpiod", "-s2"])
    subprocess.call(["pigs", "no"])
    subprocess.call(["cp", "/dev/pigpio0", "/home/pi/log&"])
    subprocess.call(["pigs", "nb", "0", "$((1<<%d))" % CLK_PIN])
    subprocess.call(["sleep", "30"])
    subprocess.call(["pigs", "nc", "0"])
    # ConvertRaw.convert("/Users/Alimohammad/Documents/Development/sonar-leak/data.bin", "data_out.bin")