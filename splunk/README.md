# Shodan Data Fetcher with Splunk Integration

This Python script fetches data from the Shodan API based on specified queries and sends the results to Splunk via the HTTP Event Collector (HEC). It also logs the results to a local file with daily rotation.

## Features

- **Shodan Data Fetching**: Executes predefined Shodan search queries for specified IP ranges, ports, and vulnerabilities.
- **Splunk Integration**: Sends Shodan search results to Splunk using the HTTP Event Collector (HEC).
- **Local Logging**: Logs data to a local file with daily rotation to manage disk space.
- **Error Handling**: Includes retry mechanisms and detailed error logging.
- **Graceful Shutdown**: Handles shutdown signals for a graceful exit.

## Prerequisites

- Python 3.x
- Required Python modules: `shodan`, `requests`, `retrying`
- Splunk HTTP Event Collector (HEC) enabled and configured

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/yourusername/shodan-fetcher-splunk.git
   cd shodan-fetcher-splunk
