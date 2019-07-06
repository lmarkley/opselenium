from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from colors import *
from colorama import init
import sys
import datetime
import secure
import os
import io
import xlrd
import csv

# convert from xlsx to csv, does what it says on the tin
def convert_to_csv(xlsx_file):
	book = xlrd.open_workbook(xlsx_file)
	filename = xlsx_file.split('.xlsx')[0].lstrip('../')
	sheet = book.sheet_by_name(filename)
	csv_name = 'temp.csv' # we will just overwrite a temp file each time
	output_csv = open(csv_name, 'w+')
	writer = csv.writer(output_csv, quoting=csv.QUOTE_ALL)
	for r in range(sheet.nrows):
		writer.writerow(sheet.row_values(r))
	
	output_csv.close();
	return 'temp.csv'
# write to output file in preferred format
def write_to_output(idx):
	reportFile.write(status[idx] + ', ' + siteID[idx] + ', ' + tid_list_input[idx] + ', ' + owner_list_input[idx] + ', ' + nsd_list_input[idx] + ', ' + notes[idx] + '\n')

# check if an element of a page exists and deal with that
def xpath_exists(driver, xpath):
	try:
		driver.find_element_by_xpath(xpath)
	except NoSuchElementException:
		return False
	return True

# initialize colorama adaptive CLI coloring
init()

todayDate = datetime.datetime.now().strftime("%m/%d/%y")

# statuses
siteOnlineStatus  = 'ONLINE'
siteOfflineStatus = 'OFFLINE'
leadOnlineStatus  = 'LEAD ONLINE'
notAuthedStatus   = 'NOT AUTHED'
noSupportStatus   = 'UNSUPPORTED TYPE'
importStatus	  = 'IMPORT/ACTIVATE'

# notes
siteOnlineNotes   = 'Check for data'
siteOfflineNotes  = 'Begin troubleshooting as normal'
leadOnlineNotes   = 'Check for Orbit OOS/HW/Connection fault'
notAuthedNotes    = 'ST600 needs to be authorized'
noSupportNotes    = 'Communication type is unsupported check manually.'
importNotes 	  = 'Site is closed; is not imported; or is deactivated.'

# figure out what kind and how much input we're dealing with
sid_list_input = []
tid_list_input = []
owner_list_input = []
nsd_list_input = []
siteID = []
status = []
notes = []
list_index = 0
reportFile = None
inputFile = None

if hasattr(secure, 'SID_LIST'): # if the SID_LIST constant is set...     
	print("Default Site ID list is set, ignoring all other input.")
	siteID = secure.SID_LIST
elif len(sys.argv) > 0: # if there are > 1 arguments....
	inputFile = str(sys.argv[1])
	output_file = str(sys.argv[1]).split('.')[0] + '_infoOut.csv'
	reportFile = io.open(output_file,'a+', encoding='utf-8')
	reportFile.write('Status,Site ID,TaskID,Owner,NSD,Notes' + '\n')
	if ".txt" in inputFile or ".csv" in inputFile or ".xlsx" in inputFile:
	# if the arg is xlsx, then convert
		if ".xlsx" in inputFile:
			inputFile = convert_to_csv(str(sys.argv[1]))
	# if the argument is a txt or csv file...
		with io.open(inputFile, 'r', encoding='utf-8') as sid_list:
			for count, line in enumerate(sid_list):
				input_data = line.split(',')
				sid_list_input.append(input_data[0].rstrip('\ue006').strip('"'))
				tid_list_input.append(input_data[1])
				owner_list_input.append(input_data[2])
				nsd_list_input.append(input_data[3].rstrip('\n'))
		siteID = sid_list_input
	else:
		siteID = [inputFile]

else:
	print("No Site IDs given as input. Provide input (STDIN | .txt | .csv) and try again.")
	sys.exit()

# set browser option to run 'headless'
# comment out to run in GUI mode
options = webdriver.ChromeOptions()
options.add_argument('--headless')
options.add_argument('--log-level=1')
options.add_argument('--no-cache')

# Specify Chrome as our browser of choice (chromedriver.exe must 
# be in the script directory or on the system path.)
browser = webdriver.Chrome(options=options)
browser.get('https://operationsportal.shoppertrak.com')
old_window_handle = browser.current_window_handle

# log ourselves in!
user_elem = browser.find_element_by_name('j_username')
pass_elem = browser.find_element_by_name('j_password')

user_elem.send_keys(secure.USER + Keys.TAB)
pass_elem.send_keys(secure.PASS + Keys.RETURN)

for sindex in siteID:
	browser.execute_script("window.open('https://operationsportal.shoppertrak.com')")

	new_window_handle = [window for window in browser.window_handles if window != old_window_handle][0]
	
	if browser.current_window_handle != old_window_handle:
		browser.switch_to.window(old_window_handle)
	else:
		browser.switch_to.window(new_window_handle)

	idSearch_elem = browser.find_element_by_id('idSearch')
	idSearch_elem.send_keys(sindex + Keys.RETURN)

	if ( xpath_exists(browser,'/html/body/h1') ):
		print('Site is not in Ops Portal')
		status.append(importStatus)
		notes.append(importNotes)
		write_to_output(list_index)
		continue

	# Determing communication protocol
	try:
		commType_elem = browser.find_element_by_xpath('//*[@id="siteInfo"]/div/div[2]/div[2]/div[2]/div/span[2]').text
	except NoSuchElementException:
		continue

	# check whether we're using SSC
	if commType_elem == 'SSC':
		# variables are last data recvd, last checkin, and last authenticated checkin respectively.

		deviceType_elem = browser.find_element_by_class_name('fullDeviceTypeTitle').text

		if ('Orbit ES' in deviceType_elem ):
			deviceInfo_elem = browser.find_element_by_xpath('//*[@id="siteDetails"]/div[4]/div[5]/div[2]/div[3]/span[2]').text
		else:
			try:
				deviceInfo_elem = browser.find_element_by_class_name('deviceInfoData').text
			except NoSuchElementException:
				deviceInfo_elem = browser.find_element_by_xpath('//*[@id="siteDetails"]/div[4]/div[6]/div[2]/div[3]/span[2]').text
			
		lastCheckin_elem = browser.find_element_by_id('lastCheckin').text
		lastAuth_elem = browser.find_element_by_xpath('//*[@id="siteInfo"]/div/div[2]/div[2]/div[3]/div[3]/span[2]').text

		if '(yesterday)' in deviceInfo_elem: 
			print('Site %s reported data yesterday, may be online. Checking "Last Checkin" time...' % sindex)
			
			if todayDate in lastCheckin_elem: #online
				sys.stdout.write(BOLD + REVERSE)
				print('** STATUS **:')
				sys.stdout.write(RESET)
				sys.stdout.write(GREEN)
				print('Site %s is online, check for data.' % sindex)
				sys.stdout.write(RESET)
				status.append(siteOnlineStatus)
				notes.append(siteOnlineNotes)
			else: #offline
				sys.stdout.write(BOLD + REVERSE)
				print('** STATUS **:')
				sys.stdout.write(RESET)
				sys.stdout.write(RED)
				print('Site %s is not online.' % sindex)
				sys.stdout.write(RESET)
				status.append(siteOfflineStatus)
				notes.append(siteOfflineNotes)
			
		else: 
			print('Site %s has not reported data recently and may be offline. Checking "Last Checkin" time...' % sindex)
			if commType_elem == 'SSC': # SSC only
				if todayDate in lastCheckin_elem:
					if todayDate in lastAuth_elem: #lead online
						sys.stdout.write(BOLD + REVERSE)
						print('** STATUS **:')
						sys.stdout.write(RESET)
						sys.stdout.write(BOLD + RED)
						print('Lead device at %s is online. No data is reporting. Check for an OOS flag or HW issue with the Orbit.' % sindex)
						sys.stdout.write(RESET)
						status.append(leadOnlineStatus)
						notes.append(leadOnlineNotes)

					else: #notAuthed
						print('The lead device is checking in but has not been authorized at site %s.' % sindex)
						status.append(notAuthedStatus)
						notes.append(notAuthedNotes)

				else: #offline 
					sys.stdout.write(BOLD + REVERSE)
					print('** STATUS **:')
					sys.stdout.write(RESET)
					sys.stdout.write(RED)
					print('Site %s is not online.' % sindex)
					sys.stdout.write(RESET)
					status.append(siteOfflineStatus)
					notes.append(siteOfflineNotes)

			else: #noSupport
				sys.stdout.write(CYAN)
				print('Communication type does not support "Checkin" time checks. Check if site %s is online manually.' % sindex)
				sys.stdout.write(RESET)
				status.append(noSupportStatus)
				notes.append(noSupportNotes)
				
	else: #noSupport
		sys.stdout.write(CYAN)
		print('Communication type does not support "Checkin" time checks. Check if site %s is online manually.' % sindex)
		sys.stdout.write(RESET)
		status.append(noSupportStatus)
		notes.append(noSupportNotes) 

	write_to_output(list_index) # use `write_to_output`function after each iteration
	list_index += 1

	if browser.current_window_handle == old_window_handle:    
		browser.close()
		browser.switch_to.window(new_window_handle)
		old_window_handle = new_window_handle
	else: 
		browser.switch_to.window(old_window_handle)
		browser.close()
		browser.switch_to.window(new_window_handle)
		old_window_handle = new_window_handle

if ( reportFile not None ):
	reportFile.close()
		
browser.quit()

sys.exit()
