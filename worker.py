from DataCollector import ConvertRaw
import pigpio
import RPi.GPIO as GPIO
import subprocess

CLK_PIN = 4


def configure_pins():
    pi = pigpio.pi()
    pi.hardware_PWM(18, 10000, 30000)
    pi.hardware_clock(4, 250000)
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(2, GPIO.IN)

if __name__ == "__main__":
    print "pigpiod -s2"
    subprocess.call(["pigpiod", "-s2"])
    configure_pins()
    print "pigs no"
    subprocess.call(["pigs", "no"])
    print "cp /dev/pigpio1 /home/pi/log&"
    subprocess.call(["cp", "/dev/pigpio0", "/home/pi/log&"])
    print "pigs nb 0 $((1<<%d))" % CLK_PIN
    subprocess.call(["pigs", "nb", "0", "$((1<<%d))" % CLK_PIN])
    print "sleep 30"
    subprocess.call(["sleep", "30"])
    print "pigs nc 0"
    subprocess.call(["pigs", "nc", "0"])
    # ConvertRaw.convert("/Users/Alimohammad/Documents/Development/sonar-leak/data.bin", "data_out.bin")