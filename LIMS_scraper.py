import requests
import re
import json 
from subprocess import PIPE, check_call
from unipath import Path
import os.path
import pytesseract
from PIL import Image
import glob
from PyPDF2 import PdfFileReader
import inquirer
import datetime
from math import floor

def convertToRegex(searchTerm):
    words = searchTerm.split(' ')
    regExTerm = '(?i)'
    for word in words:
        regExTerm +=word+'\s*'
    return re.compile(regExTerm)

# to check if user inputs valid date criteria
def validate(dateText):
    if dateText:
        try:
            datetime.datetime.strptime(dateText, '%m/%d/%Y')
        except ValueError:
            raise(ValueError('Date format should be MM/DD/YYYY'))
    else:
        pass

# This only downloads introductions - they are the only doc types with a URL in the search result json. 
# Would need to iterate through all possible file names (bill #, doctype combinations) to get other kinds of docs
def downloadToText(r,path,docTypes,urlsToDownload=None):
    ## To download files, convert PDF to text
    path1 = path+'text/'
    path = path+'pdfs/'
    locations = []
    if not os.path.isdir(path):
        os.mkdir(path)
    if not os.path.isdir(path1):
        os.mkdir(path1)
    if urlsToDownload:
        for url in urlsToDownload:
            urls = [url]
            for docType in docTypes:
                urls.append('-'.join(url.split('-')[:-1])+'-'+docType+'.pdf')
            loc = path+url.split('/')[-1]
            # check if introduction has been downloaded - if it has, don't test other doc types
            #if not os.path.isfile(loc): - add this back in to final 
            for url in urls:
                print(url)
                docs = '-'.join(url.split('-')[:-1])
                # store locations so we can reuse them when extracting text
                loc = path+url.split('/')[-1]
                # location for pulled downloadToText
                loc1 = path1+url.split('/')[-1]
                locations.append(loc1)
                # only download file if it doesnt exist yet
                if not os.path.isfile(loc):
                    response = requests.get(url)
                    #for files that don't exist, the longest downloaded 'pdf' i've seen is 8478 bytes - shortest existing pdf is 8879 bytes - there must be a better way to test if the file exists 
                    if len(response.content)>8478:
                        with open(loc, 'wb') as f:
                            f.write(response.content)
                            # if file is already OCR'd, just use pdftotext to pull text
                            check_call(['pdftotext', '-enc', 'UTF-8','-layout' , loc,loc1[:-3]+'txt'], stdout=PIPE)
                            with open(loc1[:-3]+'txt','r') as f:
                                # small files (i've seen length up to 116 bytes when read) are created when we call pdftotext on a non-OCR'd pdf
                                if len(f.read())<1000:
                                    # if file is not OCR'd (older PDFs and some angled scans), convert PDFs to png (smaller and higher qual than tiff and run tesseract OCR
                                    # specifying type grayscale breaks pytesseract for some images: 
                                    text = extractText(loc,path)
                                    with open(loc1[:-3]+'txt','w') as f:
                                        f.write(text)
    else:
        for bill in r.json(): 
            # some 'bills' (e.g. public hearings) do not have documents associated w them
            if bill['DocumentUrl']:
                # documentUrl field only includes URL for introduction (not Signed Act or intermediate documents)
                # is it safe to asume that if there is no Introduction there are no other documents?
                url = bill['DocumentUrl']
                urls = [bill['DocumentUrl']]
                # what if not all docs are from same council period? need to iterate over at least next period..
                for docType in docTypes:
                    urls.append('-'.join(url.split('-')[:-1])+'-'+docType+'.pdf')
                loc = path+url.split('/')[-1]
                # check if introduction has been downloaded - if it has, don't test other doc types
                #if not os.path.isfile(loc): - add this back in to final 
                for url in urls:
                    print(url)
                    docs = '-'.join(url.split('-')[:-1])
                    # store locations so we can reuse them when extracting text
                    loc = path+url.split('/')[-1]
                    # location for pulled downloadToText
                    loc1 = path1+url.split('/')[-1]
                    locations.append(loc1)
                    # only download file if it doesnt exist yet
                    if not os.path.isfile(loc):
                        response = requests.get(url)
                        #for files that don't exist, the longest downloaded 'pdf' i've seen is 8478 bytes - shortest existing pdf is 8879 bytes - there must be a better way to test if the file exists 
                        if len(response.content)>8478:
                            with open(loc, 'wb') as f:
                                f.write(response.content)
                                # if file is already OCR'd, just use pdftotext to pull text
                                check_call(['pdftotext', '-enc', 'UTF-8','-layout' , loc,loc1[:-3]+'txt'], stdout=PIPE)
                                with open(loc1[:-3]+'txt','r') as f:
                                    # small files (i've seen length up to 116 bytes when read) are created when we call pdftotext on a non-OCR'd pdf
                                    if len(f.read())<1000:
                                        # if file is not OCR'd (older PDFs and some angled scans), convert PDFs to png (smaller and higher qual than tiff and run tesseract OCR
                                        # specifying type grayscale breaks pytesseract for some images: 
                                        text = extractText(loc,path)
                                        with open(loc1[:-3]+'txt','w') as f:
                                            f.write(text)
    return(locations)


def convertGrayscale(imageLocation,i):
    params = ['convert', '-density','300', '-units','PixelsPerInch', '-type','Grayscale', imageLocation+str([i]), imageLocation[:-4]+'-'+str([i])+'.png']
    check_call(params)

def convertColor(imageLocation,i):
    params = ['convert', '-density','300', '-units','PixelsPerInch', imageLocation+str([i]), imageLocation[:-4]+'-'+str([i])+'.png']
    check_call(params)

def extractText(imageLocation,path):
   # converting to png outputs one file for each page, with -1,-2,...-n.png extensions - need a way to determine how many files are created
    text = ''
    numPages = PdfFileReader(open(imageLocation,'rb')).getNumPages()
    for i in range(numPages):
        try:
            convertGrayscale(imageLocation,i)
            text+=pytesseract.image_to_string(Image.open(imageLocation[:-4]+'-'+str([i])+'.png'))
        except:
            convertColor(imageLocation,i)
            text+=pytesseract.image_to_string(Image.open(imageLocation[:-4]+'-'+str([i])+'.png'))
        # delete pngs after text extraction: they are pretty large
    for file in glob.glob(os.path.join(path, imageLocation.split('/')[-1][:-4]+'-*.png')):
        os.remove(file)
    return(text)

def search(loc,searchTerm):
    parSplit = re.compile('\n\n')
    paragraphs = {}
    for file in loc:
        try:
            with open(file[:-3]+'txt') as doc:
                content = doc.read()
                docParagraphs = []
                for paragraph in re.split(parSplit,content):
                    if searchTerm.findall(paragraph):
                        # remove extra whitespace
                        paragraph = re.sub( '\s+', ' ', paragraph ).strip()
                        # remove newline chars
                        paragraph = paragraph.replace('\n',' ')
                        # strip _ chars
                        paragraph = paragraph.replace('_','')
                        # strip tab chars (so they don't mess with tsv output)
                        paragraph = paragraph.replace('\t','')
                        docParagraphs.append(paragraph)
                        # maintain dict of dicts showing which paragraphs came from which document associated with the bill (e.g. introduction, signed act)
                        paragraphs['-'.join(file.split('/')[-1].split('-')[:2])]={}
                        paragraphs['-'.join(file.split('/')[-1].split('-')[:2])][str(file.split('/')[-1].split('-')[-1][:-4])]=docParagraphs
        except FileNotFoundError:
            pass
    return paragraphs

# could add a spellchecker to output to fix words where OCR missed a letter or something - would need to make sure it does more good than harm
def saveSearchResults(results,path):
    # write to tsv so we don't get messed up by commas in original doc (are there tabs that mess us up?)
    with open(path+'searchResults.tsv','w') as outFile:
        keys = sorted(results.keys())
        outFile.write('Bill ID'+'\t'+'Document Type'+'\t'+'paragraphs where search term was found'+'\n')
        for key in keys:
            docTypes = results[key].keys()
            for docType in docTypes:
                values = results[key][docType]
                outFile.write(key+'\t'+docType+'\t'+'\t'.join(values)+'\n')

def downloadAndSearch(criteria,path,r,searchTerm,docTypes,urlsToDownload):
    # download files, convert PDFs to text, create list of file locations
    loc = downloadToText(r,path,docTypes,urlsToDownload)
    # search downloaded and converted files, pull paragraphs containing search term
    results = search(loc,searchTerm)
    # save search results to file
    saveSearchResults(results,path)


def getSearchCriteria():
    keyword = inquirer.prompt([inquirer.Text('Keyword', 
    message="Search by Legislation number or Legislation title")])    
    # master lists to find codes for search criteria
    # types master list
    categories =  requests.get(base+'/api/v1/masters/LegislationCategories').json()
    legislationCategories = ["All"]
    categoryIdLookup = {}
    for i in range(len(categories)):
        legislationCategories.append(categories[i]['LegislationCategory'])
        categoryIdLookup[categories[i]['LegislationCategory']]=categories[i]['Id']

    category = inquirer.prompt([inquirer.List('CategoryId',
        message="Choose a category of Legislation to search",
        choices=legislationCategories)])

    # need Id for search criteria; set to 0 if all selected
    if category['CategoryId']!="All":
        category['CategoryId'] = categoryIdLookup[category['CategoryId']]
    else:
        category['CategoryId'] = 0

    # subcategories belong to each category - I could implement this but is it worth the time? ask David about it
    # same is true for Introduced/co-sponsored by/At the request of/Referred to (committee)/Referred to (committee with comments)  - these depend on which council period is selected
    # master category: subcategories dictionary
    subcategories =  requests.get(base+'/api/v1/masters/LegislationTypes').json()
    legislationSubcategories = {}

    for i in categoryIdLookup.values():
        legislationSubcategories[i] = []

    subcatIdLookup = {}
    for i in subcategories:
        subcatIdLookup[i['LegislationType']] = i['Id']

    for i in range(len(subcategories)):
        legislationSubcategories[categoryIdLookup[subcategories[i]['LegislationCategory']]].append(subcategories[i]['LegislationType'])

    # now need to offer subcat choice based on cat choice (only some have subcategories)
    haveSubcats = [categoryIdLookup['Report'],categoryIdLookup['Bill'],categoryIdLookup['Resolution']]
    if category['CategoryId'] in haveSubcats:
        subcatChoices=["All"]
        for subcat in legislationSubcategories[category['CategoryId']]:
            subcatChoices.append(subcat)

        subcategory = inquirer.prompt([inquirer.List('SubCategoryId',
            message="Choose a subcategory of Legislation to search",
            choices=subcatChoices)])

        # need Id for search criteria; set to 0 if all selected
        if subcategory['SubCategoryId']!="All":
            subcategory['SubCategoryId']=subcatIdLookup[subcategory['SubCategoryId']]
        else:
            subcategory['SubCategoryId'] = 0
        
    # Get council period choice
    CouncilPeriod = 0
    validChoices = list(range(8,23))
    validChoices.append("All")
    while CouncilPeriod not in validChoices:
        CouncilPeriod = input("Please select a Council Period (8 - 22; default is all periods): ") or "All"
        if CouncilPeriod !="All":
            try:
                CouncilPeriod=int(CouncilPeriod)
            except ValueError:
                print("That wasn't an integer")

    if CouncilPeriod == "All":
        CouncilPeriod = 0

    ## can't do at the request of field - there is no API to access options, and they change every council period. 
    ## Could do it by hand but it would take forever
    ## there are also tons of typos in the lists of options, seems like it doesn't work as intended anyway
    # next fill out introduced by and co-sponsored by fields - don't think it is possible (or desirable, you'd have a 100-member dropdown)
    # to replicate the active/inactive list of all current/former members when you select All Council Periods in advanced search
    members = requests.get(base+'/api/v1/masters/Members/'+str(CouncilPeriod)).json()
    names = ["All"]
    nameIdLookup = {}
    for i in range(len(members)):
        names.append(members[i]['Name']) 
        nameIdLookup[members[i]['Name']]=members[i]['Id']

    introducedBy = inquirer.prompt([inquirer.List('Introducer',
        message="Search for legislation introduced by",
        choices=names)])

    # So you can't choose the same person as introducer and co-sponsor
    if introducedBy['Introducer']!="All":
        names.remove(introducedBy['Introducer'])
        introducedBy['Introducer']=nameIdLookup[introducedBy['Introducer']]
    else:
        introducedBy['Introducer'] = 0

    cosponsor = inquirer.prompt([inquirer.List('CoSponsor',
        message="Search for legislation co-sponsored by",
        choices=names)])

    if cosponsor['CoSponsor']!="All":
        cosponsor['CoSponsor']=nameIdLookup[cosponsor['CoSponsor']]
    else:
        cosponsor['CoSponsor'] = 0

    # committee criterai - referred to and referred to (w/ comments)
    # master list
    committees = requests.get(base+'/api/v1/masters/Committees/'+str(CouncilPeriod)).json()
    referredToOptions = ["All"]
    committeeIdLookup = {}
    for i in range(len(committees)):
        referredToOptions.append(committees[i]['Name'])
        committeeIdLookup[committees[i]['Name']]=committees[i]['Id']

    referredTo = inquirer.prompt([inquirer.List('CommitteeId',
        message="Search for legislation referred to the",
        choices=referredToOptions)])

    if referredTo['CommitteeId']!="All":
        referredTo['CommitteeId'] = committeeIdLookup[referredTo['CommitteeId']]
        referredToOptions.remove(referredTo['CommitteeId'])
    else:
        referredTo['CommitteeId'] = 0

    try:
        referredToOptions.remove('Retained by the Council')
    except:
        pass

    referredToComments = inquirer.prompt([inquirer.List('CommitteeCommentsId',
        message="Search for legislation referred with comments to the",
        choices=referredToOptions)])

    if referredToComments['CommitteeCommentsId']!="All":
        referredToComments['CommitteeCommentsId'] = committeeIdLookup[referredToComments['CommitteeCommentsId']]
    else:
        referredToComments['CommitteeCommentsId'] = 0

    #  statuses master list
    statuses = requests.get(base+'/api/v1/masters/LegislationStatus').json()
    LegislationStatuses = ["All"]
    statusIdLookup = {}
    for i in range(len(statuses)):
        LegislationStatuses.append(statuses[i]['Name'])
        statusIdLookup[statuses[i]['Name']] = statuses[i]["Id"]


    legislationStatus=inquirer.prompt([inquirer.List('LegislationStatus',
                message='Choose the status of Legislation to search',
                choices=LegislationStatuses)])

    if legislationStatus['LegislationStatus']!="All":
        legislationStatus['LegislationStatus'] = statusIdLookup[legislationStatus['LegislationStatus']]
    else:
        legislationStatus['LegislationStatus'] = 0

    validDates = 0
    validStart=0
    validEnd =0
    while not validDates:
        while not (validStart): 
            StartDate = input('Enter the beginning of the date range to search in MM/DD/YYYY format: ')
            try:
                validate(StartDate)   
                validStart = 1
            except:
                print("Date format should be MM/DD/YYYY. Leave blank to include all dates")
                pass
        while not (validEnd):
            EndDate = input('Enter the end of the date range to search in MM/DD/YYYY format: ')
            try:
                validate(EndDate) 
                validEnd = 1
            except:
                print("Date format should be MM/DD/YYYY. Leave blank to include all dates")
                pass
        if not (StartDate or EndDate):
            validDates = 1
        else:
            if EndDate:
                if datetime.datetime.strptime(StartDate, '%m/%d/%Y') < datetime.datetime.strptime(EndDate, '%m/%d/%Y'):
                    validDates = 1
                else: 
                    print('End date must be after start date.')
            else:
                validDates=1   

    # advanced search criteria
    # possible categories for advanced search listed at http://lims.dccouncil.us/api/Help/Api/POST-v1-Legislation-AdvancedSearch-rowLimit-offSet 
    # need to make sure my criteria names match up with API format
    # need to change names/text values to their corresponding codes
    # CategoryId needs to be CategoryID - Category should be numeric
    # If choice is all, need to omit criteria
    if not keyword['Keyword']:
        try:
            criteria = {**category,**subcategory,**introducedBy,**cosponsor,**referredTo,**referredToComments,**legislationStatus}
        # if we didn't pick a category that has subcategories
        except:
            criteria = {**category,**introducedBy,**cosponsor,**referredTo,**referredToComments,**legislationStatus}
    else:  
        try:      
            criteria = {**keyword,**category,**subcategory,**introducedBy,**cosponsor,**referredTo,**referredToComments,**legislationStatus}
        except:
            criteria = {**keyword,**category,**introducedBy,**cosponsor,**referredTo,**referredToComments,**legislationStatus}

    for criterion in [CouncilPeriod,StartDate,EndDate]:
        if not criterion:
            pass
        else:
            criteria['CouncilPeriod']=CouncilPeriod
            criteria['StartDate']=StartDate
            criteria['EndDate']=EndDate

    ### do the following even if already downloaded
    searchTerm = convertToRegex(input("What would you like to search the downloaded documents for? "))

    path = Path(input("Where would you like to save downloaded PDFs and extracted text? (default is current working directory): ") or os.getcwd()+'/')
    #path = Path('/Users/joshuakaplan/Documents/Georgetown/Spring 2017/Dr Bailey/Scraping/Signed Acts/')
    return(criteria, path, searchTerm)

def docTypeList():
    # once we know this part is pulling every doc, we only need to check for the existence of the introduction
    docTypes = ['SignedAct','Engrossment','Enrollment','CommitteeReport']
    # special case: how many are like this: http://lims.dccouncil.us/Download/36248/B21-0837-Amendments11.pdf
    # amendments go up to 17 (seems like they are numbered wrong for b21-0415, and cmmittee reports go up to 12 (also seems numbered wrong for b20-0198))
    for i in range(1,13):
        docTypes.append('CommitteeReport'+str(i))
    for i in range(1,18):
        docTypes.append('Amendment'+str(i))
    for i in range(1,4):
        for docType in ['HearingRecord','HearingNotice']:
            docTypes.append(docType+str(i))
    return docTypes

# this doesnt work right; need to compare to number of bills that actually have URLS/docs
# 57 of first 1000  results dont have any docs linked.\
global urlsToDownload
urlsToDownload = []
def checkDownloaded(r,councilPeriod):
    countTerm1= re.compile('([A-Z]+'+str(councilPeriod)+'-\d*-Introduction)')
    countTerm2= re.compile('([A-Z]+'+str(councilPeriod)+'-\d*-Agenda)')
    # will me miss recent updates if we start with an offset?
    # offset works in blocks of 1000 records i.e. offset of 1 will start at 1001st record. 
    urls =  {}
    for bill in r.json():
        if bill['DocumentUrl'].split('/')[-1][:-4] != '':
            urls[bill['DocumentUrl'].split('/')[-1][:-4]] = bill['DocumentUrl']
    if os.path.isdir('pdfs'):
        files = os.listdir('pdfs')
        downloaded = countTerm1.findall(' '.join(files))+countTerm2.findall(' '.join(files))
        if all(url in downloaded for url in urls.keys()):
            return 1
        else:
            toDownload = [url for url in urls.keys() if url not in downloaded]
            for bill in toDownload:
                urlsToDownload.append(urls[bill])
            return 0

if __name__ == '__main__':
    # base url
    base = 'http://lims.dccouncil.us'
    criteria,path,searchTerm = getSearchCriteria()
    print(criteria)
    # there seems to be a hard limit of 1000 on the number of search results returned - maybe David can talk to them about raising it
    # we can count the number of documents with both [Letters]21 and Introduction in their name to determine the row offset parameter, so we don't have to check that we downloaded everything
    # if i want to download more than 1000 in a run i need to make this a loop
    offset = 0
    r = requests.post(base+'/api/v1/Legislation/AdvancedSearch/1000/'+str(offset),json=criteria)
    if criteria['CouncilPeriod']:
        # can only check 1000 bills at once
        while checkDownloaded(r,criteria['CouncilPeriod']):
            offset+=1
            r = requests.post(base+'/api/v1/Legislation/AdvancedSearch/1000/'+str(offset),json=criteria)
    docTypes = docTypeList()
    downloadAndSearch(criteria,path,r,searchTerm,docTypes,urlsToDownload)  