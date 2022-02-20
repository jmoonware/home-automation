import logging
import logging.handlers
from importlib import reload

logFormatString='\t'.join(['%(asctime)s','%(levelname)s','%(message)s'])


def start_logging(level=logging.INFO,filename='log.txt',maxbytes=10000000):
	rfh=logging.handlers.RotatingFileHandler(filename=filename,maxBytes=maxbytes,backupCount=10)
	sh=logging.StreamHandler()
	logging.basicConfig(format=logFormatString,handlers=[sh,rfh],level=level)
	logging.captureWarnings(True)
	logger=logging.getLogger(__name__)
	logger.critical("Logging Started, level={0}".format(level))
	return(logger)

# needed for testing - don't use in app
def reset_logging():
	logging.shutdown()
	reload(logging)
