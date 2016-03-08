from __future__ import print_function
from __future__ import division
import struct
import datetime

CLK_PIN = 4
CS_PIN = 18
DATA_PIN = 2
VOLTAGE = 10


def convert(in_name, out_name):
    print("Converter Started...")
    start_time = datetime.datetime.now()
    input_file = open(in_name, 'rb')
    voltage_values = list()
    #start_seq is the number of wasted clock events before the first sample.
    start_seq = read_till_cs_low(input_file)
    try:
        while True:
            skip_first_eight_data_bits(input_file)
            data = read_data_bits(input_file)
            voltage_values.append(convert_to_voltage(data))
            read_till_cs_low(input_file)
    except Exception, e:
        input_file.close()
    finally:
        input_file.close()
    input_file.close()
    read_end = datetime.datetime.now()
    print("Time taken to read data: %f" % (read_end - start_time).total_seconds())
    output_file = open(out_name, 'w')
    for item in voltage_values:
        print("%f" % item, file=output_file)
    output_file.close()
    print("%d Total Samples Extracted..." % len(voltage_values))
    print("Time taken to write to file: %f" % (datetime.datetime.now() - read_end).total_seconds())


def print_sample(sample, message=""):
    int_value = struct.unpack('<I', sample)[0]
    clk_bit = int_value >> CLK_PIN & 1
    cs_bit = int_value >> CS_PIN & 1
    data_bit = int_value >> DATA_PIN & 1
    rep = (clk_bit << 2) + (cs_bit << 1) + data_bit
    print("{0:03b}".format(rep) + " " + message)


def read_till_cs_low(input_file):
    seq = 0
    try:
        while True:
            input_file.seek(8, 1) #skip the garbage
            sample = input_file.read(4)
            int_value = struct.unpack('<I', sample)[0]
            cs_bit = int_value >> CS_PIN & 1
            seq += 1
            if cs_bit == 1:
                input_file.seek(12, 1) #skip the garbage
                return seq
    except Exception, e:
        raise


def skip_first_eight_data_bits(input_file):
    try:
        for i in range(0, 16):
            input_file.seek(12, 1)
    except Exception, e:
        raise


def read_data_bits(input_file):
    data = 0
    bit_counter = 0
    try:
        while bit_counter < 16:
            input_file.seek(8, 1)
            sample = input_file.read(4)
            int_value = struct.unpack('<I', sample)[0]
            clk_bit = int_value >> CLK_PIN & 1
            data_bit = int_value >> DATA_PIN & 1
            if clk_bit == 1:
                data |= (data_bit << (15 - bit_counter))
                bit_counter += 1
        return data
    except Exception, e:
        raise


def convert_to_voltage(data):
    return VOLTAGE * (data / 0xffff)