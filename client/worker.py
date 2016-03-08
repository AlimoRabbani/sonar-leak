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
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 53))
        ip = s.getsockname()[0]
        s.close()
        now_time = datetime.datetime.utcnow()
        try:
            client = connect_to_db()
            device_collection = collection.Collection(client.sonar, "Devices")
            device_collection.update({"device_id": Config.db_config["device_id"]},
                                     {"$set": {"device_ip": ip,
                                               "latest_update": now_time}})
            Config.logger.info("keepalive sent")
        except Exception, e:
            Config.logger.error(e)
        time.sleep(30)

if __name__ == "__main__":
    Config.initialize()
    keepalive_thread = threading.Thread(target=keepalive_worker)
    keepalive_thread.daemon = True
    keepalive_thread.start()
# configure_pins()
# Sampler.start(10)
# time.sleep(1)
# ConvertRaw.convert("/home/pi/log", "/home/pi/log_cleaned")

