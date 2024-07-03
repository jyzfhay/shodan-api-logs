# Shodan Data Fetch Script

This script fetches data from the Shodan API based on specified queries and saves the results to a log file. It is designed to run continuously, appending new data to the log file and rotating the log file every six runs to manage disk space usage.

## Features

- **Shodan Data Fetching**: Executes predefined Shodan search queries for open ports and vulnerabilities.
- **Configuration**: Uses a `config.json` file to specify Shodan queries, log folder, and API key.
- **Logging**: Comprehensive logging to a dedicated log file (`shodan_script.log`) and console output for real-time monitoring.
- **Error Handling**: Includes retry mechanisms and detailed error logging.
- **Log Management**: Rotates the log file every six runs to prevent excessive disk space usage.
- **Graceful Shutdown**: Handles `SIGINT` and `SIGTERM` signals for a graceful shutdown.

## Prerequisites

- Python 3.x
- Shodan Python module
- Retrying module

Install the required Python modules using pip:
```bash
pip install shodan retrying