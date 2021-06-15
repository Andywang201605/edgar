import DOWNLOAD
import pandas as pd
import pickle

import argparse

def _download_dataframe(dfpath, filetype, urlcol, fnamecol, include_basedir=False, basedir=''):
    '''
    Download Files from dataframe, which contains url and file name
    
    Parameters:
    ------------
    dfpath: str
        Path for your dataframe
    filetype: str
        Indicating the dataframe file type, can be pickle, excel
    urlcol: str
        Column for url
    fnamecol: str
        Column for file names
    include_basedir: bool, False by default
        If True, basedir is included in file name
    basedir: str, an empty string by default
        The directory for downloading all files
        
    Returns:
    ------------
    None
    '''
    assert filetype in ['pickle', 'excel'], f'Your file type should be either `pickle` or `excel`, but {filetype} given.'
    
    if filetype == 'pickle':
        df = pd.read_pickle(dfpath)
    if filetype == 'excel':
        df = pd.read_excel(dfpath)
        
    if basedir == '':
        statusdffname = './downloaddf_status.pickle'
        statuslstfname = './download_status.pickle'
    else:
        statusdffname = f'{basedir}/downloaddf_status.pickle'
        statuslstfname = f'{basedir}/download_status.pickle'
        
    download_status = []
    download_count = 1; rowcount = len(df)
    for i, row in df.iterrows():
        ### print info
        print(f'{download_count}/{rowcount} - Start Downloading'.center(80, '+'))
        download_url = row[urlcol]
        download_fname = row[fnamecol]
        print(f'[info] URL:{download_url}')
        print(f'[info] PATH:{download_fname}')
        if not include_basedir:
            download_fname = f'{basedir}/{download_fname}'
            
        download_status.append(DOWNLOAD._download_edgar(download_url, download_fname))
        download_count += 1
        
        with open(statuslstfname, 'wb') as fp:
            pickle.dump(download_status, fp)
            
        print(f'Finished Downloading! Status - {download_status[-1]}'.center(80, '+'))
        
    df['download_status'] = download_status
    df.to_pickle(statusdffname)
       
        
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Download edgar files from an excel file or pickle file')
    parser.add_argument('dfpath', type=str, help='Path for your DataFrame')
    parser.add_argument('--t', type=str, default='excel', choices={'excel','pickle'}, help='Type of your DataFrame File (allowed values: `excel` and `pickle`)')
    parser.add_argument('--url', type=str, required=True, help='Column name for urls')
    parser.add_argument('--file', type=str, required=True, help='Column name for filenames')
    parser.add_argument('--include_basedir', type=int, default=0, choices={0, 1}, help='1 If your filenames include basedir, 0 if not')
    parser.add_argument('--base', type=str, default='', help='The base directory for downloading files')
    
    args = parser.parse_args()
    
    _download_dataframe(args.dfpath, args.t, args.url, args.file, bool(args.include_basedir), args.base)