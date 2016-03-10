__author__ = 'Alimohammad'

from flask import current_app
import datetime

from dateutil import tz
import random
import string
import hashlib
import uuid
import numpy as np
import scipy.fftpack
import math
import scipy

from pymongo import MongoClient
from pymongo import collection
import pymongo
import urllib2

def connect_to_db():
    client = MongoClient(host=current_app.config["custom_config"]["db_address"],
                         port=current_app.config["custom_config"]["db_port"])
    client.the_database.authenticate(current_app.config["custom_config"]["db_user"],
                                     current_app.config["custom_config"]["db_password"],
                                     source=current_app.config["custom_config"]["db_auth_source"])
    return client


def handle_db_error(client, e):
    current_app.logger.warn("There was a problem reading from db")
    current_app.logger.error(e)
    client.close()


class User:
    def __init__(self, user_dict):
        self.user_id = user_dict["user_id"]
        self.name = user_dict["name"]
        self.email = user_dict["email"]
        self.hashed_password = user_dict["password"]
        self.password_salt = user_dict["password_salt"]
        self.phone = user_dict["phone"]
        self.role = user_dict["role"]
        if "forgot_secret" in user_dict:
            self.forgot_secret = user_dict["forgot_secret"]
        self.authenticated = False
        self.active = True
        self.anonymous = False

    @staticmethod
    def get(email=None, user_id=None):
        user_dict = None
        try:
            client = connect_to_db()
            user_collection = collection.Collection(client.sonar, "Users")
            user_dict = None
            if email:
                user_dict = user_collection.find_one({"email": email})
                current_app.logger.info("fetched user info for '%s'" % str(email))
            elif user_id:
                user_dict = user_collection.find_one({"user_id": user_id})
                current_app.logger.info("fetched user info for '%s'" % str(user_id))

            client.close()
        except Exception, e:
            handle_db_error(client, e)

        if user_dict is not None:
            user = User(user_dict)
            user.authenticated = True
            return user
        return None

    def get_device(self, device_id):
        device_dict = None
        try:
            client = connect_to_db()
            device_collection = collection.Collection(client.sonar, "Devices")
            device_dict = device_collection.find_one({"device_id": device_id})
            current_app.logger.info("fetched %s" % str(device_dict))
            client.close()
        except Exception, e:
            handle_db_error(client, e)

        device = None
        if device_dict:
            device = Device(device_dict)
            if device.device_owner == self.user_id or self.role == "admin":
                return device
        return device

    def find_devices(self):
        return Device.find_devices(self.user_id)

    def authenticate(self, password):
        hashed_password = hashlib.sha512(password + self.password_salt).hexdigest()
        if hashed_password == self.hashed_password:
            return True
        else:
            return False

    def is_authenticated(self):
        return self.authenticated

    def is_active(self):
        return self.active

    def is_anonymous(self):
        return self.anonymous

    def get_id(self):
        return self.email


class Device:
    def __init__(self, device_dict):
        self.device_id = device_dict["device_id"]
        self.device_owner = device_dict["user_id"]
        self.device_location = device_dict["device_location"]
        self.device_ip = device_dict["device_ip"]
        self.device_mac = device_dict["device_mac"]
        self.is_alive = True
        self.latest_update_time = None

        try:
            from_zone = tz.tzutc()
            to_zone = tz.tzlocal()
            utc = device_dict["latest_update"].replace(tzinfo=from_zone)
            self.latest_update_time = utc.astimezone(to_zone)
        except KeyError:
            current_app.logger.warn("No latest update for '%s'" % self.device_id)

        self.update_warnings()

    @staticmethod
    def find_devices(user_id):
        devices = None
        try:
            client = connect_to_db()
            device_collection = collection.Collection(client.sonar, "Devices")
            devices = list(device_collection.find({"user_id": user_id}))
            current_app.logger.info("fetched %d devices for user '%s'" % (len(devices), str(user_id)))
            client.close()
        except Exception, e:
            handle_db_error(client, e)

        device_list = list()
        for device_dict in devices:
            device = Device(device_dict)
            device_list.append(device)
        return device_list

    @staticmethod
    def find_all_devices():
        devices = None
        try:
            client = connect_to_db()
            device_collection = collection.Collection(client.sonar, "Devices")
            devices = list(device_collection.find())
            current_app.logger.info("fetched %d all devices" % len(devices))
            client.close()
        except Exception, e:
            handle_db_error(client, e)

        device_list = list()
        for device_dict in devices:
            device = Device(device_dict)
            device_list.append(device)
        return device_list

    def request_sampling(self, duration=10):
        try:
            client = connect_to_db()
            sampling_collection = collection.Collection(client.sonar, "Sampling")
            now_time = datetime.datetime.utcnow()
            pending_sample = sampling_collection.find_one({"device_id": self.device_id})
            if pending_sample:
                return 1, "Another sample is pending. Please wait!"
            sampling_collection.insert({"device_id": self.device_id, "timestamp": now_time, "duration": duration})
            current_app.logger.info("submitted sampling request for %s" % self.device_id)
            client.close()
            return 0, "Sampling request successfully submitted!"
        except Exception, e:
            handle_db_error(client, e)
        return 1, "Could not initiate a sampling request!"

    def get_past_samples(self):
        past_samples = list()
        try:
            client = connect_to_db()
            samples_collection = collection.Collection(client.sonar, "Samples")
            past_samples = list(samples_collection.find({"device_id": self.device_id}).sort("timestamp", pymongo.DESCENDING))
            for sample in past_samples:
                from_zone = tz.tzutc()
                to_zone = tz.tzlocal()
                utc = sample["timestamp"].replace(tzinfo=from_zone)
                sample["timestamp"] = utc.astimezone(to_zone)
            client.close()
        except Exception, e:
            handle_db_error(client, e)

        return past_samples

    @staticmethod
    def get_pressure_timeseries_data(sample_id):
        raw_data = Device.get_raw_data(sample_id)
        data = list()
        for line in raw_data:
            value = float(line) / 0.0000241395
            data.append(value)
            # data.append(0 - value)
        original = np.array(data)
        R = len(data) / 1000
        pad_size = math.ceil(float(original.size)/R)*R - original.size
        original_padded = np.append(original, np.zeros(pad_size)*np.NaN)
        downsampled = scipy.nanmean(original_padded.reshape(-1, R), axis=1)
        xf = np.linspace(0.0, len(data) / 10, num=1000)
        result = zip(xf.tolist(), downsampled.tolist())
        return result

    @staticmethod
    def get_fft_data(sample_id):
        raw_data = Device.get_raw_data(sample_id)
        data = list()
        for line in raw_data:
            value = float(line) / 0.0000241395
            data.append(value)
            # data.append(0 - value)
        # Number of samplepoints
        N = len(data)
        # sample spacing
        T = 1.0 / 10000.0
        y = np.array(data)
        yf = scipy.fftpack.fft(y)
        yf2 = 2.0/N * np.abs(yf[:N/2])
        # yf2n = np.linalg.norm(yf2)
        # R = yf2.size / 1000
        # pad_size = math.ceil(float(yf2.size)/R)*R - yf2.size
        # original_padded = np.append(yf2, np.zeros(pad_size)*np.NaN)
        # downsampled = scipy.nanmean(original_padded.reshape(-1, R), axis=1)
        xf = np.linspace(0.0, 1.0/(100.0*T), N/100)
        result = zip(xf.tolist(), yf2.tolist())
        return result

    @staticmethod
    def get_raw_data(sample_id):
        raw_url = ""
        try:
            client = connect_to_db()
            samples_collection = collection.Collection(client.sonar, "Samples")
            sample = samples_collection.find_one({"sample_id": sample_id})
            raw_url = sample["raw_url"]
            client.close()
        except Exception, e:
            handle_db_error(client, e)
            return list()
        return urllib2.urlopen(raw_url)


    def update_warnings(self):
        self.is_alive = False
        if not self.latest_update_time:
            return
        if (datetime.datetime.utcnow().replace(tzinfo=tz.tzutc()).astimezone(tz.tzlocal()) - self.latest_update_time).total_seconds() < current_app.config["custom_config"]["keepalive_interval"]:
            self.is_alive = True