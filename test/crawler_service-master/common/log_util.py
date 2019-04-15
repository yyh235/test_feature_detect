import os
import logging

# logger config
log_path = os.path.join(os.path.dirname(__file__), os.pardir, 'logs', 'debug.log')
logger = logging.getLogger('crawler')
hdlr = logging.FileHandler(log_path)
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logger.setLevel(logging.DEBUG)