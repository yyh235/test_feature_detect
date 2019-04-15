from random import randrange
import argparse
import cv2
import glob
import faiss
# for no X-display system
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import numpy as np
import os
import sys
import json
import time
import datetime
import hashlib
import tensorflow as tf
import tensorflow_hub as hub

sys.path.append(os.path.join(os.path.dirname(__file__)))
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))
from common import utils, log_util


def create_module_graph(module_spec):
    """Creates a graph and loads Hub Module into it.

    Args:
      module_spec: the hub.ModuleSpec for the image module being used.

    Returns:
      graph: the tf.Graph that was created.
      bottleneck_tensor: the bottleneck values output by the module.
      jpeg_data for the node to feed JPEG data into
    """
    height, width = hub.get_expected_image_size(module_spec)
    input_depth = hub.get_num_image_channels(module_spec)
    with tf.Graph().as_default() as graph:
        jpeg_data = tf.placeholder(tf.string, name='DecodeJPGInput')
        decoded_image = tf.image.decode_jpeg(jpeg_data, channels=input_depth)
        # Convert from full range of uint8 to range [0,1] of float32.
        decoded_image_as_float = tf.image.convert_image_dtype(decoded_image, tf.float32)
        decoded_image_4d = tf.expand_dims(decoded_image_as_float, 0)
        resize_shape = tf.stack([height, width])
        resize_shape_as_int = tf.cast(resize_shape, dtype=tf.int32)
        resized_image = tf.image.resize_bilinear(decoded_image_4d, resize_shape_as_int)
        m = hub.Module(module_spec)
        bottleneck_tensor = m(resized_image)
    return graph, bottleneck_tensor, jpeg_data

def crop_center_square(frame):
    y, x = frame.shape[0:2]
    min_dim = min(y, x)
    start_x = (x // 2) - (min_dim // 2)
    start_y = (y // 2) - (min_dim // 2)
    return frame[start_y:start_y + min_dim, start_x:start_x + min_dim]

def load_video(path, max_frames=0, resize=(224, 224)):
    cap = cv2.VideoCapture(path)
    frames = []
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            frame = crop_center_square(frame)
            frame = cv2.resize(frame, resize)
            frame = frame[:, :, [2, 1, 0]]
            frames.append(frame)

            if len(frames) == max_frames:
                break
    finally:
        cap.release()
    frames = np.array(frames) / 255.0
    return frames


# load static features from local disk
def load_static_image_features():
    try:
        static_feature = []
        for parent, _, filenames in os.walk(utils.static_image_feature_dir):
            log_util.logger.debug("loading static features from %s", parent)
            for f in filenames:
                feature_path = os.path.join(parent, f)
                if feature_path[-3:] == 'txt':
                    feature = np.float32(np.loadtxt(feature_path)).reshape(utils.static_dimension)
                    static_feature.append(feature)
        static_feature = np.array(static_feature)
        assert not utils.static_image_index.is_trained
        utils.static_image_index.train(static_feature)
        assert utils.static_image_index.is_trained
        utils.static_image_index.add(static_feature)

        log_util.logger.debug("Total %s static image features loaded.", utils.static_image_index.ntotal)
    except Exception as e:
        log_util.logger.error("tensorlfow load static features error: %s", str(e))
        raise e

# load animated features from local disk
def load_animated_image_features():
    try:
        animated_image_features = []
        for parent, _, filenames in os.walk(utils.animated_image_feature_dir):
            log_util.logger.debug("loading animated features from %s", parent)
            for f in filenames:
                feature_path = os.path.join(parent, f)
                if feature_path[-3:] == 'txt':
                    feature = np.float32(np.loadtxt(feature_path)).reshape(utils.animaed_dimension)
                    animated_image_features.append(feature)
        animated_image_features = np.array(animated_image_features)
        assert not utils.animated_image_index.is_trained
        utils.animated_image_index.train(animated_image_features)
        assert utils.animated_image_index.is_trained
        utils.animated_image_index.add(animated_image_features)

        log_util.logger.debug("Total %s animated image features loaded.", utils.animated_image_index.ntotal)
    except Exception as e:
        log_util.logger.error("tensorlfow load animated features error: %s", str(e))
        raise e


def extract_jpg_feature(image_path):    
    tfhub_module = 'https://tfhub.dev/google/imagenet/inception_v3/feature_vector/1'
    module_spec = hub.load_module_spec(tfhub_module)
    graph, bottleneck_tensor, jpeg_tensor = create_module_graph(module_spec)
    
    with tf.Session(graph=graph) as sess:
        init = tf.global_variables_initializer()
        sess.run(init)
        
        image_data = tf.gfile.GFile(image_path, 'rb').read()
        try:
            bottleneck_values = sess.run(bottleneck_tensor,
                                            {jpeg_tensor: image_data})
            bottleneck_values = np.squeeze(bottleneck_values)
            #np.savetxt(feature_path, bottleneck_values)
            return bottleneck_values.reshape(1, utils.static_dimension)

        except Exception as e:
            log_util.logger.error("extract feature of jpg[%s] fail: %s", image_path, str(e))
            return None


def extract_gif_feature(image_path):
    with tf.Graph().as_default() as graph:
        i3d = hub.Module('https://tfhub.dev/deepmind/i3d-kinetics-600/1')
        input_placeholder = tf.placeholder(shape=(None, None, 224, 224, 3), dtype=tf.float32)
        bottleneck_tensor = i3d(input_placeholder)
        with tf.Session(graph=graph) as sess:
            init = tf.global_variables_initializer()
            sess.run(init)
            frames = load_video(image_path)

            model_input = np.expand_dims(frames, axis=0)
            try:
                bottleneck_values = sess.run(bottleneck_tensor,
                                                {input_placeholder: model_input})
                bottleneck_values = np.squeeze(bottleneck_values)
                if not np.isnan(bottleneck_values).any():
                    return bottleneck_values.reshape(1,utils.animaed_dimension)
                else:
                    return None
            except Exception as e:
                log_util.logger.error("extract feature of gif[%s] fail: %s", image_path, str(e))
                return None



def save_feature(image_md5, feature, im_type):
    # save feature to local disk
    # determine sub-folder
    sub_folder = datetime.datetime.now().strftime('%Y-%m-%d')
    file_name = image_md5 + '.txt'
    if im_type == 'gif':
        dest_dir = os.path.join(utils.animated_image_feature_dir, sub_folder)
    else:
        dest_dir = os.path.join(utils.static_image_feature_dir, sub_folder)

    os.makedirs(dest_dir, exist_ok=True)
    feature_path = os.path.join(dest_dir, file_name)
    np.savetxt(feature_path, feature)



def detect_static_feature(feature):
    # detect wether feature is duplicated in index
    utils.static_image_index.nprobe = 5
    D, I = utils.static_image_index.search(feature, 1)
    # return score
    return D[0][0]

def detect_animated_feature(feature):
    utils.animated_image_index.nprobe = 5
    D, I = utils.animated_image_index.search(feature, 1)
    # return score
    return D[0][0]

def check_image_duplicate(img_path, im_type):
    try:
        image_md5 = utils.calc_md5(img_path)

        if im_type == 'gif':
            feature = extract_gif_feature(img_path)
            score = detect_animated_feature(feature)
        else:
            feature = extract_jpg_feature(img_path)
            score = detect_static_feature(feature)

        duplicated = True
        if score > utils.duplicate_threshold:
            duplicated = False
            if im_type == 'gif':
                utils.animated_image_index.add(feature)
            else:
                utils.static_image_index.add(feature)

            # save feature to local disk
            save_feature(image_md5, feature, im_type)

        # return duplicate or not
        return duplicated
    except Exception as e:
        log_util.logger.error("check image duplicate fail: %s", str(e))
        return True