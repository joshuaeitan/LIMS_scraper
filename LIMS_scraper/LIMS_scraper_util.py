import requests
import re
import json 
from subprocess import PIPE, Popen, check_call
from unipath import Path
import os.path
import pytesseract
from PIL import Image
import glob

def convertToRegex(searchTerm):
    words = searchTerm.split(' ')
    regExTerm = '(?i)'
    for word in words:
        regExTerm +=word+'\s*'
    return re.compile(regExTerm)

def downloadToText(r,path):
    ## To download files, convert PDF to text
    ids = []
    loc = []
    num = len(r.json())
    for i in range(num):
        ids.append((r.json()[i]['Id'],r.json()[i]['LegislationNumber']))
        url = 'http://lims.dccouncil.us/Download/'+str(ids[i][0])+'/'+ids[i][1]+'-SignedAct.pdf'
        # store locations so we can reuse them when extracting text
        loc.append(path+ids[i][1]+'-SignedAct.pdf')
        if not os.path.isfile(loc[i]):
            response = requests.get(url)
            #if the file doesnt exist, the downloaded 'pdf' will be 531 bytes
            if len(response.content)!=531:
                with open(loc[i], 'wb') as f:
                    f.write(response.content)
                    # if file is already OCR'd, just use pdftotext to pull text
                check_call(['pdftotext', '-enc', 'UTF-8','-layout' , loc[i]], stdout=PIPE)
                with open(loc[i][:-3]+'txt','r') as f:
                    # empty files (length 3 when read) are created when we call pdftotext on a non-OCR'd pdf
                    if len(f.read())<10:
                        # if file is not OCR'd (older PDFs and some angled scans), convert PDFs to png (smaller and higher qual than tiff and run tesseract OCR
                        params = ['convert', '-density','300', '-units','PixelsPerInch', '-type','Grayscale', loc[i], loc[i][:-3]+'png']
                        check_call(params)
                        # converting to png outputs one file for each page, with -1,-2,...-n.png extensions - need a way to determine how many files are created
                        pages = glob.glob(loc[i][:-4]+'-*')
                        text = ''
                        for page in pages:
                            text+=pytesseract.image_to_string(Image.open(page))
                        with open(loc[i][:-3]+'txt','w') as f:
                            f.write(text)
    return ids,loc

def search(loc,searchTerm):
    parSplit = re.compile('\n\n')
    paragraphs = {}
    for i in range(len(loc)):
        try:
            with open(loc[i][:-3]+'txt') as file:
                content = file.read()
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
                        paragraphs[loc[i][84:92]]=docParagraphs
        except FileNotFoundError:
            pass
    return paragraphs

def saveSearchResults(results,path):
    # write to tsv so we don't get messed up by commas in original doc (are there tabs that mess us up?)
    with open(path.parent.parent+'/searchResults.tsv','w') as outFile:
        keys = sorted(results.keys())
        outFile.write('Bill ID'+'\t'+'paragraphs where search term was found'+'\n')
        for key in keys:
            values = results[key]
            outFile.write(key+'\t'+'\t'.join(values)+'\n')



