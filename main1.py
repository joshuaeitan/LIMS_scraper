from LIMS_scraper.LIMS_scraper_util import * 
import inquirer
import datetime

# need to convert older pdfs (without OCR) and newer angled scans to some kind of image format
# try pdftotext first - if we can just pull text, no need to convert and run OCR
# need to check if pdftotext file is empty
#end goal: user inputs LIMS advanced search criteria for files to download and term to pull paragraphs based on - if files are already downloaded, skip to search step. 
# utilities needed - tesseract, pdftotext (probably there is an alternative to this), imagemagick
# python libraries requests, re, json, subprocess, os, unipath, pytesseract, PIL, glob

# need to convert criteria to form that works with advanced search API, need to make sure default criteria get overwritten if user says havent already downloaded data
### main1 allows user-input criteria, main lets you hardcode them


# base url
base = 'http://lims.dccouncil.us'


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

def validate(dateText):
    if dateText:
        try:
            datetime.datetime.strptime(dateText, '%m/%d/%Y')
        except ValueError:
            raise(ValueError('Date format should be MM/DD/YYYY'))
    else:
        pass

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
        if datetime.datetime.strptime(StartDate, '%m/%d/%Y') < datetime.datetime.strptime(EndDate, '%m/%d/%Y'):
            validDates = 1
        else: 
            print('End date must be after start date.')

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
print(criteria)

### do the following even if already downloaded
searchTerm = convertToRegex(input("What would you like to search the downloaded documents for? "))

path = Path(input("Where would you like to save downloaded PDFs and extracted text? (default is current working directory): ") or os.getcwd()+'/')
#path = Path('/Users/joshuakaplan/Documents/Georgetown/Spring 2017/Dr Bailey/Scraping/Signed Acts/')

# there seems to be a hard limit of 1000 on the number of search results returned - maybe David can talk to them about raising it
r = requests.post(base+'/api/v1/Legislation/AdvancedSearch/1000',json=criteria)

if __name__ == '__main__':
    downloadAndSearch(criteria,path,r,searchTerm)  