# -*- coding: utf-8 -*-
import oss2
import hashlib
import os
import sys


from common.utils import clientId, clientSecret, calc_md5
from common.log_util import logger

auth = oss2.Auth(clientId, clientSecret)
endpoint_cn = 'oss-cn-shanghai.aliyuncs.com'
bucket_name_cn = 'studio88images'

bucket_cn = oss2.Bucket(auth, endpoint_cn, bucket_name_cn)

# oss related config
OSS_ANIMATED_STICKER_DIR = "asset/gif/"
OSS_STATIC_STICKER_DIR = "asset/jpg/"

def get_oss_path(file_path):
    fmd5 = calc_md5(file_path)
    if file_path.split('.')[-1].upper() == 'GIF':
        oss_path = OSS_ANIMATED_STICKER_DIR + fmd5 + '.gif'
    else:
        oss_path = OSS_STATIC_STICKER_DIR + fmd5 + '.jpg'
    
    return oss_path

def get_url(name, type='cn'):
    #return 'http://img.fang88.com/' + name
    return 'http://studio88img.fang88.com/' + name
    #if type == 'cn':
    #    return 'https://' + bucket_name_cn + '.' + endpoint_cn + '/' + name
    #else:
    #    return 'https://' + bucket_name_us + '.' + endpoint_us + '/' +  name

def upload_content(target, content):
    headers = {'Cache-Control': 'public,max-age=2592000'}
    bucket_cn.put_object(target, content, headers)
    logger.debug('upload content to oss')

def uploadContent(fd, target):
    headers = {'Cache-Control': 'public,max-age=2592000'}
    ret = bucket_cn.put_object(target, fd.open(), headers) and bucket_us.put_object(target, fd.open(), headers)
    return ret.status == 200

def uploadFile(full_file_path, target_file_name):
    #headers = {'Cache-Control': 'public,max-age=2592000'}
    try:
        #with open ('/home/skygon/Downloads/a251c2f11e0ee85260577a2ede685e18.jpg', 'rb') as fobject:
        ret_cn = ""
        with open (full_file_path, 'rb') as fobject:
            ret_cn = bucket_cn.put_object(target_file_name, fobject)
            logger.debug('upload file[%s] to cn-oss as %s', full_file_path, target_file_name)
        
        return ret_cn.status == 200
    except Exception as e:
        return False

def delete_object(target):
    try:
        bucket_cn.delete_object(target)
    except Exception as e:
        logger.error("OSS delete file fail: %s", str(e))
        return False

def OSS_exists(full_file_path):
    return bucket_cn.object_exists(full_file_path) and bucket_us.object_exists(full_file_path)
    
def md5(file_file_path):
    with open(file_file_path, 'rb') as f:
        fcont=f.read()
        fmd5=hashlib.md5(fcont)  
        return fmd5.hexdigest()

def inmemoryMD5(f):
    fcont=f.chunks()
    fmd5=hashlib.md5(fcont)
    return fmd5.hexdigest()


if __name__ == "__main__":
    #md5 = md5('/home/skygon/Downloads/custom_service.jpg')
    #target = md5 + ".jpg"
    target = 'upload/2018/04/27/1.png'
    uploadFile('/home/skygon/work/server/version3/f88_back/ng_server/media/upload/2018/04/27/1.png', target)
