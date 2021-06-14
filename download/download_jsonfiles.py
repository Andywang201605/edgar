# Download Submission Json Files for all company

from time import sleep
from numpy import random
import pandas as pd
import requests
import json
import os

def _download_file(url, path):
    r = requests.get(url)
    with open(path, 'wb') as fp:
        fp.write(r.content)

def _check_fail(reportpath):    
    with open(reportpath) as fp:
        content = fp.read()
        
    return 'Your Request Originates from an Undeclared Automated Tool' in content


def _download_edgar(url, path, maxiter=-1, verbose=True):
    '''
    Download files from edgar, maxiter is the maximum attempts, -1 means try until download successfully
    '''
    try:
        attemptcount = 0
        _download_file(url, path)
        while _check_fail(path):
            sleep(random.uniform(1,2))
            _download_file(url, path)
            attemptcount += 1
            print(f'--Download Edgar Failed - Attempts ({attemptcount})--')
            
            if maxiter > 0 and attemptcount > maxiter:
                print(f'--Reach Maximum Attempts({maxiter}) - Downloading Aborted-- ')
                return -1
        return 1
    except:
        print(f'--Error in Downloading - Downloading Aborted--')
        return -2
    
if __name__ == "__main__":
    capxsup = pd.read_excel('../../data/capxsup.xls')
    ciks = capxsup['cik'].unique()
    
    jsonsavedir = '../../data/edgar/json/download/'
    submissiondir = 'https://data.sec.gov/submissions/'
    statusjsonfname = '../../data/edgar/json/status_test.json'
    jsondict = {'CIK':[],
                'files':[],
                'status':[]
               }

    count = len(jsondict['CIK'])+1
    cikcount = len(ciks)
    
    ###read old json dict
    if os.path.exists(statusjsonfname):
        with open(statusjsonfname) as fp:
            jsondict = json.load(fp)
    
    for cik in ciks:
        # format cik
        cik = f'{cik:0>10d}'
        
        ### check dict
        if cik in jsondict['CIK']:
            continue

        print(f'+++++{count}/{cikcount} - Start Downloading Submission Json Files For {cik}+++++')

        ### download
        jsonfiles = []
        download_status = []
        ### Get recent json file
        print(f'+++ Downloading the Recent Submission Json File +++\n')
        recentjson_url = f'{submissiondir}/CIK{cik}.json'
        recentjsonfname = recentjson_url.split('/')[-1]
        recentjsonfpath = f'{jsonsavedir}/{recentjsonfname}'
        jsonfiles.append(recentjsonfname)

        download_status.append(_download_edgar(recentjson_url, recentjsonfpath))

        sleep(1)
        ### Open recent file
        if os.path.exists(recentjsonfpath):
            if not _check_fail(recentjsonfpath):
                
                openrecent = False
                try:
                    with open(recentjsonfpath) as fp:
                        recentjson = json.load(fp)
                    openrecent = True
                except:
                    download_status[-1] = -3
                
                if openrecent:
                    print('+++ Downloading All Submission Json Files ({})+++\n'.format(len(recentjson['filings']['files'])))
                    for jsondetail in recentjson['filings']['files']:
                        jsonfname = jsondetail['name']
                        json_url = f'{submissiondir}/{jsonfname}'
                        jsonfpath = f'{jsonsavedir}/{jsonfname}'
                        jsonfiles.append(jsonfname)

                        download_status.append(_download_edgar(json_url, jsonfpath))

        jsondict['CIK'].append(cik)
        jsondict['files'].append(jsonfiles)
        jsondict['status'].append(download_status)

        statusjsonfname = '../../data/edgar/json/status_test.json'

        print('+++++Finish downloading {} files for {}, status - {}+++++\n'.format(len(jsonfiles), cik, download_status))

        with open(statusjsonfname, 'w') as fp:
            json.dump(jsondict, fp)

        count += 1