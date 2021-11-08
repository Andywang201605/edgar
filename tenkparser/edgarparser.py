### attempt to parsing 10-k html file
from bs4 import BeautifulSoup
import logging
import pickle
import os
import re

class TENKPARSER:
    '''
    Object for parsing 10-k html file
    '''
    def __init__(
        self,
        tenkhtmlpath,
        workdir,
        ):
        '''
        initialize TENKPARSER object

        Params:
        ----------
        tenkhtmlpath: str
            path for saving 10-k file
        workdir: str
            directory for saving various ~temp files
        '''
        self.logger = logging.getLogger('edgar.tenk')
        self.workdir = workdir
        if not os.path.exists(self.workdir):
            os.makedirs(self.workdir)
        self.logger.info(f'setting work directory to {self.workdir}')
        self.htmlpath = tenkhtmlpath
        ### run _souphtml_ function
        self._souphtml_()
        ### make a status dictionary for checking purpose
        
    def _souphtml_(self):
        '''parsing the html file to a beautiful soup'''
        self.logger.info('parsing the html file into a beautifulsoup object...')
        with open(self.htmlpath) as fp:
            self.soup = BeautifulSoup(fp.read(), 'lxml')

    def _finditemhref_(self, scorethreshold = 1):
        '''finding all hyperlinks in the file and match to item7/7A/8'''
        self.logger.info('finding all hyperlinks in the html file...')
        ataglst = self.soup.findAll('a')
        self.logger.debug('{} a tags found in the html file...'.format(len(ataglst)))

        cutdict = {'I7':[], 'I7A':[], 'I8':[]}
        #check item7/7A/8 from all ataglst
        # only keep html tag above the score threshold...
        self.logger.info('finding item 7/7A/8 tags in all atags...')
        for atag in ataglst:
            score = self._matchitemseven_(atag)
            if score > scorethreshold: cutdict['I7'].append(atag)
            score = self._matchitemeight_(atag)
            if score > scorethreshold: cutdict['I8'].append(atag)
            score = self._matchitemsevenA_(atag)
            if score > scorethreshold: cutdict['I7A'].append(atag)
        self.logger.info(
            '{} item7 tags found, {} item7A tags found and {} item8 tags'.format(
                len(cutdict['I7']),
                len(cutdict['I7A']),
                len(cutdict['I8'])
                )
            )
        self.logger.info('saving matched dictionary to $workdir...')
        self.hreftagmatch = cutdict
        with open(f'{self.workdir}/hrefmatch.dict.pickle', 'wb') as fp:
            pickle.dump(self.hreftagmatch.__str__(), fp)

    def _matchscore_(self, repats, weights, htmltag):
        '''
        evaluating for a string to match the pattern in `repats`
        each weight is given in `weights`
        '''
        if not isinstance(htmltag, str):
            htmltag = htmltag.__str__()

        self.logger.debug(f'evaluating scores for htmltag - {htmltag}...')
        score = 0
        for repat, weight in zip(repats, weights):
            if len(re.findall(repat, htmltag)) > 0:
                score += weight
        self.logger.debug(f'score: {score}')
        return score

    def _matchitemseven_(self, htmltag, weights=[3,1,1]):
        ''' 
        check if item seven is in html tag
        Things we need to consider - 
        ``item<space>7''
        ``Management's discussion and analysis of financial condition and results of operations''
        '''
        repats = [
            re.compile(r'item\s*7[^A-Z]', re.IGNORECASE),
            re.compile(r'discussion\s*and\s*analysis', re.IGNORECASE),
            re.compile(r'financial\s*condition', re.IGNORECASE),
        ]

        ### give the score of a htmltag to be the target tag
        return self._matchscore_(repats, weights, htmltag)

    def _matchitemsevenA_(self, htmltag, weights=[3,1,1]):
        '''
        check if item sevenA is in the html tag
        Things we need to consider - 
        ``item<space>7A''
        ``Quantitative and Qualitative Disclosures about Market Risk''
        '''
        repats = [
            re.compile(r'item\s*7A', re.IGNORECASE),
            re.compile(r'quantitative\s*and\s*qualitative\s*disclosures', re.IGNORECASE),
            re.compile(r'market\s*risk', re.IGNORECASE),
        ]

        return self._matchscore_(repats, weights, htmltag)

    def _matchitemeight_(self, htmltag, weights=[3,1,1]):
        '''
        check if item eight is in the html tag
        Things we need to consider - 
        ``item<space>8''
        ``
        '''
        repats = [
            re.compile(r'item\s*8[^A-Z]', re.IGNORECASE),
            re.compile(r'financial\s*statements', re.IGNORECASE),
            re.compile(r'supplementary\s*data', re.IGNORECASE),
        ]

        return self._matchscore_(repats, weights, htmltag)

    def _extractanchor_(self, atag):
        '''
        extract href from a tag... (all strings after the hashtag)
        '''
        rawanchor = atag.attrs['href']
        hashtagidx = rawanchor.find('#')
        return rawanchor[hashtagidx+1:]

    def _finditemanchor_(self):
        '''
        extract all possible anchors from self.hreftagmatch
        '''
        checkmessage = ''
        self.itemanchor = {}
        self.logger.info('extracting item name/id from atags...')
        for item in self.hreftagmatch:
            tmpanchors = []
            atags = self.hreftagmatch[item]
            for atag in atags:
                tmpanchors.append(self._extractanchor_(atag))
            tmpanchors = list(set(tmpanchors))
            self.logger.info('{} id/name has been found for {}...'.format(len(tmpanchors), item))
            if len(tmpanchors) > 1 or len(tmpanchors) == 0: checkmessage += f'{item},'
            self.itemanchor[item] = tmpanchors

        self.logger.info('saving item anchor to $workdir...')
        with open(f'{self.workdir}/itemanchor.dict.pickle', 'wb') as fp:
            pickle.dump(self.itemanchor, fp)
        
        if checkmessage:
            self.logger.warning('please check item anchor manually... check messages have been saved in $workdir...')
            with open(f'{self.workdir}/CHECK_ITEM_ANCHOR.LOG', 'w') as fp:
                fp.write(checkmessage)

    def _findanchortag_(self):
        '''
        find anchor tag from self.soup...
        '''
        self.logger.info(f'finding anchor tags in the html file...')
        checkmessage = ''
        self.anchortag = {}
        for item in self.itemanchor:
            self.anchortag[item] = []
            if len(self.itemanchor[item]) == 0:
                continue
            anchor_id = self.itemanchor[item][0]
            ### searching for name first
            nametags = self.soup.find_all(attrs={'name':anchor_id})
            nametags = [i.__str__() for i in nametags]
            idtags = self.soup.find_all(attrs={'id':anchor_id})
            idtags = [i.__str__() for i in idtags]
            ### tmptags
            tmptags = []
            tmptags.extend(nametags); tmptags.extend(idtags)
            ### checkmessage
            if len(tmptags) == 0 or len(tmptags) > 1: checkmessage += f'{item},'
            self.anchortag[item].extend(tmptags)

        self.logger.info('saving item anchor tag to $workdir...')
        with open(f'{self.workdir}/itemanchortag.dict.pickle', 'wb') as fp:
            pickle.dump(self.anchortag, fp)
        
        if checkmessage:
            self.logger.warning('please check anchor tags manually... check messages have been saved in $workdir...')
            with open(f'{self.workdir}/CHECK_ITEM_ANCHOR_TAG.LOG', 'w') as fp:
                fp.write(checkmessage)

    def _findanchoridx_(self):
        '''
        find string index for a given anchor dictionary
        '''
        self.logger.info('finding index for given anchors in different sections...')
        checkmessage = ''
        self.anchoridx = {}
        for item in self.anchortag:
            ### finding index for a given anchor
            if len(self.anchortag[item]) == 0:
                checkmessage += f'{item},'
                self.logger.info(f'no tag found for {item}')
                continue
            elif len(self.anchortag[item]) > 1:
                checkmessage += f'{item},'

            idx = self.soup.__str__().find(self.anchortag[item][0])
            if idx == -1:
                checkmessage += f'{item}_find,'
            else:
                self.anchoridx[item] = idx

        self.logger.info('saving item anchor index to $workdir...')
        with open(f'{self.workdir}/itemanchorindex.dict.pickle', 'wb') as fp:
            pickle.dump(self.anchoridx, fp)
        
        if checkmessage:
            self.logger.warning('please check anchor indexes manually... check messages have been saved in $workdir...')
            with open(f'{self.workdir}/CHECK_ITEM_ANCHOR_INDEX.LOG', 'w') as fp:
                fp.write(checkmessage)
            


        




    

        




        