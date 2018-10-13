import glob
import time
import requests
import datetime
from requests.exceptions import ConnectionError
from dotenv import load_dotenv
import os

env_path = os.path.dirname(os.path.realpath(__file__)) + '/.env'
load_dotenv(dotenv_path=env_path, verbose=True)
base_dir = '/sys/bus/w1/devices/'
device_folder = glob.glob(base_dir + '28*')[0]
device_file = device_folder + '/w1_slave'
SECRET = os.getenv("SECRET")
BREWURL = os.getenv("BREWURL")
last_dispatch = -1
dispatch_threshold = 60  # One minute
measurement_interval = 5
data = []


def read_temp_raw():
    f = open(device_file, 'r')
    lines = f.readlines()
    f.close()
    return lines


def read_temp():
    lines = read_temp_raw()
    while lines[0].strip()[-3:] != 'YES':
        time.sleep(0.2)
        lines = read_temp_raw()
    equals_pos = lines[1].find('t=')
    if equals_pos != -1:
        temp_string = lines[1][equals_pos + 2:]
        temp_c = float(temp_string) / 1000.0
        temp_f = temp_c * 9.0 / 5.0 + 32.0
        return temp_c, temp_f


def send_temp():
    global last_dispatch
    global data
    print "Dispatching temp..."
    try:
        requests.post(BREWURL, json={'data': data, 'secret': SECRET})
        last_dispatch = time.time()
        data = []
    except ConnectionError:
        print 'Failed to open url.'


while True:
    global data
    temp = read_temp()[0]
    payload = {
        'temperature': temp,
        'time': str(datetime.datetime.now())
    }
    data.append(payload)
    if last_dispatch == -1 or last_dispatch < time.time() - dispatch_threshold:
        send_temp()
    time.sleep(measurement_interval)
