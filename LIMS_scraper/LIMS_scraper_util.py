import requests
import re
import json 
from subprocess import PIPE, Popen, check_call
from unipath import Path
import os.path
import pytesseract
from PIL import Image
import glob
from PyPDF2 import PdfFileReader

def convertToRegex(searchTerm):
    words = searchTerm.split(' ')
    regExTerm = '(?i)'
    for word in words:
        regExTerm +=word+'\s*'
    return re.compile(regExTerm)

# This only downloads introductions - they are the only doc types with a URL in the search result json. 
# Would need to iterate through all possible file names (bill #, doctype combinations) to get other kinds of docs

def downloadToText(r,path,docTypes):
    ## To download files, convert PDF to text
    path1 = path+'text/'
    path = path+'pdfs/'
    locations = []
    if not os.path.isdir(path):
        os.mkdir(path)
    if not os.path.isdir(path1):
        os.mkdir(path1)
    for bill in r.json(): 
        # some 'bills' (e.g. public hearings) do not have documents associated w them
        if bill['DocumentUrl']:
            # documentUrl field only includes URL for introduction (not Signed Act or intermediate documents)
            # is it safe to asume that if there is no Introduction there are no other documents?
            url = bill['DocumentUrl']
            urls = [bill['DocumentUrl']]
            for docType in docTypes:
                urls.append('-'.join(url.split('-')[:-1])+'-'+docType+'.pdf')
            for url in urls:
                docs = '-'.join(url.split('-')[:-1])
                # store locations so we can reuse them when extracting text
                loc = path+url.split('/')[-1]
                # location for pulled downloadToText
                loc1 = path1+url.split('/')[-1]
                locations.append(loc1)
                # only download file if it doesnt exist yet
                if not os.path.isfile(loc):
                    response = requests.get(url)
                    #if the file doesnt exist, the downloaded 'pdf' will be 531 bytes
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
    for file in glob.glob(os.path.join(path, '*-*.png')):
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

def downloadAndSearch(criteria,path,r,searchTerm,docTypes):
    # download files, convert PDFs to text, create list of file locations
    loc = downloadToText(r,path,docTypes)
    # search downloaded and converted files, pull paragraphs containing search term
    results = search(loc,searchTerm)
    # save search results to file
    saveSearchResults(results,path)


