import logging

def _setlogger_(
    module='main',
    logfname='main.log',
    loglevel=logging.DEBUG,
    streamlevel=logging.DEBUG,
    filelevel=logging.INFO,
    ):
    '''
    Settings for the logger
    '''

    logger = logging.getLogger(module)
    logger.setLevel(loglevel)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    ### stream logger handle
    console = logging.StreamHandler()
    console.setLevel(streamlevel)
    console.setFormatter(formatter)
    logger.addHandler(console)

    ### file logger handle
    file = logging.FileHandler(logfname, 'w')
    file.setLevel(filelevel)
    file.setFormatter(formatter)
    logger.addHandler(file)
