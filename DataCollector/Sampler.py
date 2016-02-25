from __future__ import print_function
import subprocess
import os


def start(duration):
    pigpio_n = subprocess.Popen(["pigs", "no"], stdout=subprocess.PIPE).communicate()[0]
    pigpio_n = pigpio_n.strip()
    source_filename = "/dev/pigpio" + pigpio_n
    print("Staring copy from %s" % source_filename)
    cp_cmd = "cp " + source_filename + " /home/pi/log&"
    os.system(cp_cmd)
    sampling_cmd = "pigs nb " + pigpio_n + ";" + "sleep " + str(duration) + ";" + "pigs nc " + pigpio_n
    print("Running %s" % sampling_cmd)
    os.system(sampling_cmd)
