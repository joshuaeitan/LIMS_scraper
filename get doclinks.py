#from PyQt5.QtWebEngine import *
from PyQt5.QtCore import QEventLoop
import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWebEngineWidgets import QWebEngineView
# selenium is a broswer emulator - use it to click tabbed pane and activate it 
from selenium import webdriver
import re
import time
from multiprocessing import Process
import requests
#17361 documents from council periods 20-22 - 507 mb of text

#http://stackoverflow.com/questions/41473391/how-to-grab-data-from-the-comment-tab-from-an-online-nyt-article-using-python
# need to get list of URLs - legislation numbers - can use API
# then open browser window and pull document urls
# then download/convert docs
#test criteria
# Let's get every single legislation ID first, then run through them all (in parallel) and get all docLinks
criteria = {'CommitteeCommentsId': 0, 'Introducer': 0, 'CategoryId': 0, 'CommitteeId': 0, 'LegislationStatus': 0, 'CoSponsor': 0, 'CouncilPeriod': 0, 'StartDate': '', 'EndDate': ''}
base = 'http://lims.dccouncil.us'
# 37,847 bills (as of 4/12)
urls = []
introLinks = []
for i in range(38):
    r = requests.post(base+'/api/v1/Legislation/AdvancedSearch/1000/'+str(i),json=criteria)
    bills = r.json()
    # get legislation numbers:
    for bill in bills:
        urls.append(base+'/Legislation/'+bill['LegislationNumber'])
        introLinks.append(bill['DocumentUrl'])

with open('docLinks11','w') as f:
    f.write('\n'.join(introLinks))
    
driver1 = webdriver.firefox.webdriver.WebDriver(executable_path='/Users/joshuakaplan/geckodriver')
driver2 = webdriver.firefox.webdriver.WebDriver(executable_path='/Users/joshuakaplan/geckodriver')
driver3 = webdriver.firefox.webdriver.WebDriver(executable_path='/Users/joshuakaplan/geckodriver')
driver4 = webdriver.firefox.webdriver.WebDriver(executable_path='/Users/joshuakaplan/geckodriver')
driver5 = webdriver.firefox.webdriver.WebDriver(executable_path='/Users/joshuakaplan/geckodriver')
driver6 = webdriver.firefox.webdriver.WebDriver(executable_path='/Users/joshuakaplan/geckodriver')
driver7 = webdriver.firefox.webdriver.WebDriver(executable_path='/Users/joshuakaplan/geckodriver')
driver8 = webdriver.firefox.webdriver.WebDriver(executable_path='/Users/joshuakaplan/geckodriver')
driver9 = webdriver.firefox.webdriver.WebDriver(executable_path='/Users/joshuakaplan/geckodriver')
driver10 = webdriver.firefox.webdriver.WebDriver(executable_path='/Users/joshuakaplan/geckodriver')

docTerm = re.compile('http:\/\/lims..*?pdf')

docLinks1 = []
docLinks2 = []
docLinks3 = []
docLinks4 = []
docLinks5 = []
docLinks6 = []
docLinks7 = []
docLinks8 = []
docLinks9 = []
docLinks10 = []

#0-3800
# through 200 4/13 @ 11am
# 300 @2.15 pm
# 400 @2.35 pm
#1400 7 am 4/14
# 1800 11am 4/14
#2300 6 pm 4/14  
def loop_a():
    i=0
    for url in urls[2300:3800]:
        print(i)
        i+=1
        try:
            driver1.get(url)
        except:
            continue
        # waiting for the page is fully loaded
        time.sleep(5)
        try: 
            link = driver1.find_element_by_partial_link_text('Bill History').click()
            page  = driver1.page_source
        except:
            page  = driver1.page_source
        try:
            history = page.split('<div id="billHistory">')[1].split('<div class="tab-pane" id="thirds3322">')[0]
            docLinks1.append(re.findall(docTerm,history))
        except:
            continue
    with open('docLinks1.txt','w') as f:
        f.write('\n'.join([item for sublist in docLinks1 for item in sublist]))

#3800
def loop_b():
    for url in urls[6101:7600]:
        driver2.get(url)
        # waiting for the page is fully loaded
        time.sleep(5)
        try: 
            link = driver2.find_element_by_partial_link_text('Bill History').click()
            page  = driver2.page_source
        except:
            page  = driver2.page_source
        try:
            history = page.split('<div id="billHistory">')[1].split('<div class="tab-pane" id="thirds3322">')[0]
            docLinks2.append(re.findall(docTerm,history))
        except:
            continue
    with open('docLinks2.txt','w') as f:
        f.write('\n'.join([item for sublist in docLinks2 for item in sublist]))

#7600
def loop_c():
    for url in urls[9901:11400]:
        driver3.get(url)
        # waiting for the page is fully loaded
        time.sleep(5)
        try: 
            link = driver3.find_element_by_partial_link_text('Bill History').click()
            page  = driver3.page_source
        except:
            page  = driver3.page_source
        try:
            history = page.split('<div id="billHistory">')[1].split('<div class="tab-pane" id="thirds3322">')[0]
            docLinks3.append(re.findall(docTerm,history))
        except:
            continue
    with open('docLinks3.txt','w') as f:
        f.write('\n'.join([item for sublist in docLinks3 for item in sublist]))

#11400
def loop_d():
    for url in urls[13701:15200]:
        driver4.get(url)
        # waiting for the page is fully loaded
        time.sleep(5)
        try: 
            link = driver4.find_element_by_partial_link_text('Bill History').click()
            page  = driver4.page_source
        except:
            page  = driver4.page_source
        try:
            history = page.split('<div id="billHistory">')[1].split('<div class="tab-pane" id="thirds3322">')[0]
            docLinks4.append(re.findall(docTerm,history))
        except:
            continue
    with open('docLinks4.txt','w') as f:
        f.write('\n'.join([item for sublist in docLinks4 for item in sublist]))

#15200
def loop_e():
    for url in urls[17501:19000]:
        driver5.get(url)
        # waiting for the page is fully loaded
        time.sleep(5)
        try: 
            link = driver5.find_element_by_partial_link_text('Bill History').click()
            page  = driver5.page_source
        except:
            page  = driver5.page_source
        try:
            history = page.split('<div id="billHistory">')[1].split('<div class="tab-pane" id="thirds3322">')[0]
            docLinks5.append(re.findall(docTerm,history))
        except:
            continue
    with open('docLinks5.txt','w') as f:
        f.write('\n'.join([item for sublist in docLinks5 for item in sublist]))

#19000
def loop_f():
    for url in urls[21301:22800]:
        driver6.get(url)
        # waiting for the page is fully loaded
        time.sleep(5)
        try: 
            link = driver6.find_element_by_partial_link_text('Bill History').click()
            page  = driver6.page_source
        except:
            page  = driver6.page_source
        try:
            history = page.split('<div id="billHistory">')[1].split('<div class="tab-pane" id="thirds3322">')[0]
            docLinks6.append(re.findall(docTerm,history))
        except:
            continue
    with open('docLinks6.txt','w') as f:
        f.write('\n'.join([item for sublist in docLinks6 for item in sublist]))

#22800
#urls 24358-24359 don't exist
#RPO18-0002
def loop_g():
    i=0
    for url in urls[25101:26600]:
        print(i)
        i+=1
        try:
            driver7.get(url)
        except:
            continue
        # waiting for the page is fully loaded
        time.sleep(5)
        try: 
            link = driver7.find_element_by_partial_link_text('Bill History').click()
            page  = driver7.page_source
        except:
            page  = driver7.page_source
        try:
            history = page.split('<div id="billHistory">')[1].split('<div class="tab-pane" id="thirds3322">')[0]
            docLinks7.append(re.findall(docTerm,history))
        except:
            continue
    with open('docLinks7.txt','w') as f:
        f.write('\n'.join([item for sublist in docLinks7 for item in sublist]))

#26600
def loop_h():
    i=0
    for url in urls[28901:30400]:
        print(i)
        i+=1
        try:
            driver8.get(url)
        except: 
            continue
        # waiting for the page is fully loaded
        time.sleep(5)
        try: 
            link = driver8.find_element_by_partial_link_text('Bill History').click()
            page  = driver8.page_source
        except:
            page  = driver8.page_source
        try:
            history = page.split('<div id="billHistory">')[1].split('<div class="tab-pane" id="thirds3322">')[0]
            docLinks8.append(re.findall(docTerm,history))
        except:
            continue
    with open('docLinks8.txt','w') as f:
        f.write('\n'.join([item for sublist in docLinks8 for item in sublist]))

#30400
def loop_i():
    i=0
    for url in urls[32701:34200]:
        print(i)
        i+=1
        try:
            driver9.get(url)
        except:
            continue
        # waiting for the page is fully loaded
        time.sleep(5)
        try: 
            link = driver9.find_element_by_partial_link_text('Bill History').click()
            page  = driver9.page_source
        except:
            page  = driver9.page_source
        try:
            history = page.split('<div id="billHistory">')[1].split('<div class="tab-pane" id="thirds3322">')[0]
            docLinks9.append(re.findall(docTerm,history))
        except:
            continue
    with open('docLinks9.txt','w') as f:
        f.write('\n'.join([item for sublist in docLinks9 for item in sublist]))

#34200
def loop_j():
    i=0
    for url in urls[36501:]:
        print(i)
        i+=1
        try:
            driver10.get(url)
        except:
            continue
        # waiting for the page is fully loaded
        time.sleep(5)
        try: 
            link = driver10.find_element_by_partial_link_text('Bill History').click()
            page  = driver10.page_source
        except:
            page  = driver10.page_source
        try:
            history = page.split('<div id="billHistory">')[1].split('<div class="tab-pane" id="thirds3322">')[0]
            docLinks10.append(re.findall(docTerm,history))
        except:
            continue
    with open('docLinks10.txt','w') as f:
        f.write('\n'.join([item for sublist in docLinks10 for item in sublist]))      


Process(target=loop_a).start()
Process(target=loop_b).start()
Process(target=loop_c).start()
Process(target=loop_d).start()
Process(target=loop_e).start()
Process(target=loop_f).start()
Process(target=loop_g).start()
Process(target=loop_h).start()
Process(target=loop_i).start()
Process(target=loop_j).start()


docLinks = [item for sublist in docLinks for item in sublist]
# once we have all the urls to download, we can check which we've already downloaded
global docLinksToDownload
docLinksToDownload = []
def checkDownloaded(docLinks):
    if os.path.isdir('pdfs'):
        downloaded = os.listdir('pdfs')
        if all(docLink in downloaded for docLink in docLinks):
            return 1
        else:
            docLinksToDownload = [docLink for docLink in docLinks if docLink not in downloaded]
            return 0

# combining link files:
docs = ['doclinks','docLinks1','docLinks2','docLinks3','docLinks4','docLinks5','docLinks6','docLinks7','docLinks8','docLinks9','docLinks10','docLinks11']
links = []
for doc in docs:
with open(doc+'.txt','r') as f:
    links.append(f.read())

links = [item.split('\n') for item in links]
links = [item for sublist in links for item in sublist]

links = list(set(links))
with open('doclinks.txt','w') as f:
    f.write('\n'.join(links))
