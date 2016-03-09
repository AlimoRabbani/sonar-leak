from DataCollector import ConvertRaw
from DataCollector import Sampler
import pigpio
import RPi.GPIO as GPIO
import time
import threading
from config import Config

from pymongo import MongoClient
from pymongo import collection

import datetime
import socket


CLK_PIN = 4


def connect_to_db():
    client = MongoClient(host=Config.db_config["db_address"],
                         port=Config.db_config["db_port"])
    client.the_database.authenticate(Config.db_config["db_user"],
                                     Config.db_config["db_password"],
                                     source=Config.db_config["db_auth_source"])
    return client


def handle_db_error(client, e):
    Config.logger.warn("There was a problem connecting to db")
    Config.logger.error(e)
    client.close()


def configure_pins():
    pi = pigpio.pi()
    pi.hardware_PWM(18, 10000, 30000)
    pi.hardware_clock(4, 250000)
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(2, GPIO.IN)


def keepalive_worker():
    while True:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('8.8.8.8', 53))
            ip = s.getsockname()[0]
            s.close()
        except Exception, e:
            Config.logger.error(e)
            s.close()
            ip = ''

        try:
            mac = open('/sys/class/net/wlan0/address').read().strip()
        except Exception, e:
            Config.logger.error(e)
            mac = ''

        now_time = datetime.datetime.utcnow()
        try:
            client = connect_to_db()
            device_collection = collection.Collection(client.sonar, "Devices")
            device_collection.update({"device_id": Config.db_config["device_id"]},
                                     {"$set": {"device_ip": ip,
                                               "latest_update": now_time,
                                               "device_mac": mac}})
            Config.logger.info("keepalive sent")
        except Exception, e:
            Config.logger.error(e)
        time.sleep(30)


def perform_sampling_request(sampling_request):
    Config.logger.info("performing sampling request")
    start_timestamp = datetime.datetime.utcnow()
    try:
        Sampler.start(sampling_request["duration"])
        time.sleep(1)
        ConvertRaw.convert("/home/pi/log", "/home/pi/log_cleaned")
    except Exception, e:
        Config.logger.error(e)
        return

    try:
        client = connect_to_db()
        samples_collection = collection.Collection(client.sonar, "Samples")
        sampling_collection = collection.Collection(client.sonar, "Sampling")
        samples_collection.insert({"device_id": Config.db_config["device_id"],
                                   "timestamp": start_timestamp,
                                   "duration": sampling_request["duration"]})
        sampling_collection.remove({"device_id": Config.db_config["device_id"]})
    except Exception, e:
        handle_db_error(client, e)
        return

    Config.logger.info("sampling request performed")


def request_worker():
    while True:
        Config.logger.info("checking for new sampling requests")
        try:
            client = connect_to_db()
            sampling_collection = collection.Collection(client.sonar, "Sampling")
            sampling_request = sampling_collection.find_one({"device_id": Config.db_config["device_id"]})
            if sampling_request:
                Config.logger.info("new sampling request received with duration %d" % sampling_request["duration"])
                perform_sampling_request(sampling_request)
            else:
                Config.logger.info("no new sampling requests received")
        except Exception, e:
            handle_db_error(client, e)

        time.sleep(0.1)


if __name__ == "__main__":
    Config.initialize()
    configure_pins()

    keepalive_thread = threading.Thread(target=keepalive_worker)
    keepalive_thread.daemon = True
    keepalive_thread.start()

    sampling_request_thread = threading.Thread(target=request_worker)
    sampling_request_thread.daemon = True
    sampling_request_thread.start()

    while True:
        time.sleep(100)
