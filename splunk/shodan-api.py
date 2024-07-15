import shodan
import json
import time
import os
import logging
import signal
import sys
from retrying import retry
from logging.handlers import TimedRotatingFileHandler
import requests

# Load configuration from config.json
config_path = 'config.json'
if not os.path.isfile(config_path):
    raise FileNotFoundError(f"Configuration file not found: {config_path}")

with open(config_path) as config_file:
    config = json.load(config_file)

required_keys = {'log_folder', 'api_key', 'queries', 'splunk_url', 'splunk_token'}
if not required_keys.issubset(config.keys()):
    raise ValueError(f"Configuration file must contain keys: {required_keys}")

# Shodan API key from config.json
SHODAN_API_KEY = config['api_key']
if not SHODAN_API_KEY:
    raise ValueError("Shodan API key must be set in the configuration file")

# Splunk HEC configuration
SPLUNK_URL = config['splunk_url']
SPLUNK_TOKEN = config['splunk_token']

api = shodan.Shodan(SHODAN_API_KEY)

log_folder = config['log_folder']
os.makedirs(log_folder, exist_ok=True)
log_file_path = os.path.join(log_folder, 'shodan_data.log')

# Configure logging with TimedRotatingFileHandler
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

handler = TimedRotatingFileHandler(log_file_path, when="midnight", interval=1, backupCount=7)
handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
logger.addHandler(handler)

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
logger.addHandler(console_handler)

logging.info('Starting Shodan data fetch script')

def signal_handler(sig, frame):
    logging.info('Received shutdown signal, exiting...')
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

@retry(stop_max_attempt_number=3, wait_fixed=2000)
def fetch_shodan_data(query):
    return api.search(query)

def send_to_splunk(data):
    headers = {
        'Authorization': f'Splunk {SPLUNK_TOKEN}',
        'Content-Type': 'application/json'
    }
    response = requests.post(SPLUNK_URL, headers=headers, data=json.dumps(data))
    if response.status_code != 200:
        logging.error(f'Failed to send data to Splunk: {response.text}')
    else:
        logging.info('Data successfully sent to Splunk')

def fetch_and_save_shodan_data():
    queries = config['queries']
    with open(log_file_path, 'a') as log_file:
        for query in queries:
            logging.info(f'Executing query: {query}')
            try:
                results = fetch_shodan_data(query)
                logging.info(f'Query successful: {query}, found {len(results["matches"])} results')
                for result in results['matches']:
                    log_data = {
                        "query": query,
                        "reason": "Relevant Shodan search result",
                        "ip": result.get("ip_str", "N/A"),
                        "port": result.get("port", "N/A"),
                        "transport": result.get("transport", "N/A"),
                        "location": {
                            "city": result.get("location", {}).get("city", "N/A"),
                            "country_name": result.get("location", {}).get("country_name", "N/A"),
                            "longitude": result.get("location", {}).get("longitude", "N/A"),
                            "latitude": result.get("location", {}).get("latitude", "N/A")
                        },
                        "vulns": result.get("vulns", "N/A"),
                        "timestamp": result.get("timestamp", "N/A")
                    }
                    log_file.write(json.dumps(log_data) + '\n')
                    send_to_splunk(log_data)
                logging.info(f'Data for query \'{query}\' saved to {log_file_path}')
            except shodan.APIError as e:
                logging.error(f'Shodan API Error for query "{query}": {e}')
            except Exception as e:
                logging.error(f'Error for query "{query}": {e}')

if __name__ == '__main__':
    try:
        while True:
            logging.info('Starting new data fetch cycle')
            fetch_and_save_shodan_data()
            logging.info('Data fetch cycle complete, sleeping for 1 hour')
            time.sleep(3600)  # Wait for 1 hour before the next fetch
    except Exception as e:
        logging.critical(f'Critical error in main loop: {e}', exc_info=True)
    finally:
        logging.info('Shodan data fetch script has stopped')
