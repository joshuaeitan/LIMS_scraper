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

confirm = {
    inquirer.Confirm('confirmed',
                     message="Have you already downloaded the files you want to search?" ,
                     default=True)
}
confirmation = inquirer.prompt(confirm)

if not confirmation['confirmed']:
    base = 'http://lims.dccouncil.us'
    # master lists to find codes for search criteria
    # types master list
    categories =  requests.get(base+'/api/v1/masters/LegislationCategories').json()
    LegislationCategories = []
    for i in range(len(categories)):
        LegislationCategories.append(categories[i]['LegislationCategory'])

    # subcategories belong to each category - I could implement this but is it worth the time? ask David about it
    # same is true for Introduced/co-sponsored by/At the request of/Referred to (committee)/Referred to (committee with comments)  - these depend on which council period is selected
    #subCategories =  requests.get(base+'/api/v1/masters/LegislationTypes').json()
    #LegislationSubCategories = []
    #for i in range(len(subCategories)):
    #   LegislationSubCategories.append(subCategories[i]['LegislationCategory'])

    #  statuses master list
    statuses = requests.get(base+'/api/v1/masters/LegislationStatus').json()
    LegislationStatuses = []
    for i in range(len(statuses)):
        LegislationStatuses.append(statuses[i]['StatusText'])

    print('Please input the following search criteria to determine which files to download, or leave them blank to include all categories')
    questions = [
        inquirer.Text('Keyword', message="Search by Legislation number or Legislation title"),
        inquirer.List('LegislationCategory',
                    message="Choose a category of Legislation to search",
                    choices=LegislationCategories),
        inquirer.List('LegislationStatus',
                    message='Choose the status of Legislation to search',
                    choices=LegislationStatuses)
    ]
    criteria = inquirer.prompt(questions)

    CouncilPeriod = 0
    while 8 > CouncilPeriod or 22 < CouncilPeriod:
        try:
            CouncilPeriod = int(input("Please select a Council Period (8 - 22): "))
        except ValueError:
            print("That wasn't an integer")

    criteria['CouncilPeriod']=CouncilPeriod

    print('Next, we will create a date range for introduction of the legislation. Again, leave these fields blank to include all dates')
    BeginDate = input('Enter the beginning of the range in MM/DD/YYYY format: ')
    criteria['BeginDate']=BeginDate
    EndDate = input('Enter the end of the range in MM/DD/YYYY format: ')
    criteria['EndDate']=EndDate

searchTerm = convertToRegex(input("What would you like to search for? "))
# base url
base = 'http://lims.dccouncil.us'
# advanced search criteria
# possible categories for advanced search listed at http://lims.dccouncil.us/api/Help/Api/POST-v1-Legislation-AdvancedSearch-rowLimit-offSet 
criteria = {
    "CategoryId": "1",
    "CouncilPeriod": "21",
    # enacted bill
    "LegislationStatus": "60"
}
path = input("Where would you like to save downloaded PDFs and extracted text? (default is current working directory): ") or os.getcwd()
path = Path(path)

r = requests.post(base+'/api/v1/Legislation/AdvancedSearch',json=criteria)

if __name__ == '__main__':
    if confirmation['confirmed']:
        searchOnly(r,searchTerm,path)
    else:
        downloadAndSearch(criteria,path,r,searchTerm)  