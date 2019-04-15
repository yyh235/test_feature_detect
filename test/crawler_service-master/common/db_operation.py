import os
import time
import sys
import pymysql

sys.path.append(os.path.join(os.path.dirname(__file__)))
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))
from common import utils, log_util


class DBOperation(object):
    def __init__(self):
        self.connection = self.connect()

    def connect(self):
        try:
            return pymysql.connect(host='rm-j6c4883wd5345860apo.mysql.rds.aliyuncs.com',
                             user='root88',
                             password='fanG882015chinauS',
                             db='image_db',
                             cursorclass=pymysql.cursors.DictCursor)
        except Exception as e:
            log_util.error("DBOperation::connect fail: %s", str(e))

    def execute(self, sql):
        try:
            # check connection alive (if not, ping will reconnect)
            self.connection.ping()
            cursor = self.connection.cursor()
            log_util.debug("DBOperation::execute [%s]", sql)
            cursor.execute(sql)
            self.connection.commit()
        except Exception as e:
            log_util.error("DBOperation::execute fail: %s", str(e))