import shodan
import json
import time
import os
import logging
import signal
import sys
from retrying import retry

# Load configuration from config.json
config_path = 'config.json'
if not os.path.isfile(config_path):
    raise FileNotFoundError(f"Configuration file not found: {config_path}")

with open(config_path) as config_file:
    config = json.load(config_file)

required_keys = {'log_folder', 'api_key', 'queries'}
if not required_keys.issubset(config.keys()):
    raise ValueError(f"Configuration file must contain keys: {required_keys}")

# Shodan API key read function
SHODAN_API_KEY = config['api_key']
if not SHODAN_API_KEY:
    raise ValueError("Shodan API key must be set in the api_key field in the configuration file!")

api = shodan.Shodan(SHODAN_API_KEY)

log_folder = config['log_folder']
os.makedirs(log_folder, exist_ok=True)
log_file_path = os.path.join(log_folder, 'shodan_data.log')

# Configure logging
log_file = os.path.join(log_folder, 'shodan_script.log')
logging.basicConfig(
    filename=log_file,
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
logging.getLogger().addHandler(console_handler)

logging.info('Starting Shodan data fetch script')

log_run_count = 0
max_log_runs = 6

def signal_handler(sig, frame):
    logging.info('Received shutdown signal, exiting...')
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

@retry(stop_max_attempt_number=3, wait_fixed=2000)
def fetch_shodan_data(query):
    return api.search(query)

def fetch_and_save_shodan_data():
    queries = config['queries']
    with open(log_file_path, 'a') as log_file:
        for query in queries:
            logging.info(f'Executing query: {query}')
            try:
                results = fetch_shodan_data(query)
                logging.info(f'Query successful: {query}, found {len(results["matches"])} results')
                for result in results['matches']:
                    log_file.write(json.dumps(result) + '\n')
                logging.info(f'Data for query \'{query}\' saved to {log_file_path}')
            except shodan.APIError as e:
                logging.error(f'Shodan API Error for query "{query}": {e}')
            except Exception as e:
                logging.error(f'Error for query "{query}": {e}')

def rotate_log_file():
    global log_run_count
    log_run_count += 1
    if log_run_count >= max_log_runs:
        with open(log_file_path, 'w') as log_file:
            log_file.write('')
        log_run_count = 0
        logging.info('Log file rotated after maximum runs')

if __name__ == '__main__':
    try:
        while True:
            logging.info('Starting new data fetch cycle')
            fetch_and_save_shodan_data()
            logging.info('Data fetch cycle complete, sleeping for 1 hour')
            rotate_log_file()
            time.sleep(3600)  # Wait for 1 hour before the next fetch
    except Exception as e:
        logging.critical(f'Critical error in main loop: {e}', exc_info=True)
    finally:
        logging.info('Shodan data fetch script has stopped')
