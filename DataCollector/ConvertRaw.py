from __future__ import print_function
import struct

CLK_PIN = 4
CS_PIN = 18
DATA_PIN = 2


def convert(in_name, out_name):
    input_file = open(in_name, 'rb')
    output_file = open(out_name, 'w')

    #start_seq is the number of wasted clock events before the first sample.
    start_seq = read_till_cs_low(input_file)
    try:
        while True:
            skip_first_eight_data_bits(input_file)
            data = read_data_bits(input_file)
            print("0x%04x" % data, file=output_file)
            read_till_cs_low(input_file)
    finally:
        input_file.close
    input_file.close()
    output_file.close()


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
            input_file.read(8) #read the garbage
            sample = input_file.read(4)
            # print_sample(sample, "SKIP CS!")
            int_value = struct.unpack('<I', sample)[0]
            cs_bit = int_value >> CS_PIN & 1
            seq += 1
            if cs_bit == 1:
                input_file.read(8) #read the garbage
                sample = input_file.read(4)
                # print_sample(sample, "SKIP CS!")
                return seq
    except Exception, e:
        print(e.message)
        exit(1)


def skip_first_eight_data_bits(input_file):
    for i in range(0, 16):
        input_file.read(8)
        sample = input_file.read(4)
        # print_sample(sample, "SKIP BITs >> %d" % i)

def read_data_bits(input_file):
    data = 0
    bit_counter = 0
    while bit_counter < 16:
        input_file.read(8)
        sample = input_file.read(4)
        int_value = struct.unpack('<I', sample)[0]
        clk_bit = int_value >> CLK_PIN & 1
        data_bit = int_value >> DATA_PIN & 1
        if clk_bit == 1:
            data += (data_bit << (15 - bit_counter))
            # print_sample(sample, "READ BIT >> %d" % (15 - bit_counter))
            bit_counter += 1
    return data

