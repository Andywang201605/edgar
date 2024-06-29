from utils import _setlogger_

import pandas as pd

import requests
import logging
import json
import os

from time import sleep
from numpy import random


def _download_url_(url, path, overwrite=True):
    '''
    Download file from a given `url` and save it to the `path` in your computer

    Params:
    ----------
    url: str
    path: str
    '''
    logger = logging.getLogger('edgar.download')

    headers = {"User-Agent": "Andy Wang (ztwang201605@gmail.com)"}

    ### check if the path has already been existed
    if os.path.exists(path):
        logger.debug(f'file {path} already existed...')
        if overwrite == True:
            logger.warning('overwriting the file...')

    logger.info(f'downloading the file from - {url}')
    r = requests.get(url, headers=headers)
    with open(path, 'wb') as fp:
        fp.write(r.content)
    logger.info('file downloaded successfully...')
    return True

def _check_fail_(path, drop=True):
    '''
    Check if the url was failed to access due to edgar limit, delete the file if `drop` is True
    '''
    logger = logging.getLogger('edgar.download')

    with open(path) as fp:
        content = fp.read()

    fail = 'Your Request Originates from an Undeclared Automated Tool' in content
    if fail:
        logger.info('The downloading was failed...')
        if drop:
            logger.info(f'removing the failed file - {path}')
            os.remove(path)
    return fail

class DOWNLOADER:
    '''
    object for downloading various ``edgar'' files 

    Initialize the object
    Params:
    ----------
    url: str
        url for the file
    path: str
        path for saving the file
    maxiter: int
        maximum iteration for trying downloading the file, -1 for with no upper limit (not recommended)
    overwrite: bool
        whether to overwrite the file or not
    drop: bool
        whether to delete the file if it was failed    
    '''
    def __init__(
        self,
        url,
        path,
        maxiter=-1,
        overwrite=True,
        drop=True,
        sleep=2,
        ):
        self.logger = logging.getLogger('edgar.download')
        self.url = url; self.path = path
        self.maxiter = maxiter
        self.overwrite = overwrite; self.drop = drop
        self.sleep = sleep

        ### initial check
        self._checkdir_()

    def _checkdir_(self):
        '''
        check if the directory has been created already, make new directory if possible
        '''
        if self.path[-1] == '/':
            self.logger.error(f'{self.path} is not a correct file path...')
            raise ValueError(f'{self.path} is not a correct file path... Aborted...')

        pathdir = '/'.join(self.path.split('/')[:-1])
        if not os.path.exists(pathdir):
            self.logger.info(f'making new directory - {pathdir}...')
            os.makedirs(pathdir)

    def _iterdownload_(self):
        '''
        download the file iteratively 
        '''
        download_attempt = 0
        self.logger.info(f'downloading iteration - {download_attempt}')
        _download_url_(self.url, self.path, overwrite=self.overwrite)
        
        
        while _check_fail_(self.path, drop=self.drop):
            sleep(random.uniform(self.sleep, self.sleep + 2))

            download_attempt += 1
            self.logger.info(f'downloading iteration - {download_attempt}')
            _download_url_(self.url, self.path, overwrite=self.overwrite)

            if self.maxiter > 0 and download_attempt > self.maxiter:
                self.logger.info(f'have reached maximum attempts ({self.maxiter})... Aborted...')
                return -1
        return 1

class COMPANYFILINGJSON:
    '''
    object for manipulating json files for a given company (i.e.: CIK)
    '''
    def __init__(
        self,
        cik,
        jsonpath,
        ):
        self.logger = logging.getLogger('edgar.download')
        self.cik = self._formatcik_(cik)
        self.jsonpath = jsonpath
        self.logger.info(f'working on company CIK{self.cik}... saving data to {self.jsonpath}...')
        ### make directory for jsonpath
        if not os.path.exists(self.jsonpath):
            os.makedirs(self.jsonpath)
        ### several lists initialization
        self.jsondflst = []
        self.jsonsublst = []
        ### running downloading and parsing
        self._download_parse_()

    def _formatcik_(self, cik):
        '''formatting the cik to the length of 10'''
        return '{:0>10}'.format(cik)

    def _parse_recent_(self):
        recentfile = f'{self.jsonpath}/CIK{self.cik}.json'
        self.logger.info(f'loading recent json file from {recentfile}...')

        with open(recentfile) as fp:
            recent_sub = json.load(fp)

        ### extracting files from recent submission
        self.logger.info('adding recent filings dataframe...')
        self.jsondflst.append(pd.DataFrame(recent_sub['filings']['recent']))

        self.logger.info(f'finding other json files for CIK{self.cik}...')
        for jsonsub in recent_sub['filings']['files']:
            self.jsonsublst.append(jsonsub['name'])
        self.logger.info('{} other json submission files found...'.format(len(self.jsonsublst)))

    def _parse_history_(self, fname):
        '''parse historical json submission files'''

        self.logger.info(f'loading submission files from {fname}')
        with open(fname) as fp:
            hist_sub = json.load(fp)

        self.jsondflst.append(pd.DataFrame(hist_sub))

    def _download_parse_(self):
        '''download files and parsing them into a dataframe'''
        self.logger.info('starting downloading all relavent submission json files and parsing to dataframe...')
        submission_dir_url = 'https://data.sec.gov/submissions'

        ### download recent json
        self.logger.info('downloading recent submission file...')
        downloader = DOWNLOADER(
            url = f'{submission_dir_url}/CIK{self.cik}.json',
            path = f'{self.jsonpath}/CIK{self.cik}.json',
            maxiter = 5,
            sleep = 2,
        )
        downloader._iterdownload_()
        ### analyzing recent json
        self._parse_recent_()

        ### download historical json
        self.logger.info('downloading historical submission files...')
        for histsub in self.jsonsublst:
            sleep(2) # rest for a few seconds
            downloader = DOWNLOADER(
                url = f'{submission_dir_url}/{histsub}',
                path = f'{self.jsonpath}/{histsub}',
                maxiter = 5,
                sleep = 2,
            )
            downloader._iterdownload_()
        ### analyzing historical json
        for histsub in self.jsonsublst:
            self._parse_history_(f'{self.jsonpath}/{histsub}')

        ### concatenating dataframes
        self.logger.info('concatenating dataframes...')
        self.jsondataframe = pd.concat(self.jsondflst).reset_index(drop=True)
        self.logger.info('saving combined dataframe...')
        self.jsondataframe.to_pickle(f'{self.jsonpath}/CIK{self.cik}.submission.all.pickle')

if __name__ == '__main__':
    _setlogger_(module='edgar', logfname='test.log')
    COMPANYFILINGJSON(12927, './data/test/')

        


        



    
        


            







