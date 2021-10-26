# -*- coding: utf-8 -*-

import os
import sys
import json
from zettaSpotBlockChecker import LIST_SPLIT_STATIONS_FILE
import requests
import re
from requests.api import request
import logging
from logging.handlers import RotatingFileHandler

# A FAIRE : typer les variables 

# CONFIG
LOCAL_DIR = os.path.dirname(os.path.abspath(__file__))+"/"
CONFIG_FILE_NAME = 'config.json'
CONFIG_FILE = LOCAL_DIR+CONFIG_FILE_NAME
LIST_SPLIT_STATIONS_OUTPUT_FILE_NAME = 'splitStations.json'
LIST_SPLIT_STATIONS_OUTPUT_FILE = LOCAL_DIR+LIST_SPLIT_STATIONS_OUTPUT_FILE_NAME
LOG_FILE_NAME = 'splitStationFinder.log'
LOG_FILE = LOCAL_DIR+LOG_FILE_NAME


# LOGGING CONFIG
logger_file = logging.getLogger("logger_file")
handler_file = logging.handlers.RotatingFileHandler(LOG_FILE, mode="a", maxBytes= 1000000, backupCount= 5, encoding="utf-8")
formatter_file = logging.Formatter("%(asctime)s|%(levelname)s|%(message)s")
handler_file.setFormatter(formatter_file)
logger_file.setLevel(logging.INFO)
logger_file.addHandler(handler_file)


def load_config(CONFIG_FILE):
    """Read splitStationFinder.json and check the config."""
    try:
        config_file = open(CONFIG_FILE)
        config = json.load(config_file)
        # A FAIRE : Faire une vérification si aucune exception    
        config_file.close()
    except:
        logger_file.exception("The following exception occurred :")
        sys.exit(f"An error has occurred, please read the log file '{LOG_FILE_NAME}' for more details.")
    else:
        return config

def request_list_stations(config):
    """Get list of station available on the server. Return the requests."""
    try:
        url = f"http://{config['server']}:{config['port']}/ZettaApi/1.0/Station/list"
        headers = {'user-agent': 'advanced-rest-client','accept': 'application/json','APIKEY': config['APIKEY'],'authorization': 'Basic '+ config['authorization']}
    except:
        logger_file.exception("The following exception occurred :")
        sys.exit(f"An error has occurred, please read the log file '{LOG_FILE_NAME}' for more details.")
    try:
        req = requests.get(url, headers=headers)
    except:
        logger_file.exception("The following exception occurred :")
        sys.exit(f"An error has occurred, please read the log file '{LOG_FILE_NAME}' for more details.")
    else:
        return req
    

def check_req_status_code(req):
    """Check the status of the request. Return the status_code"""
    status_code = req.status_code
    if status_code == 200:
        logger_file.info(f"{status_code} - Request OK")
        print(f"{status_code} - Request OK")
        return True
    elif status_code == 404:
        logger_file.error(f"{status_code} - Request NOK - Not found")
        print(f"{status_code} - Request NOK - Not found")
        logger_file.error(f"The request returns an error.")
        sys.exit(f"The request returns an error, please read the log file '{LOG_FILE_NAME}' for more details.")
    elif status_code == 400:
        logger_file.error(f"{status_code} - Request NOK - Bad request")
        print(f"{status_code} - Request NOK - Bad request")
        logger_file.error(f"The request returns an error.")
        sys.exit(f"The request returns an error, please read the log file '{LOG_FILE_NAME}' for more details.")
    else:
        logger_file.error(f"{status_code} - Request NOK - Error")
        print(f"{status_code} - Request NOK - Error")
        logger_file.error(f"The request returns an error.")
        sys.exit(f"The request returns an error, please read the log file '{LOG_FILE_NAME}' for more details.")

def is_station_a_station(list):
    """Check if the station role from the list is 'station' and not 'backgroundTask. Return a list of station with the role set as 'station' """
    stations = []
    try:
        for station in list:
            if station['role'] == 'station':
                stations.append(station)
    except:
        logger_file.exception("The following exception occurred :")
        sys.exit(f"An error has occurred, please read the log file '{LOG_FILE_NAME}' for more details.")
    else:
        return stations

def does_it_match_to_patern(stations, pattern):
    """Check if the station match with the pattern defined in config file"""
    p = re.compile(pattern)
    split_stations = []
    for station in stations:
        m = p.match(station['name'])
        if m:
            split_stations.append(station)
    return split_stations

def parse_list_stations(req, config):
    """Parse the list of stations. Return a collection of list"""
    try: 
        resp = json.loads(req.text)
        list = resp['dataObject']
        stations = is_station_a_station(list)
        pattern = config['pattern']
        split_stations = does_it_match_to_patern(stations, pattern)
    except:
        logger_file.exception("The following exception occurred :")
        sys.exit(f"An error has occurred, please read the log file '{LOG_FILE_NAME}' for more details.")
    else:
        return split_stations

def create_list_split_stations(split_stations):
    """Create the list of split station. Return a dictionnary"""
    list_split_stations = []
    try:
        for station in split_stations:
            name = {'name': station['name']}
            uuid = {'uuid': station['uuid']}
            logger_file.info(f'Station find : {name} - {uuid}')
            print(f'Station find : {name} - {uuid}')
            list_to_append = {}
            list_to_append.update(name)
            list_to_append.update(uuid)
            list_split_stations.append(list_to_append)
    except:
        logger_file.exception("The following exception occurred :")
        sys.exit(f"An error has occurred, please read the log file '{LOG_FILE_NAME}' for more details.")
    else:
        return list_split_stations

def write_list_splite_stations_json (LIST_SPLIT_STATIONS_FILE, list_split_stations):
    """Write the list of split station in the JSON file. Return nothing."""
    try: 
        file = open(LIST_SPLIT_STATIONS_FILE, 'w')
        a = json.dump(list_split_stations, file)
        file.close()
    except:
        logger_file.exception("The following exception occurred :")
        sys.exit(f"An error has occurred, please read the log file '{LOG_FILE}' for more details.")
    else:
        logger_file.info(f"List split station file was created correctly in '{LIST_SPLIT_STATIONS_OUTPUT_FILE_NAME}'.")
        print(f"List split station file was created correctly in '{LIST_SPLIT_STATIONS_OUTPUT_FILE_NAME}'.")
        return None

if __name__ == '__main__':
    logger_file.info("STARTUP")
    config = load_config(CONFIG_FILE)
    req = request_list_stations(config)
    if check_req_status_code(req):
        split_stations = parse_list_stations(req, config)
        list_split_stations = create_list_split_stations(split_stations)
        write_list_splite_stations_json(LIST_SPLIT_STATIONS_OUTPUT_FILE, list_split_stations)