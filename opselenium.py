from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import datetime

todayDate = datetime.datetime.now().strftime("%m/%d/%y");
siteID = [
'S********',
'S********',
'S********',
'S********',
'S********',
'S********',
'S********',
'S********',
'S********',
'S********'
]

# set browser option to run 'headless'
options = webdriver.ChromeOptions()
options.add_argument('--headless')

# Specify Chrome as our browser of choice (chromedriver.exe must 
# be in the script directory or on the system path.)
browser = webdriver.Chrome(options=options)

browser.get('INSERT OPS URL')
old_window_handle = browser.current_window_handle

# log ourselves in!
user_elem = browser.find_element_by_name('j_username')
pass_elem = browser.find_element_by_name('j_password')

user_elem.send_keys('INSERT USER' + Keys.TAB)
pass_elem.send_keys('INSERT PASS' + Keys.RETURN)

for sindex in siteID:
    
    browser.execute_script("window.open('INSERT OPS URL')")

    new_window_handle = [window for window in browser.window_handles if window != old_window_handle][0]
    
    if browser.current_window_handle != old_window_handle:
        browser.switch_to.window(old_window_handle)
    else:
        browser.switch_to.window(new_window_handle)
    

    
    # next page
    
    idSearch_elem = browser.find_element_by_name('idSearch')
    idSearch_elem.send_keys(sindex + Keys.RETURN)
    
    commType_elem = browser.find_element_by_xpath('//*[@id="siteInfo"]/div/div[2]/div[2]/div[2]/div/span[2]').text

    deviceInfo_elem = browser.find_element_by_xpath('//*[@id="siteDetails"]/div[4]/div[6]/div[2]/div[3]/span[2]').text
    if commType_elem == 'SSC':
        lastCheckin_elem = browser.find_element_by_id('lastCheckin').text
        lastAuth_elem = browser.find_element_by_class_name('siteData').text

        if '(yesterday)' in deviceInfo_elem: 
            print('Site reported data yesterday, may be online. Checking "Last Checkin" time...')
            
            if todayDate in lastCheckin_elem:
                    print('Site %s is online, check for data.' % sindex)
            else:
                print('Site %s is not online.' % sindex)
            
        else: 
            print('Site has not reported data recently and may be offline. Checking "Last Checkin" time...')
            if commType_elem == 'SSC':
                if todayDate in lastCheckin_elem:
                    if todayDate in lastAuth_elem:
                        print('The lead device that the site is checking in. Check Orbit for an OOS flag or a connection issue.')
                    else: 
                        print('The lead device is checking in but has not been authorized.')
                else:
                    print('Site %s is not online.' % sindex)
            else:
                print('Communication type does not support "Checkin" time checks. Check if site %s is online manually.' % sindex)
    else:
        print('Communication type does not support "Checkin" time checks. Check if site %s is online manually.' % sindex)

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