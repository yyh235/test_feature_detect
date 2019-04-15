import os
import sys
import time
sys.path.append(os.path.join(os.path.dirname(__file__)))
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))
from common import utils, log_util
from common.msg_que import MsgQueue
from . import image_etl, ingestor

log_util.debug("Starting ingest main service...")
# declare msg queues
mq = MsgQueue()
for v in utils.msg_queues.values():
    mq.createQueue(v)

# crawler notify queue handler
img_etl = image_etl.ImageETL(mq, utils.msg_queues['crawler_notify'], utils.msg_queues['feature_detect'])
img_etl.start()

# feature detect handler
ingestor_service = ingestor.Ingestor(mq, utils.msg_queues['detect_finish'])
ingestor_service.start()

img_etl.join()
ingestor_service.join()


log_util.error("!!! Ingest main service exited.")