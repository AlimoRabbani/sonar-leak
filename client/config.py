__author__ = 'Alimohammad'

import json
import logging
import os
import sys
import logging.handlers

class Config:
    db_config = dict()
    logger = logging.getLogger("sonar-leak client")
    resource_path = "."
    log_path = "/var/log/sonar-leak/"

    def __init__(self):
        pass

    @staticmethod
    def initialize():
        Config.db_config = json.loads(open(Config.resource_path + "config_db.json").read())

        logger = logging.getLogger("sonar-leak client")
        logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

        file_handler = logging.handlers.RotatingFileHandler(Config.log_path + 'sonar_leak.log', maxBytes=20000000, backupCount=5)

        file_handler.setLevel(logging.DEBUG)

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)

        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

        Config.logger.info("Configurations loaded...")