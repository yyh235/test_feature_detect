import os
import sys
import subprocess
import cv2

def calc_quality(full_path):
    try:
        cmd = 'identify -format "%Q \n" ' + "\"" + full_path + "\""
        print(cmd)
        score = int(subprocess.getoutput(cmd))
        return score
    except Exception as e:
        print("calc quality fail: %s" %str(e))
        return 0


def get_img_frq_score(img_path):
	image = cv2.imread(img_path);
	img2gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
	imageVar = cv2.Laplacian(img2gray, cv2.CV_64F).var()

	return imageVar


def image_etl(img_path, t1=500, t2=90):
    img = cv2.imread(img_path)
    if img is None:
        return False
    
    shape = img.shape
    height = shape[0]
    width = shape[1]

    if height < 240 and width < 240:
        return False
    
    score = calc_quality(img_path)
    
    img2gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    imageVar = cv2.Laplacian(img2gray, cv2.CV_64F).var()
    print("[%s] quality score is %s, frq score is %s" %(img_path, score, imageVar))


    return imageVar > t1 and score >= t2
    

if __name__ == "__main__":
    src_dir = sys.argv[1]
    dest_dir = sys.argv[2]
    t = int(sys.argv[3])

    for f in os.listdir(src_dir):
        full_path = os.path.join(src_dir, f)
        if full_path.split('.')[-1] not in ['jpg', 'png', 'gif']:
            continue
        
        print("process ", full_path)
        if image_etl(full_path, t, 90):
            dest_path = os.path.join(dest_dir, f)
            cmd = "cp " + "\"" + full_path + "\" " + "\"" + dest_path + "\""
            #print(cmd)
            os.system(cmd)

