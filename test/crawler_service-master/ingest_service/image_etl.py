import os
import sys
import time
import threading
sys.path.append(os.path.join(os.path.dirname(__file__)))
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))
from common import utils, log_util, image_util
from common.msg_que import MsgQueue

quality_thres = 90

class ImageETL(threading.Thread):
    def __init__(self, que_manager, get_que_name, put_que_name):
         super(ImageETL, self).__init__()
         self.que_manager = que_manager
         self.get_que_name = get_que_name
         self.put_que_name = put_que_name

    def run(self):
        while True:
            try:
                task = self.que_manager.getQue(self.get_que_name)
                if task is None:
                    time.sleep(0.5)
                    continue
                
                image_dir = task['image_dir']
                for f in os.listdir(image_dir):
                    img_path = os.path.join(image_dir, f)
                    md5 = utils.calc_md5(img_path)
                    if utils.get_key(md5, rcli=utils.g_md5_redis) is Not None:
                        # md5 duplicated, remove image and process next
                        utils.remove_file(img_path)
                        continue
                    
                    # md5 unique, record to redis
                    utils.set_key(md5, 1, rcli=utils.g_md5_redis)

                    # image quality check
                    score = image_util.calc_quality(img_path)
                    if score < quality_thres:
                        utils.remove_file(img_path)
                        continue
                    
                    # put to feature detect que
                    task = {}
                    task['img_path'] = img_path
                    self.que_manager.putQue(json.dumps(task), utils.msg_queues['feature_detect'])
            except Exception as e:
                log_util.error("ImageETL run error: %s", str(e))
                time.sleep(0.5)