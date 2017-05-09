from time import sleep
import requests
import re
import json 
from subprocess import PIPE, run,check_call, CalledProcessError
import os.path
import pytesseract
from PIL import Image
import glob
from PyPDF2 import PdfFileReader


with open('doclinks.txt') as file:
    urls = file.read().split('\n')

pdfs = os.getcwd()+'/pdfs/'
#if not os.path.isdir(pdfs):
#    os.mkdir(pdfs)

text = os.getcwd()+'/text/'
#if not os.path.isdir(text):
#    os.mkdir(text)

files = os.listdir('pdfs')
files = [str.lower(file) for file in files]
# do names in all caps mess this up (do the non-all caps versions not get found)? http://lims.dccouncil.us/Download/29298/B20-0142-COMMITTEEREPORT.pdf

toDownload = []
for url in urls:
    filename = str.lower(url.split('/')[-1])
    if filename not in files:
        toDownload.append(url)


councilPeriod20 = [url for url in toDownload if '20' in url.split("/")[-1].split('-')[0]]
councilPeriod21 = [url for url in toDownload if '21' in url.split("/")[-1].split('-')[0]]
councilPeriod22 = [url for url in toDownload if '22' in url.split("/")[-1].split('-')[0]]

# this file is broken for some reason: http://lims.dccouncil.us/Download/29565/B20-0409-Engrossment.pdf
# this too http://lims.dccouncil.us/Download/30020/GBM20-0050-Introduction.pdf

for file in councilPeriod22:
    print(file)
    response = requests.get(file)
    if len(response.content)==0:
        continue
    else:
        filename = file.split('/')[-1]
        if os.path.isfile(pdfs+filename):
            continue
        else:
            with open(pdfs+filename, 'wb') as file:
                file.write(response.content)
            try:
                # small pdfs get written too quickly for pdftotext to find them
                run(['pdftotext', '-enc', 'UTF-8','-layout' , pdfs+filename,text+filename[:-3]+'txt'], stdout=PIPE,check=True)
                with open(text+filename[:-3]+'txt','r') as f:
                    if len(f)<1000:
                        content = extractText(pdfs+filename,pdfs)
                        with open(path(text+filename[:-3])+'txt','w') as f:
                            f.write(content)
            except:
                with open(text+filename[:-3]+'txt','w') as f:
                    content = extractText(pdfs+filename,pdfs)
                    if content=='':
                        print('true')
                        continue
                    else:
                        f.write(content)


def convertGrayscale(imageLocation,i):
    params = ['convert', '-density','300', '-units','PixelsPerInch', '-type','Grayscale', imageLocation+str([i]), imageLocation[:-4]+'-'+str([i])+'.png']
    check_call(params)

def convertColor(imageLocation,i):
    params = ['convert', '-density','300', '-units','PixelsPerInch', imageLocation+str([i]), imageLocation[:-4]+'-'+str([i])+'.png']
    check_call(params)

# This doesn't deal with encrypted PDFs (why are there encrypted docs?) - if there turns out to be more than just the oen I will have to figure something out
def extractText(imageLocation,path):
   # converting to png outputs one file for each page, with -1,-2,...-n.png extensions - need a way to determine how many files are created
    text = ''
    try:
        numPages = PdfFileReader(open(imageLocation,'rb')).getNumPages()
    except:
        return('')
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