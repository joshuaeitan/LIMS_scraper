from LIMS_scraper.LIMS_scraper_util import * 

# need to convert older pdfs (without OCR) and newer angled scans to some kind of image format
# try pdftotext first - if we can just pull text, no need to convert and run OCR
# need to check if pdftotext file is empty

#end goal: user inputs LIMS advanced search criteria for files to download and term to pull paragraphs based on - if files are already downloaded, skip to search step. 

searchTerm = convertToRegex(input("What would you like to search for? "))

# base url
base = 'http://lims.dccouncil.us'

# master lists to find codes for search criteria
# types master list
types =  requests.get(base+'/api/v1/masters/LegislationCategories')
#types.json()
#  statuses master list
statuses = requests.get(base+'/api/v1/masters/LegislationStatus')
#statuses.json()

# advanced search criteria
# possible categories for advanced search listed at http://lims.dccouncil.us/api/Help/Api/POST-v1-Legislation-AdvancedSearch-rowLimit-offSet 
criteria = {
    "CategoryId": "1",
    "CouncilPeriod": "21",
    # enacted bill
    "LegislationStatus": "60"
}

path = Path('/Users/joshuakaplan/Documents/Georgetown/Spring 2017/Dr Bailey/Scraping/Signed Acts/')

r = requests.post(base+'/api/v1/Legislation/AdvancedSearch',json=criteria)

def main(criteria,path,r,searchTerm):
    # download files, convert PDFs to text, create list of file locations
    loc = downloadToText(r,path)
    # search downloaded and converted files, pull paragraphs containing search term
    results = search(loc,searchTerm)
    # save search results to file
    saveSearchResults(results,path)

if __name__ == '__main__':
    main(criteria,path,r,searchTerm)  