#!/usr/bin/python3

import requests
import subprocess


def check_connection():
    try:
        test_connection = requests.get('https://get.geojs.io/v1/ip/geo.json', timeout=.5)
        return test_connection.status_code
    except Exception:
        pass


def get_ip_info_json():
    try:
        ip_info_json = requests.get('https://get.geojs.io/v1/ip/geo.json', timeout=.5).json()
        return ip_info_json
    except Exception:
        pass


def kill_transmission():
    transmission_pid = ()
    get_trans_pid = "ps -eo pid,etime,comm | grep 'transmission-da' | awk '{ print $1 }'"
    transmission_pid = subprocess.check_output([get_trans_pid], shell=True).decode('utf-8')
    if transmission_pid:
        # transmission_pid = subprocess.check_output([get_trans_pid], shell=True).decode('utf-8')
        subprocess.check_output(['kill -9 {}'.format(transmission_pid.split()[0])], shell=True)
    else:
        print("transmission is already dead")


if check_connection() != 200:
    print("possible connection issues")
    print("killing transmission")
    kill_transmission()
elif check_connection() == 200 and get_ip_info_json()['region'] != 'Florida' :
    print("killing transmission")
    kill_transmission()
else:
    print("VPN Checks Healthy")
    print('Conncted to {}'.format(get_ip_info_json()['region']))