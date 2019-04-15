import os
import sys
import hashlib
import redis
# hack for faiss as it was installed by conda, not a regular system-wide python dist.
sys.path.append("/Users/tonyyoung/anaconda3/envs/tensorflow/lib/python3.7/site-packages")
import faiss
from common import log_util

# define msg queue names
msg_queues = {}
msg_queues['crawler_notify'] = "CRAWLER_NOTIFY_QUE"
msg_queues['feature_detect'] = "FEATURE_DETECT_QUE"
msg_queues['detect_finish'] = "FEATURE_DETECT_FINISH_QUE"


# feature detect related config
static_image_feature_dir = "/Users/tonyyoung/test/feature/inception/image"
animated_image_feature_dir = "/Users/tonyyoung/test/feature/600"
static_dimension = 2048
animaed_dimension = 600
nlist = 20  # Number of clustering centers
quantizer_static = faiss.IndexFlatL2(static_dimension)
quantizer_animaed = faiss.IndexFlatL2(animaed_dimension)

static_image_index = faiss.IndexIVFFlat(quantizer_static, static_dimension, nlist, faiss.METRIC_L2)
animated_image_index = faiss.IndexIVFFlat(quantizer_animaed, animaed_dimension, nlist, faiss.METRIC_L2)

'''static_image_index = faiss.IndexFlatL2(static_dimension)
animated_image_index = faiss.IndexFlatL2(animaed_dimension)'''

duplicate_threshold = 10

# OSS account info. 
clientId = 'LTAIW5NjZnlwWIjr'
clientSecret = 'BWajgSlWW32EtuQbTmDywvSf7pvwuj'

MEDIA_ROOT = "/home/ubuntu/workspace/smile_sv/smile/media"

# ========================= Redis operations ========================
'''sticker_md5 = "sticker_md5"
g_common_redis = redis.Redis('127.0.0.1', 6379)
g_md5_redis = redis.Redis('127.0.0.1', 6379, db=1)

def set_key(k, v, ttl=None, rcli=g_common_redis):
    try:
        rcli.set(k, v)
        if ttl is not None:
            rcli.expire(k, ttl)
    except Exception as e:
        log_util.error('redis set key fail: %s', str(e))

def get_key(k, rcli=g_common_redis):
    try:
        return rcli.get(k)
    except Exception as e:
        log_util.error('redis get key fail: %s', str(e))

def get_hkey(table, k, rcli=g_md5_redis):
    return rcli.hget(table, k)

def set_hkey(table, k, v, ttl=None, rcli=g_md5_redis):
    rcli.hset(table, k, v)
    if ttl is not None:
        rcli.expire(k, ttl)'''


# ========================== Help functions =======================================
def remove_file(file_path):
    try:
        cmd = "rm " + "\"" + file_path + "\""
        os.system(cmd)
    except Exception as e:
        log_util.error("remove file[%s] error: %s", file_path, str(e))

def move_file(src_file, dest_file):
    try:
        cmd = "mv " + "\"" + src_file + "\"" + dest_file
        os.system(cmd)
    except Exception as e:
        log_util.error("move file[%s] error: %s", cmd, str(e))

def calc_md5(file_path):
    with open(file_path, 'rb') as f:
        fcont=f.read()
        fmd5=hashlib.md5(fcont)  
        return fmd5.hexdigest()

def check_md5_exist(file_path):
    pass