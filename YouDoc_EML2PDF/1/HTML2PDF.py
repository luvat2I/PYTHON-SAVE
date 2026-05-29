'''
HTML2PDF.py
=============

	Convert all input HTM files to PDF
		- generated file will have same filename, just .mhtml rather than .HTM
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
  File				  HTML files to convert

optional arguments:
  -h, --help			show this help message and exit
  --chromedriver CHROMEDRIVER
						Path to chromedriver
  --threads THREADS	 Number of threads to use
  --verbosity VERBOSITY
						Set the logging verbosity level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

	Author:
		Michael Tonkin : mike.tonkin@april.com

	Copyright April Santé Prévoyance: mike.tonkin@april.com
'''
#######################################################
#
# Exit codes (should have minimum ERROR log message)
#
# 0 - all OK
# 1 - OS not supported
# 2 - Chromedriver not found
#
import os
import pdfkit
import sys
import re
import argparse
import configparser
import logging
import logging.handlers
from datetime import datetime, timedelta
from multiprocessing import Process, Queue




current_time_debut = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
current_time_traitement = datetime.now().strftime("%Y%m%d")
def log_console(level,log_text):
	current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
	print(f"{current_time} > {level} > {log_text}")

	

# Lecture du fichier de configuration
config = configparser.ConfigParser()


try:
	config.read('config.ini')
	if not config.sections():  # Vérifie si le fichier ini est vide
		raise FileNotFoundError("Le fichier de configuration 'config.ini' est vide.")
except Exception as e:
	log_console("ERROR",f"Probleme de traitement du fichier 'config.ini': {e}")
	sys.exit(1)  # ferme lapp

try:
	log_folder = config['logging']['log_folder']
	wkhtmltox_folder = config['param']['wkhtmltox_folder']
except Exception as e:
	log_console("ERROR",f"Probleme de traitement du fichier 'config.ini': {e}")
	sys.exit(1)  # ferme lapp
	
	
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
	options.add_argument('--verbose')
	options.add_argument('--log-path=chromedriver.log')
	options.add_argument('--disable-gpu')
	options.add_argument('--no-sandbox')
	options.add_argument('--disable-extensions')
	options.add_argument('--disable-infobars')
	options.add_argument('--disable-dev-shm-usage')
	options.add_argument('--user-agent=Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; Trident/6.0)')
	return options


def eml_to_pdf(queue):
	output_OK = f"{log_folder}OK_{current_time_traitement}.txt"
	output_KO = f"{log_folder}KO_{current_time_traitement}.txt"
	
	
	global nombre_ligne
	# Cycle through all files on the same chrome driver.
	# The four threads each read first come, first served until the queue is empty then the thread quits
	while True:
		file = queue.get()
		if file is None:
			break
		print(f"{file}")
		if not re.search(r'\.HTM?$', file, re.IGNORECASE):
			with open(output_KO, 'a', encoding='utf-8') as f:
				f.write(f"{file};Not a .HTM file: {file}\n")
			logging.warning(f"Not a .HTM file: {file}")
			continue
		
		abs_in = os.path.abspath(file)
		if not os.path.exists(f"{abs_in}"):
			with open(output_KO, 'a', encoding='utf-8') as f:
				f.write(f"{file};Nonexistent file {abs_in}\n")
			logging.error(f"Nonexistent file {abs_in}")
			continue
			
		abs_out = re.sub(r"(.*).HTM", r"\1." + "PDF", abs_in, flags=re.IGNORECASE)
		if os.path.exists(abs_out):
			logging.warning(f"Output file exists. Skipping {abs_in} due to {abs_out}")
			with open(output_KO, 'a', encoding='utf-8') as f:
				f.write(f"{file};Output file exists. Skipping {abs_in} due to {abs_out}\n")
			continue

		try:
			logging.info(f"traite {abs_out}")
			eml_file = abs_in
			pdf_file = abs_out
			config = pdfkit.configuration(wkhtmltopdf=wkhtmltox_folder)
			pdfkit.from_file(eml_file, pdf_file, configuration=config)
			
			with open(output_OK, 'a') as f:
				 f.write(f"{file}\n")

		except Exception as e:
			with open(output_KO, 'a') as f:
				f.write(f"Error processing {abs_in}: {e}")
			logging.error(f"Error processing {abs_in}: {e}")


if __name__ == "__main__":
	
	parser = argparse.ArgumentParser(description="Convert HTML files to MHTML format.")
	parser.add_argument('--threads', type=int, default=4, help='Number of threads to use')
	parser.add_argument('--verbosity', type=str, default='WARNING', help='Set the logging verbosity level (DEBUG, INFO, WARNING, ERROR, CRITICAL)')
	parser.add_argument('--ext', type=str, default='EML', help='Set the output file extension (ex: MHT/mht/mhtml/eml - this does not change the file contents)')
	parser.add_argument('--infile', type=str, default=None, help='Input file containing files to convert, one per line')
	parser.add_argument('files', metavar='File', type=str, nargs='*', help='HTML files to convert')

	# Parse kwnown args 
	args, unknown = parser.parse_known_args()
	if unknown:
		args.files = unknown

	# Set up logging based on verbosity level
	setup_logging(args.verbosity)

	logging.debug(f"Threads: {args.threads}")
	logging.debug(f"Verbosity: {args.verbosity}")
	logging.debug(f"Ext: {args.ext}")
	logging.debug(f"Infile: {args.infile}")
	logging.debug(f"Files: {args.files}")

	fileQ = Queue()

	if (args.infile is not None ):
		log_console("DEBUG",f"lecture du fichier {args.infile}")
		with open(args.infile) as inf:
			for line in inf:
				file=line.strip()
				logging.debug(f"Adding file '{file}' to queue")
				fileQ.put(file)

	for file in args.files:
		logging.debug(f"Adding file '{file}' to queue")
		fileQ.put(file)

	processes = []
	for i in range(args.threads):
		p = Process(target=eml_to_pdf, args=(fileQ,))
		p.start()
		processes.append(p)

	# Add sentinel values to signal workers to exit - one per thread
	for _ in range(args.threads):
		fileQ.put(None)

	# Wait for all processes to complete
	for p in processes:
		p.join()

current_time_fin = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

print(f"{current_time_debut} > {current_time_fin}")