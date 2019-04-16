#!python.exe

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from colors import *
from colorama import init
import sys
import datetime
import secure
import re

# initialize colorama adaptive CLI coloring
init()

todayDate = datetime.datetime.now().strftime("%m/%d/%y")

# figure out what kind and how much input we're dealing with
sid_list_input = []
siteID = []
sid_pattern = re.compile("(S[0-9]{8}|8[0-9]{7}|[0-1]00[0-9]{5}|[0-9]{5})")
if hasattr(secure, 'SID_LIST'): # if the SID_LIST constant is set...     
    print("Default Site ID list is set, ignoring all other input.")
    siteID = secure.SID_LIST
elif len(sys.argv) > 0: # if there are > 1 arguments....
    if ".txt" in str(sys.argv[1]) or ".csv" in str(sys.argv[1]):
    # if the argument is a txt or csv file...
        with open(sys.argv[1], 'r') as sid_list:
            for count, line in enumerate(sid_list):
                sid_list_input.append(line.rstrip('\n')
            sid_list.close()
        siteID = sid_list_input    
    else:
        siteID = [str(sys.argv[1])]
else:
    print("No Site IDs given as input. Provide input (STDIN | .txt | .csv) and try again.")
    sys.exit()
    
# ensure all input site IDs are valid
idx = 0
for id in siteID:
    if not sid_pattern.match(str(sys.argv[1])): 
        print("%s is not a valid Site ID, deleting it from input." % id)
        siteID.pop(idx)
    idx += 1                                  

if len(siteID) == 0:
    print("No Site IDs given as input. Provide input (STDIN | .txt | .csv) and try again.")
    sys.exit()

# set browser option to run 'headless'
# comment out to run in GUI mode
options = webdriver.ChromeOptions()
options.add_argument('--headless')
options.add_argument('--log-level=2')
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
    

    
    # next page
    
    idSearch_elem = browser.find_element_by_name("idSearch")
    idSearch_elem.send_keys(sindex + Keys.RETURN)
    
    # Determing communication protocol
    commType_elem = browser.find_element_by_xpath('//*[@id="siteInfo"]/div/div[2]/div[2]/div[2]/div/span[2]').text

    # check whether we're using SSC
    if commType_elem == 'SSC':
        # variables are last data recvd, last checkin, and last authenticated checkin respectively.
        deviceInfo_elem = browser.find_element_by_xpath('//*[@id="siteDetails"]/div[4]/div[6]/div[2]/div[3]/span[2]').text
        lastCheckin_elem = browser.find_element_by_id('lastCheckin').text
        lastAuth_elem = browser.find_element_by_xpath('//*[@id="siteInfo"]/div/div[2]/div[2]/div[3]/div[3]/span[2]').text

        if '(yesterday)' in deviceInfo_elem: 
            print('Site %s reported data yesterday, may be online. Checking "Last Checkin" time...' % sindex)
            
            if todayDate in lastCheckin_elem:
                sys.stdout.write(GREEN)
                print('** STATUS **: Site %s is online, check for data.' % sindex)
                sys.stdout.write(RESET)
            else:
                sys.stdout.write(RED)
                print('** STATUS **: Site %s is not online.' % sindex)
                sys.stdout.write(RESET)
            
        else: 
            print('Site %s has not reported data recently and may be offline. Checking "Last Checkin" time...' % sindex)
            if commType_elem == 'SSC':
                if todayDate in lastCheckin_elem:
                    if todayDate in lastAuth_elem:
                        sys.stdout.write(BOLD + REVERSE)
                        print('** STATUS **:')
                        sys.stdout.write(RESET)
                        sys.stdout.write(GREEN)
                        print('Lead device is online.')
                        sys.stdout.write(BOLD + RED)
                        print('No data is reporting.')
                        sys.stdout.write(RESET)
                        print('Check for an OOS flag or HW issue with the Orbit.')
                    else: 
                        print('The lead device is checking in but has not been authorized at site %s.' % sindex)
                else:
                    sys.stdout.write(RED)
                    print('** STATUS **: Site %s is not online.' % sindex)
                    sys.stdout.write(RESET)
            else:
                sys.stdout.write(CYAN)
                print('Communication type does not support "Checkin" time checks. Check if site %s is online manually.' % sindex)
                sys.stdout.write(RESET)
    else:
        sys.stdout.write(CYAN)
        print('Communication type does not support "Checkin" time checks. Check if site %s is online manually.' % sindex)
        sys.stdout.write(RESET)

    if browser.current_window_handle == old_window_handle:    
        browser.close()
        browser.switch_to.window(new_window_handle)
        old_window_handle = new_window_handle
    else: 
        browser.switch_to.window(old_window_handle)
        browser.close()
        browser.switch_to.window(new_window_handle)
        old_window_handle = new_window_handle

browser.quit()
sys.exit()
