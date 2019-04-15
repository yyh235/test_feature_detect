import os
import sys
import time
import imageio
import json
import faiss

sys.path.append(os.path.join(os.path.dirname(__file__)))
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))
from common import utils, log_util
from common.msg_que import MsgQueue
import imagedna


# ========================== Help Functions =============================
def get_gif_frames(img_path):
    im = imageio.mimread(img_path)
    return len(im)

def duplicated_image(task):
    img_path = task['img_path']
    im_type = 'jpg'
    # gif animated and valid (large than 8 frames)
    if img_path.split('.')[-1].upper() == 'GIF':
        im_type = 'gif'
        if get_gif_frames(img_path)< 8:
            return True
    
    return imagedna.check_image_duplicate(img_path, im_type)


# deploy on image_sv ecs
mq = MsgQueue()
for v in utils.msg_queues.values():
    mq.createQueue(v)

log_util.logger.debug("Starting feature detect service...")
# load feature files from local disk
imagedna.load_static_image_features()
imagedna.load_animated_image_features()

# infinite loop to process feature detect tasks
while True:
    try:
        task = mq.getQue(utils.msg_queues['feature_detect'])
        if task is None:
            time.sleep(0.5)
        
        task = json.loads(task.decode())
        duplicated = duplicated_image(task)
        
        response = {}
        response['ingest'] = True
        if duplicated:
            response['ingest'] = False
            # delete image
            #utils.remove_file(task['img_path'])
        
        response['img_path'] = task['img_path']
        
        mq.putQue(json.dumps(response), utils.msg_queues['detect_finish'])
        faiss.write_index(utils.static_image_index, "static.index")
        faiss.write_index(utils.animated_image_index, "animated.index")
    except Exception as e:
        log_util.logger.error("feature detect error: %s", str(e))
        time.sleep(0.5)


