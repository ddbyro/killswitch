import requests
import subprocess
import os
import signal
import time
import logging

# Set up logging to a file with INFO level and a specific format
logging.basicConfig(filename='transmission_health.log', level=logging.INFO, format='%(asctime)s %(message)s')

def get_ip_info_json():
    """
    Fetches IP information in JSON format from a web service.
    """
    try:
        ip_info_json = requests.get('https://get.geojs.io/v1/ip/geo.json', timeout=5)
        return ip_info_json
    except requests.exceptions.RequestException as e:
        logging.error("Request failed: {}".format(e))  # Log any request exceptions
        return None

def is_transmission_running():
    """
    Checks if the 'transmission-da' process is running.
    """
    ps = subprocess.Popen(('ps', '-eo', 'pid,etime,comm'), stdout=subprocess.PIPE)
    try:
        output = subprocess.check_output(('grep', 'transmission-da'), stdin=ps.stdout)
        ps.wait()
        return bool(output.strip())  # Return True if the process is running, False otherwise
    except subprocess.CalledProcessError:
        logging.info("transmission-da process not found")
        return False

def kill_transmission():
    """
    Kills the 'transmission-daemon.service' process.
    """
    ps = subprocess.Popen(('ps', '-eo', 'pid,etime,comm'), stdout=subprocess.PIPE)
    try:
        output = subprocess.check_output(('grep', 'transmission-daemon.service'), stdin=ps.stdout)
        ps.wait()
        transmission_pid = output.strip().split()[0]
        if transmission_pid:
            os.kill(int(transmission_pid), signal.SIGKILL)  # Kill the process if it's running
        else:
            logging.info("transmission is already dead")
    except subprocess.CalledProcessError:
        logging.info("transmission-daemon.service process not found")

def restart_vpn():
    """
    Restarts the VPN service using systemctl and logs the status and IP region before and after the restart.
    """
    # Fetch and log IP region before restart
    try:
        ip_info_json_before = get_ip_info_json()
        if ip_info_json_before is not None:
            logging.info("IP region before restart: {}".format(ip_info_json_before.json()['region']))
    except requests.exceptions.RequestException as e:
        logging.error("Request failed: {}".format(e))

    # Fetch and log VPN status before restart
    try:
        status_before = subprocess.check_output(["sudo", "systemctl", "is-active", "pia.service"]).decode().strip()
        logging.info("VPN status before restart: {}".format(status_before))
    except subprocess.CalledProcessError:
        logging.info("VPN service not found or not active before restart")

    subprocess.run(["sudo", "systemctl", "restart", "pia.service"])  # Restart the VPN service

    # Fetch and log VPN status after restart
    try:
        status_after = subprocess.check_output(["sudo", "systemctl", "is-active", "pia.service"]).decode().strip()
        logging.info("VPN status after restart: {}".format(status_after))
    except subprocess.CalledProcessError:
        logging.info("VPN service not found or not active after restart")

    time.sleep(5)  # Wait for 5 seconds

    # Fetch and log IP region after restart
    try:
        ip_info_json_after = get_ip_info_json()
        if ip_info_json_after is not None:
            logging.info("IP region after restart: {}".format(ip_info_json_after.json()['region']))
    except requests.exceptions.RequestException as e:
        logging.error("Request failed: {}".format(e))

def start_transmission():
    """
    Starts the 'transmission-daemon.service' process using systemctl and logs the status before and after the start.
    """
    # Fetch and log transmission status before start
    try:
        status_before = subprocess.check_output(["sudo", "systemctl", "is-active", "transmission-daemon.service"]).decode().strip()
        logging.info("Transmission status before start: {}".format(status_before))
    except subprocess.CalledProcessError:
        logging.info("Transmission service not found or not active before start")

    subprocess.run(["sudo", "systemctl", "start", "transmission-daemon.service"])  # Start the transmission service

    # Fetch and log transmission status after start
    try:
        status_after = subprocess.check_output(["sudo", "systemctl", "is-active", "transmission-daemon.service"]).decode().strip()
        logging.info("Transmission status after start: {}".format(status_after))
    except subprocess.CalledProcessError:
        logging.info("Transmission service not found or not active after start")

# TODO: Impliment limit on retries if vpn unhealthy

def is_vpn_valid():
    """
    Checks if the VPN is valid by checking the IP region. If the region is 'Utah', it's considered invalid.
    """
    ip_info_json = get_ip_info_json()
    if ip_info_json is None or ip_info_json.json()['region'] == 'Utah':
        return False
    return True

# Main loop
while True:
    if is_vpn_valid():
        if not is_transmission_running():
            logging.info("starting transmission")
            start_transmission()
    else:
        logging.info("VPN is not valid, restarting VPN and killing transmission")
        kill_transmission()
        restart_vpn()

    time.sleep(10)  # Wait for 10 seconds before the next iteration
