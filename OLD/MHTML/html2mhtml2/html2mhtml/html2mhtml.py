'''
html2mhtml.py
=============

    Convert all input html files to mhtlm
        - generated file will have same filename, just .mhtml rather than .html
        - runs in threads to split the load (each thread runs one chrome)

    Requirements:
        - selenium
        - chromedriver

    Possible improvements: 
        - smarter wait-for-document (here just wait for body to load) in chromedriver
        - other file extensions than ".html"

    Usage:

usage: html2mhtml.py [-h] [--chromedriver CHROMEDRIVER] [--threads THREADS] [--verbosity VERBOSITY] File [File ...]

Convert HTML files to MHTML format.

positional arguments:
  File                  HTML files to convert

optional arguments:
  -h, --help            show this help message and exit
  --chromedriver CHROMEDRIVER
                        Path to chromedriver
  --threads THREADS     Number of threads to use
  --verbosity VERBOSITY
                        Set the logging verbosity level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Author:
        Michael Tonkin : mike.tonkin@april.com

    Copyright April Santé Prévoyance: mike.tonkin@april.com
'''

import os
import sys
import re
import argparse
import logging
from multiprocessing import Process, Queue
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Function to convert Cygwin paths to Windows paths
def cygwin_to_windows(cyg_path):
    return cyg_path.replace("/cygdrive/c/", "C:\\").replace("/", "\\")

# Function to set up logging
def setup_logging(verbosity):
    log_levels = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }
    level = log_levels.get(verbosity.upper(), logging.INFO)
    logging.basicConfig(level=level, format='%(asctime)s - %(levelname)s - %(message)s')

def configure_chrome_options():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-infobars')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--user-agent=Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; Trident/6.0)')
    return options

def save_pages_as_mhtml(queue, chromedriver_path):
    # Set Chrome options
    options = configure_chrome_options()

    # Set up the Chrome service and driver
    service = Service(chromedriver_path)
    driver = webdriver.Chrome(service=service, options=options)

    # Cycle through all files on the same chrome driver.
    # The four threads each read first come, first served until the queue is empty then the thread quits
    while True:
        file = queue.get()
        if file is None:
            break
        if not file.endswith(".html"):
            logging.warning(f"Not a .html file: {file}")
            continue

        abs_in = os.path.abspath(file)
        if not os.path.exists(abs_in):
            logging.error(f"Nonexistent file {abs_in}")
            continue

        abs_out = re.sub(r"(.*).html", r"\1.mhtml", abs_in, flags=re.IGNORECASE)
        if os.path.exists(abs_out):
            logging.warning(f"Output file exists. Skipping {abs_in} due to {abs_out}")
            continue

        try:
            if sys.platform == 'cygwin':
                file_url = 'file:///' + cygwin_to_windows(abs_in)
            else:
                file_url = 'file:///' + abs_in

            logging.info(f"Opening {file_url}")
            driver.get(file_url)

            WebDriverWait(driver, 10).until(
                    lambda d: d.execute_script("return document.readyState") == "complete"
                    )
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

            mhtml = driver.execute_cdp_cmd("Page.captureSnapshot", {"format": "mhtml"})

            with open(abs_out, "wb") as mhtml_file:
                mhtml_file.write(mhtml['data'].encode('utf-8'))
            logging.info(f"MHTML saved to: {abs_out}")

        except Exception as e:
            logging.error(f"Error processing {abs_in}: {e}")
    
    # clean up 
    driver.quit()

if __name__ == "__main__":
    # set up default paths if not given on command line
    platform=sys.platform.lower()
    defaultchromedriver ={
                "linux": "/usr/bin/chromedriver",
                "aix": "/usr/bin/chromedriver",
                "cygwin" : "/cygdrive/c/selenium/chromedriver/chromedriver.exe",
                "msys" : "c:/selenium/chromedriver/chromedriver.exe",
                "win32": "c:/selenium/chromedriver/chromedriver.exe"
                }.get(platform,None)

    if defaultchromedriver is None:
        print(f"Error: No support for your system (sys.platform={sys.platform})")
        sys.exit(1)  # Exit the script with a non-zero status code

    parser = argparse.ArgumentParser(description="Convert HTML files to MHTML format.")
    parser.add_argument('--chromedriver', type=str, default=defaultchromedriver, help='Path to chromedriver')
    parser.add_argument('--threads', type=int, default=4, help='Number of threads to use')
    parser.add_argument('--verbosity', type=str, default='WARNING', help='Set the logging verbosity level (DEBUG, INFO, WARNING, ERROR, CRITICAL)')
    parser.add_argument('files', metavar='File', type=str, nargs='+', help='HTML files to convert')

    # Parse kwnown args 
    args, unknown = parser.parse_known_args()
    if unknown:
        args.files = unknown

    # Set up logging based on verbosity level
    setup_logging(args.verbosity)

    logging.debug(f"Chromedriver: {args.chromedriver}")
    logging.debug(f"Threads: {args.threads}")
    logging.debug(f"Verbosity: {args.verbosity}")
    logging.debug(f"Files: {args.files}")

    fileQ = Queue()

    for file in args.files:
        fileQ.put(file)

    processes = []
    for i in range(args.threads):
        p = Process(target=save_pages_as_mhtml, args=(fileQ, args.chromedriver))
        p.start()
        processes.append(p)

    # Add sentinel values to signal workers to exit - one per thread
    for _ in range(args.threads):
        fileQ.put(None)

    # Wait for all processes to complete
    for p in processes:
        p.join()

