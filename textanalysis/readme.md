# Text Analysis for EDGAR Reports

### matching_edgar.py

This scripts is for matching and extract sentences that contains certain keywords. As decimals contain `.`, it makes harder for us to use regular expression to extract sentences directly. 

Our method:
- Read content from a txt file (You can use BeautifulSoup to produce a plain text file)
- Replace all decimals with `<prefix>_<count>` and Keep this information in a dataframe
- Use Regular Expression to extract sentences
- Replace those decimals back with our dataframe created earlier for replacing
