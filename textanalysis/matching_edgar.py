import pandas as pd
import re

### compile the format
class _Numberiter(object):
    def __init__(self, start = 1, prefix='NUMBERREBMUN'):
        self.count = start - 1
        self.prefix = prefix
        
    def __call__(self, match):
        self.count += 1
        return f"{self.prefix}_{self.count}"


def _Rereplacenumber(content, prefix='NUMBERREBMUN'):
    '''
    Replace all number(with decimals) into a string without decimal
    
    and return a dataframe that containes the replacement information
    '''
    pattern = re.compile(r'\d+\.\d+')
    ### make dataframe for replacement information
    count = 1
    replacementdf = []
    for match in pattern.finditer(content):
        replacementdf.append((f'{prefix}_{count}', match.group()))
        count += 1
    replacementdf = pd.DataFrame(replacementdf, columns=['REWORD', 'ORIGIN_NUM'])
    ### replacement the data
    newcontent = re.sub(pattern, _Numberiter(prefix=prefix), content)
    return newcontent, replacementdf
    
    

def _Rekeywordsentence(keyword):
    '''
    A string for Re compiling a sentence that contains keywords
    '''
    ### add \s* between single words
    wordpart = r'\s*'.join(keyword.split())
    ### start and end
    stopword = r'.!?\n'
    return r'[^{}]*{}[^{}]*[{}]'.format(stopword, wordpart, stopword, stopword)

def _RekeywordsPattern(keywords):
    patterns = []
    for keyword in keywords:
        patterns.append(_Rekeywordsentence(keyword))
    return '|'.join(patterns)

def _replaceSUBstr(sentence, replacementdf, prefix='NUMBERREBMUN'):
    '''
    Change back to a number 
    '''
    ### We here use the most unefficient way to do so
    if sentence.count(prefix) != 0:
        prefixpattern = re.compile(r'{}_[\d]'.format(prefix))
        SUBstrings = re.findall(prefixpattern, sentence)
        for substring in SUBstrings:
            ### get the number back
            number = replacementdf[replacementdf['REWORD'] == substring].iloc[0]['ORIGIN_NUM']
            sentence = sentence.replace(substring, str(number))
            
    return sentence

def _MatchSentences(content, keywordspattern, prefix='NUMBERREBMUN'):
    ### replace the number first
    newcontent, replacementdf = _Rereplacenumber(content)
    ### Find sentences that contain our keywords
    rawsentences = re.findall(keywordspattern, newcontent)
    
    ### Clean these sentences with dataframe
    sentences = []
    for RAWsentence in rawsentences:
        sentences.append(_replaceSUBstr(RAWsentence, replacementdf))
        
    return sentences

if __name__ == '__main__':
    matchingdf = pd.read_pickle('./Matching_Files.pickle')

    longlist = []
    with open('../../data/edgar/edgar_keywords/keyword_list_long_091917.txt') as fp:
        fplines = fp.readlines()
        for fpline in fplines:
            wordraw = fpline.strip()
            longlist.append(wordraw)

    keywordspatternstr = _RekeywordsPattern(longlist)
    pattern = re.compile(keywordspatternstr, re.IGNORECASE)
    
    sentence_numbers = []
    notes = []
    for i, row in matchingdf.iterrows():
        print('*'*80)
        print('Matching Sentences From {}'.format(row['fileidx']))
        itemsevenfile = '{}/Item7.txt'.format(row['itemseven_folder'])
        with open(itemsevenfile, encoding='utf-8') as fp:
            content = fp.read()
        try:
            sentences = _MatchSentences(content, pattern)
            sentences_df = pd.DataFrame(sentences, columns=['sentences'])
            sentences_df.to_pickle('{}/longsentence.pickle'.format(row['itemseven_folder']))
            sentence_count = len(sentences)
            note = ''
        except Exception as Excpt:
            sentence_count = -1
            note = Excpt

        if note:
            print(f'NOTE:{note}!!!') 
        else:
            print(f'Matching {sentence_count} sentences!')

        sentence_numbers.append(sentence_count)
        notes.append(note)

    matchingdf['sentence_count'] = sentence_numbers
    matchingdf['note'] = notes

    matchingdf.to_pickle('./Matching_status.pickle')
