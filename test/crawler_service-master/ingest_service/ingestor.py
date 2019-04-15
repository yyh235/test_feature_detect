import os
import sys
import time
import datetime
import json
import threading
sys.path.append(os.path.join(os.path.dirname(__file__)))
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))
from common import utils, log_util, image_util, oss2util
from common.msg_que import MsgQueue
from common.db_operation import DBOperation

class Ingestor(threading.Thread):
    def __init__(self, que_manager, get_que_name):
         super(Ingestor, self).__init__()
         self.que_manager = que_manager
         self.get_que_name = get_que_name
         self.db_con = DBOperation()
    
    def get_sub_folder(self, img_path, im_type):
        sub_folder = os.path.join(im_type, datetime.datetime.now().strftime('%Y-%m-%d'))
        return sub_folder

    def ingest_one(self, img_path, im_type):
        try:
            log_util.debug("start to ingest one image: %s", img_path)
            ret = False
            retry = 0
            # upload to oss. img in table is a relative oss storage path
            # retry 3 times
            target = oss2util.get_oss_path(img_path)
            while ret is False and retry < 3:
                ret = oss2util.uploadFile(img_path, target)
                retry += 1
            
            if ret:
                # move file to correct place, named by md5
                file_name = target.split('/')[-1]
                sub_folder = self.get_sub_folder(img_path)
                dest_file_path = os.path.join(utils.MEDIA_ROOT, sub_folder, file_name)

                utils.move_file(img_path, dest_file_path)
                relative_path = os.path.join(sub_folder, file_name)
                # insert image meta to database
                meta = image_util.get_image_meta(img_path)

                # insert into db
                table = 'static_image'
                if im_type == 'gif':
                    table = 'animated_image'
                
                params = []
                values = []
                for k,v in meta.items():
                    params.append(k)
                    values.append(v)
                params.append('create_time')
                values.append(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                #TODO add iamge original name to description

                sql = "insert into %s %s values %s" %(table, str(params), str(values))
                self.db_con.execute(sql)
        except Exception as e:
            log_util.error("ingest image[%s] fail: %s", img_path, str(e))

    def run(self):
        while True:
            try:
                # get task from finish que
                task = self.que_manager.getQue(self.get_que_name)
                if task is None:
                    time.sleep(0.5)
                    continue
                
                log_util.debug("get one task from ingest queue: %s", task)
                # ingest or delete image
                task = json.loads(task.decode())
                if task['ingest']:
                    # ingest image
                    im_type = 'jpg'
                    if image_util.is_gif(task['img_path']):
                        im_type = 'gif'
                    
                    self.ingest_one(task['img_path'], im_type)
                else:
                    # delete image
                    utils.remove_file(task['img_path'])
            except Exception as e:
                log_util.error("Ingestor run error: %s", str(e))