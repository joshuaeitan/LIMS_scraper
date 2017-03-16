#Weekly update of which bills have had changes

#One possible approach: pull pdf (already OCR-d) bill history from http://lims.dccouncil.us/_layouts/15/uploader/AdminProxy.aspx?LegislationId=PR22-0170
#   Would have to dowload pdf for every bill ID for at least past two council sessions
#   download, convert to text, check dates in bill history section
#   If something has changed in the last week, add to output

# takes an hour and a half to download and process last 3 council sessions (20,21,22)

from subprocess import check_call, PIPE
import os
import re
import requests
import json
import datetime
import sys
import shutil
import schedule
import time

timeFrame = int(sys.argv[1])

def clean():
    if os.path.isdir('LegislationDetailsText'):
        shutil.rmtree('LegislationDetailsText')
    if os.path.isdir('LegislationDetailsPDFs'):
        shutil.rmtree('LegislationDetailsPDFs')

def getLegislationStatus():
# get all legislation IDs
    criteria = {'LegislationStatus': 0, 'CommitteeCommentsId': 0, 'CategoryId': 0, 'StartDate': '', 'CoSponsor': 0, 'EndDate': '', 'Introducer': 0, 'CouncilPeriod': 0, 'CommitteeId': 0}
    base = 'http://lims.dccouncil.us'

    ids= []
    for i in range(20,23):
        criteria['CouncilPeriod']=i
        offset=0
        while True:
            r = requests.post(base+'/api/v1/Legislation/AdvancedSearch/1000/'+str(offset),json=criteria)
            ids.extend([bill['LegislationNumber'] for bill in r.json()])
            offset+=1
            if not r.json():
                break

    # download Legislation Detail pdf
    path = os.getcwd()+'/'

    url = 'http://lims.dccouncil.us/_layouts/15/uploader/AdminProxy.aspx?LegislationId='
    path1 = path+'LegislationDetailsText/'
    path = path+'LegislationDetailsPDFs/'
    if not os.path.isdir(path):
        os.mkdir(path)

    if not os.path.isdir(path1):
        os.mkdir(path1)

    for id in ids:
        loc = path+id+'.pdf'
        loc1 = path1+id+'.txt'
        if not os.path.isfile(loc):
            r = requests.get(url+id)
            with open(loc, 'wb') as f:
                f.write(r.content)
            check_call(['pdftotext', '-enc', 'UTF-8','-layout' , loc,loc1[:-3]+'txt'], stdout=PIPE)


#took from 9:24 - 3:41 (4:41 but missing daylight savings hour) to download 35783 (of 37610) items 
#6hr 17 = 377 minutes; if we only need to check say last 3 council periods (20,21,22), we would have 568+3818+4023 = 8409 (up to about 12000 by end of council period) items:
#would take about 90 (88.6) minutes to download those 8409 bill histories - then how long to process them?

# takes 11 seconds to find updated items and save them
# find legislation with updates in the last week ()
# also need to check date is not after today, or they will just show up every week



# 1: is to get rid of .ds_store
def getUpdates(timeFrame):
    today = datetime.date.today()
    updatesSince= today-datetime.timedelta(days=timeFrame)
    updatesTo = today+datetime.timedelta(days=timeFrame)
    locs = os.listdir('LegislationDetailsText')[1:]
    updated = {}
    dateSearch = re.compile('[A-Z][\D][\D] \d*, [\d][\d][\d][\d]')
    pageNumLine = re.compile('\\n[A-Z][\D][\D] \d*, [\d][\d][\d][\d]\s*Page: \d\\n\\x0c')
    for loc in locs:
        hasUpdates = 0
        with open('LegislationDetailsText/'+loc) as doc:
            content = doc.read()
            legTitle = content.split(loc[:-4])[1].split('\n\n\n')[0].lstrip('- ').rstrip('.')
            if legTitle.split(' ')[-1]=='New':
                legTitle = ' '.join(legTitle.split(' ')[:-1])
            elif legTitle.split(' ')[-1]=='Withdrawn':
                legTitle = ' '.join(legTitle.split(' ')[:-1])
            elif ' '.join(legTitle.split(' ')[-3:])=='Under Council Review':
                legTitle = ' '.join(legTitle.split(' ')[:-3])
            # do we need this? what happend for docs w/out bill history
            try:
                # 2 page docs mess up the split - there aren't five lines between the history and end of the page
                history = ' '.join(content.split('Bill History')[1:]).split('\n\n\n\n\n')[0]
                history = pageNumLine.sub('',history)
                items = history.split('\n\n')[1:]
                for item in items:
                    try:
                        date = datetime.datetime.strptime(dateSearch.search(str(item)).group(), "%b %d, %Y").date()
                        if date>updatesSince and date <=updatesTo:
                            if hasUpdates==0:
                                updated[loc[:-4]] = {}
                                updated[loc[:-4]][legTitle]=[]
                                hasUpdates=1
                            updated[loc[:-4]][legTitle].append(item)
                    # if the item doesn't contain a date, it's not an entry in the bill history, so we dont care about it
                    except AttributeError:
                        continue
            except IndexError:
                continue
    return(updated)

# now need to convert this to neat output: bill ID - date of introduction, date of update, date of signature
# pull legislation number

def saveUpdates(updated):
    path = os.getcwd()+'/'
    with open(path+'weeklyUpdate'+ datetime.datetime.strftime(datetime.datetime.today(),"%m_%d_%Y")+'.tsv','w') as outFile:
        keys = sorted(updated.keys())
        outFile.write('Legislation ID'+'\t'+'Legislation Title'+'\t'+'Update Date'+'\t'+'Update Content'+'\n')
        for key in keys:
            legTitle = sorted(updated[key].keys())[0]
            cleanLegTitle = ' '.join(legTitle.replace('\n','').split())
            outFile.write(key+'\t'+cleanLegTitle+'\t')
            if len(updated[key][legTitle])==1:
                for update in updated[key][legTitle]:
                    split = update.split('        ')
                    date = str(datetime.datetime.strptime(split[0].lstrip(), "%b %d, %Y").date())
                    content = split[-1].lstrip()
                    outFile.write(date+'\t'+content+'\n')
            else:
                for update in updated[key][legTitle][:-1]:
                    split = update.split('        ')
                    date = str(datetime.datetime.strptime(split[0].lstrip(), "%b %d, %Y").date())
                    content = split[-1].lstrip()
                    outFile.write(date+'\t'+content+'\n'+'\t\t')
                update = updated[key][legTitle][-1]
                split = update.split('        ')
                date = str(datetime.datetime.strptime(split[0].lstrip(), "%b %d, %Y").date())
                content = split[-1].lstrip()
                outFile.write(date+'\t'+content+'\n')

def downloadAndSave(timeFrame=timeFrame):
    clean()
    getLegislationStatus()
    updated = getUpdates(timeFrame)
    saveUpdates(updated)

# another approach: scrape bill history direectly from javascript: https://impythonist.wordpress.com/2015/01/06/ultimate-guide-for-scraping-javascript-rendered-web-pages/
if __name__ == '__main__':
    #https://schedule.readthedocs.io
    schedule.every().sunday.at("20:00").do(downloadAndSave)
    while 1:
        schedule.run_pending()
        time.sleep(1)