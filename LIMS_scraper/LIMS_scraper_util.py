import requests
import re
import json 
from subprocess import PIPE, Popen
from unipath import Path
import os.path

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
            ## can we do OCR here without acually downloading (writing to hard drive) the pdfs? - it looks like we cant, extraction tools dont recognize bytes object (response.content) as a PDF
            with open(loc[i], 'wb') as f:
                f.write(response.content)
            Popen(['pdftotext', '-enc', 'UTF-8','-layout' , loc[i]], stdout=PIPE)
    return loc

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



