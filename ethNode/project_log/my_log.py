from logzero import setup_logger,LogFormatter



_DEFAULT_FORMAT = '%(color)s[%(name)s: %(levelname)1.1s %(asctime)s %(module)s:%(lineno)d]%(end_color)s %(message)s'
_DATE_FORMATTER="%y-%m-%d %H:%M:%S"

def setup_mylogger(name=None,logfile=None,formatter=LogFormatter(datefmt=_DATE_FORMATTER,fmt=_DEFAULT_FORMAT)):
   return setup_logger(name=name,logfile=logfile,formatter=formatter,maxBytes=3e7)


