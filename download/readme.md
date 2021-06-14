# Scripts for downloading various data

### download_jsonfiles.py
For each company (CIK), there is(are) json files that contain a list of files submitted. The main json file is at: `https://data.sec.gov/submissions/[CIK(10)].json`. If there are any other json files, you can get them from the main json file by `['filings']['files']`.

This script is for downloading all submission files for companies in an excel file (in Line44), the excel file should have a column called `cik` that stores company ciks.

P.S.: As we don't use an API so we might fail to access edgar files. We solve that by using a while loop (and check if the file contains string 'Your Request Originates from an Undeclared Automated Tool') - You can set a maximum iteration for attempting downloading by changing `maxiter` parameter in `_download_edgar` function.
