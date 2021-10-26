# -*- coding: utf-8 -*-

import os
import sys
import json
import requests
import logging
import logging.handlers
import datetime
import argparse
import smtplib

# PARSING THE ARGUMENTS
parser = argparse.ArgumentParser()
parser.add_argument("-v", "--verbose", help="Set log level to debug",
                    action="store_true")
parser.add_argument("-d", "--delta", help="Set the delta of day(s) from today to check. If not, delta is 0", type=int, default=0)
args = parser.parse_args()
if args.verbose:
    logging_level = "DEBUG"
else:
    logging_level = "INFO"
delta = args.delta

# CONFIG
LOCAL_DIR = os.path.dirname(os.path.abspath(__file__))+"/"
CONFIG_FILE_NAME = 'config.json'
CONFIG_FILE = LOCAL_DIR+CONFIG_FILE_NAME
LIST_SPLIT_STATIONS_FILE_NAME = 'splitStations.json'
LIST_SPLIT_STATIONS_FILE = LOCAL_DIR+LIST_SPLIT_STATIONS_FILE_NAME
LOG_FILE_NAME = 'zettaSpotBlockChecker.log'
LOG_FILE = LOCAL_DIR+LOG_FILE_NAME
DATE = (datetime.datetime.today()+datetime.timedelta(days=delta)).strftime("%Y-%m-%d")

# LOGGING CONFIG
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

formatter_file = logging.Formatter("%(asctime)s|%(levelname)s|%(message)s")
handler_file = logging.handlers.RotatingFileHandler(LOG_FILE, mode="a", maxBytes= 1000000, backupCount= 5, encoding="utf-8")
handler_file.setFormatter(formatter_file)
if args.verbose:
    handler_file.setLevel(logging.DEBUG)
else:
    handler_file.setLevel(logging.INFO)

# handler_smtp = logging.handlers.SMTPHandler(
#               mailhost = ("", 587),
#               fromaddr = "",
#               toaddrs = ["", ""],
#               subject = "ZettaSpotBlockChecker",
#               credentials=("", "")
# #             )
# handler_smtp.setLevel(logging.CRITICAL)
# handler_smtp.setFormatter(formatter_file)

logger.addHandler(handler_file)
# logger.addHandler(handler_smtp)

def sendMail(nb_error, error_msg):
    server = smtplib.SMTP('')
    # .set_debuglevel(1)
    server.connect('', 587)
    server.starttls()
    server.login('', '')
    # server.ehlo()
    fromaddr = ''
    toaddrs = ['', '']
    sujet = f'ZettaSpotBlockChecker - {nb_error} error(s) found !'
    message = u"""ZettaSpotBlockChecker - %s error(s) found ! \n %s""" % (nb_error, error_msg)
    msg = """\
From: %s\r\n\
To: %s\r\n\
Subject: %s\r\n\
\r\n\
%s
""" % (fromaddr, ", ".join(toaddrs), sujet, message)
    try:
        server.sendmail(fromaddr, toaddrs, msg)
        logger.info("Envoi d'un mail")
        print("Envoi d'un mail")
    except smtplib.SMTPException as e:
        logger.info("Probleme d'envoi du mail")
        logger.exception("The following exception occurred :")
        print(e)
    server.quit()


def load_config(CONFIG_FILE):
    """Read splitStationFinder.json and check the config."""
    try:
        config_file = open(CONFIG_FILE)
        config = json.load(config_file)
        # A FAIRE : Faire une vérification si aucune exception    
        config_file.close()
    except:
        logger.exception("The following exception occurred :")
        sys.exit(f"An error has occurred, please read the log file '{LOG_FILE_NAME}' for more details.")
    else:
        return config

def load_list_split_station(LIST_SPLIT_STATIONS_FILE):
    """Read splitStations.json and return the list of stations available."""
    try:
        list_split_station_file = open(LIST_SPLIT_STATIONS_FILE)
        list_split_station = json.load(list_split_station_file)
        list_split_station_file.close()
    except:
        logger.exception("The following exception occurred :")
        sys.exit(f"An error has occurred, please read the log file '{LOG_FILE_NAME}' for more details.")
    else:
        return list_split_station

def request_schedule(config, uuid, DATE):
    """Get schedule of the station identified by uuid. Return the request."""
    try:
        url = f"http://{config['server']}:{config['port']}/ZettaApi/1.0/StationScheduleLog/{uuid}/{DATE}"
        headers = {'user-agent': 'advanced-rest-client','accept': 'application/json','APIKEY': config['APIKEY'],'authorization': 'Basic '+ config['authorization']}
    except:
        logger.exception("The following exception occurred :")
        sys.exit(f"An error has occurred, please read the log file '{LOG_FILE_NAME}' for more details.")
    try:
        req = requests.get(url, headers=headers)
    except:
        logger.exception("The following exception occurred :")
        sys.exit(f"An error has occurred, please read the log file '{LOG_FILE_NAME}' for more details.")
    else:
        return req

def check_req_status_code(req):
    """Check the status of the request. Return the status_code"""
    status_code = req.status_code
    if status_code == 200:
        logger.info(f"{status_code} - Request OK")
        return True
    elif status_code == 404:
        logger.error(f"{status_code} - Request NOK - Not found")
        logger.error(f"The request returns an error.")
        sys.exit(f"The request returns an error, please read the log file '{LOG_FILE_NAME}' for more details.")
    elif status_code == 400:
        logger.error(f"{status_code} - Request NOK - Bad request")
        logger.error(f"The request returns an error.")
        sys.exit(f"The request returns an error, please read the log file '{LOG_FILE_NAME}' for more details.")
    else:
        logger.error(f"{status_code} - Request NOK - Error")
        logger.error(f"The request returns an error.")
        sys.exit(f"The request returns an error, please read the log file '{LOG_FILE_NAME}' for more details.")

def get_response(req):
    """Get the data inside the request. Return the data."""
    try: 
        resp = json.loads(req.text)
    except:
        logger.exception("The following exception occurred :")
        sys.exit(f"An error has occurred, please read the log file '{LOG_FILE_NAME}' for more details.")
    else:
        return resp

def get_schedule_of_all_station(config, list_split_station):
    """Parse the list of split station and get the schedule for each."""
    schedule_by_station = []
    for split_station in list_split_station:
        name = split_station["name"]
        uuid = split_station["uuid"]
        logger.info(f"Station find : {name}")
        req = request_schedule(config, uuid, DATE)
        if check_req_status_code(req):
            resp = get_response(req)
            formated_resp = {}
            name = {'name': split_station["name"]}
            schedule = {'schedule': resp}
            formated_resp.update(name)
            formated_resp.update(schedule)
        schedule_by_station.append(formated_resp)
    return schedule_by_station
     
def get_logEventCollection(hour, hourGroup):
    """Get the logEventCollection if exist. Return it or nothing if doesn't exist."""
    try:
        logEventCollection = hourGroup["logEventCollection"]
    except KeyError:
        logger.info(f"No log for {hour} hour")
    else:
        logger.info(f"Log exists for {hour} hour")
        return logEventCollection

def is_logEventCollection_even(logEventCollection):
    """Check if the logEventCollection is even."""
    try:
        length = len(logEventCollection)
    except:
        logger.exception("The following exception occurred :")
    else:
        if (length % 2 == 0):
            logger.debug(f"logEventCollection is even.")
            return True
        else:
            # Ajouter un envoie de mail en cas d'erreur
            logger.error(f"logEventCollection is not even. ETM and SpotBlock number are not egal.")
            return False

def get_etm_time(hour, event):
    try:
        time = event["exactTimeMarkerEvent"]["time"]
    except KeyError:
        time = "00:00:00"
    except:
        logger.exception("The following exception occurred :")
    finally:
        etm_time = str(hour)+time[2:-3]
        logger.debug(etm_time)
        return etm_time

def get_spotBlock_duration(event):
    """Add the 'duration' of each element in logEventCollection of the spotBlock. Return the spotBlock duration. """
    spotBlock_duration = datetime.datetime.strptime("00:00:00.00000",'%H:%M:%S.%f')
    event_logEventCollection = event["spotBlockEvent"]["logEventCollection"]
    for element in event_logEventCollection:
        duration_str = element["assetEvent"]["effectiveTransitions"]["duration"][:15]
        element_duration = datetime.datetime.strptime(duration_str, '%H:%M:%S.%f')
        spotBlock_duration = spotBlock_duration+datetime.timedelta(hours=element_duration.hour, minutes=element_duration.minute, seconds=element_duration.second, microseconds=element_duration.microsecond)
    spotBlock_duration = spotBlock_duration.time()
    spotBlock_duration_ms = str((spotBlock_duration.hour*360000000)+(spotBlock_duration.minute*60000000)+(spotBlock_duration.second*1000000)+spotBlock_duration.microsecond)[:-3]
    logger.debug(f"Spotblock duration : {spotBlock_duration_ms}")
    return spotBlock_duration_ms

def exists_etm_in_list(spotBlock_duration_list, etm_time):
    try:
        list_of_etm = spotBlock_duration_list.get(etm_time)
    except:
        logger.exception("The following exception occurred :")
    else:
        if list_of_etm:
            logger.debug(f"{etm_time} already exists")
        else:
            logger.debug(f"{etm_time} doesn't exist")
            spotBlock_duration_list.update({etm_time: []})

def put_spotBlock_duration(spotBlock_duration_list, etm_time, infos_to_append):
    list_of_etm = spotBlock_duration_list.get(etm_time)
    list_of_etm.append(infos_to_append)
    logger.debug(f"{infos_to_append} puts in list_of_etm")

def check_logEvent_type(station_name, spotBlock_duration_list, hour, logEventCollection):
    etm_indic = 0
    for event in logEventCollection:
        event_type = event["type"]
        if (event_type == "exactTimeMarker"):
            if (etm_indic == 0):
                logger.debug("The event before this SpotBlock was an SpotBlock")
                etm_time = get_etm_time(hour, event)
                exists_etm_in_list(spotBlock_duration_list, etm_time)
                etm_indic = 1
            else:
                logger.error("The event before this SpotBlock WAS NOT an SpotBlock !")
        if (event_type == "spotBlock"):
            if (etm_indic == 1):
                logger.debug("The event before this SpotBlock was an ETM")
                spotBlock_duration = get_spotBlock_duration(event)
                infos_to_append = {"station" :station_name, "duration": spotBlock_duration}
                put_spotBlock_duration(spotBlock_duration_list, etm_time, infos_to_append)
                etm_indic = 0 
            else:
                logger.error("The event before this SpotBlock WAS NOT an ETM !")

def get_hourGroupCollection(schedule):
    try:
        #Get the dataObjcet of the schedule
        dataObject = schedule["dataObject"]
    except KeyError:
        logger.error("No dataObject. Log is not available.")
        hourGroupCollection = False
        return hourGroupCollection
    else:
        #Get the hourGroupCollection of the dataObject
        hourGroupCollection = dataObject["hourGroupCollection"]
        return hourGroupCollection

def loop_into_schedule(station_name, spotBlock_duration_list, hourGroupCollection):
    # Loop from 0 to 23 to get each hourGroup
        i = 0
        while (i < 24):
            hourGroup = hourGroupCollection[i]
            i += 1
            # Get the hour we are working on
            hour = hourGroup["hour"]
            logger.debug(f"Heure : {hour}")
            # Get the logEventCollection for this hour
            logEventCollection = get_logEventCollection(hour, hourGroup)
            # If logEventCollection exists, do some stuff
            if logEventCollection:
                #Check if logEventCollention is even, supposing ETM and Spotblock are in equal number
                if is_logEventCollection_even(logEventCollection):
                    check_logEvent_type(station_name, spotBlock_duration_list, hour, logEventCollection)

def is_delta_upper_10_percent(etm, list_for_an_etm, max_stretch, error_msg):
    try:
        max_duration = int(max(list_for_an_etm))
        min_duration = int(min(list_for_an_etm))
        delta = abs(max_duration - min_duration)
        delta_percent = abs((delta / max_duration)*100)
    except:
        logger.exception("The following exception occurred :")
        return False
    else:
        logger.debug(f"Min : {min_duration}")
        logger.debug(f"Max : {max_duration}")
        logger.debug(f"Delta : {delta}")
        logger.debug(f"Delta % : {delta_percent}")
        if (delta_percent < max_stretch):
            logger.debug("Everything is OK !")
            is_error = 0
        else: 
            logger.critical(f"Delta is bigger than {max_stretch} % for {etm} ! Please do something to avoid dead air")
            error_msg = error_msg + f"Delta is bigger than {max_stretch} % for {etm} ! Please do something to avoid dead air\n"
            is_error = 1
    return is_error, error_msg

def compare_spotBlock_duration(config, spotBlock_duration_list, error_msg=""):
    error = 0
    max_stretch = config["max_stretch"]
    logger.info(f"Starting the comparison")
    for etm in spotBlock_duration_list:
        list_for_an_etm = []
        logger.info(f'ETM Found : {etm}')
        list_duration = spotBlock_duration_list[etm]
        for station_duration in list_duration:
            logger.debug(f"Station : {station_duration['station']}, duration : {station_duration['duration']}")
            list_for_an_etm.append(station_duration['duration'])
        is_error, error_msg = is_delta_upper_10_percent(etm, list_for_an_etm, max_stretch, error_msg)
        error = error + is_error
    if (error == 0):
        return True
    else:
        logger.info(f"Error : {error}")
        sendMail(error, error_msg)
        return False

if __name__ == '__main__':
    logger.info("------")
    logger.info("STARTUP")
    logger.info(f"Date to check : {DATE}")
    print(f"Date to check : {DATE}")
    # Read config file
    config = load_config(CONFIG_FILE)
    # Read station list
    list_split_station = load_list_split_station(LIST_SPLIT_STATIONS_FILE)
    # Get schedule by station and put it in a dictionnary.
    schedule_by_station = get_schedule_of_all_station(config, list_split_station)
    spotBlock_duration_list = {}
    for a in schedule_by_station:
        station_name = a["name"]
        logger.info(f"Station : {station_name}")
        schedule = a["schedule"]
        hourGroupCollection = get_hourGroupCollection(schedule)
        if (hourGroupCollection == False):
            pass
        else:
            # Loop from 0 to 23 to get each hourGroup
            loop_into_schedule(station_name, spotBlock_duration_list, hourGroupCollection)
    if (spotBlock_duration_list == {}):
        logger.critical(f"Log was not available for a least one station. Please check if log is present in Zetta for {DATE}.")
        print(f"Log was not available for a least one station. Please check if log is present in Zetta for {DATE}.")
    else: 
        if compare_spotBlock_duration(config, spotBlock_duration_list):
            logger.info("No error found, everything is OK.")
            print("No error found, everything is OK.")
        else:
            logger.error("ERROR FOUND !")
            print("ERROR FOUND !")  
