import matplotlib.image as mpimg
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import cv2
import urllib
from sklearn.cluster import KMeans, MeanShift, estimate_bandwidth
from PIL import Image
import colorsys
import os
from io import BytesIO
from django.contrib.sites import requests
from django.conf import settings
from django.db import DatabaseError, connection

class GetImageColor():
    def __init__(self,imgurl): 
        self.imgurl = str(imgurl)
        # print(imgurl)

    #이미지 픽셀 섞기
    def shuffle_image(self, image):
        image2 = np.reshape(image, (-1, image.shape[2]))
        np.random.shuffle(image2)
        image2 = np.reshape(image2, image.shape)
        return image2

    def url_to_image(self,url):
        resp = urllib.request.urlopen(url)
        image = np.asarray(bytearray(resp.read()), dtype="uint8")
        image = cv2.imdecode(image, cv2.IMREAD_COLOR)
        return image

    #이미지 로드, 전처리
    def preprocess_image(self):
        #load image from url
        image = self.url_to_image(self.imgurl)
        #load image from path
        #image = cv2.imread(os.path.join(self.imgurl))
        
        ## 밝기조절
        val=10
        array=np.full(image.shape,(val,val,val),dtype=np.uint8)
        image=cv2.add(image,array)
        
        ## rgb mode
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB) 

        ## 선명하게
        # 커널 생성(대상이 있는 픽셀을 강조)
        kernel = np.array([[0, -1, 0],
                        [-1, 5, -1],
                        [0, -1, 0]])
        # 커널 적용 
        image = cv2.filter2D(image, -1, kernel)
       
        ## image w,h 구하기(픽셀수 128*128) 
        scale_percent = (image.shape[0] * image.shape[1]) / (128*128) # percent of original size
        width = int(image.shape[1] / np.sqrt(scale_percent))
        height = int(image.shape[0] / np.sqrt(scale_percent))
        dim = (width, height) 
        
        # resize: 비율은 유지하면서 픽셀수는 128*128 로
        image = cv2.resize(image, dim, interpolation = cv2.INTER_AREA)  

        # random shuffle image pixel 
        # image = self.shuffle_image(image)

        #reshape
        image = image.reshape((image.shape[0] * image.shape[1], 3)) # height, width 통합
        
        return image

    # Kmeans clustering
    def get_kmeans(self):
        image = self.preprocess_image()

        #5개의 대표 색상 추출
        k = 5
        clt = KMeans(n_clusters = k)
        clt.fit(image)
        self.centeroid_histogram(clt)
        return clt
    
    # MeanShift Clustering
    def get_meanshift(self):
        image = self.preprocess_image()

        bandwidth = estimate_bandwidth(image, quantile=0.1, n_samples=200) #128*128에 이 파라미터가 적절한듯(조정)
        #print('bandwidth:',bandwidth)
        ms = MeanShift(bandwidth=bandwidth, bin_seeding=True)
        ms.fit(image)
        
        self.centeroid_histogram(ms)
        return ms

    def centeroid_histogram(self,clt):
        num_labels = np.arange(0, len(np.unique(clt.labels_)) + 1)
        (hist, _) = np.histogram(clt.labels_, bins=num_labels)
        hist = hist.astype("float")
        hist /= hist.sum()
        centroids = clt.cluster_centers_
 
        #plot colors
        bar = np.zeros((50, 300, 3), dtype="uint8")
        start_x = 0
        for (percent, color) in zip(hist, centroids):
            end_x = start_x + (percent * 300)
            cv2.rectangle(bar, (int(start_x), 0), (int(end_x), 50),color.astype("uint8").tolist(), -1)
            start_x = end_x

        #save results
        plt.figure()
        plt.axis('on')
        plt.imshow(bar)
        img_data = BytesIO()
        plt.savefig(img_data, format='jpg')
        img_data.seek(0)
        return img_data

class Recommendation():
    def __init__(self,clt,data,default=False):
        self.clt = clt
        self.default=default
        # data 전체
        self.df = pd.DataFrame(data, columns =['img_id','author','title','h1','s1','v1','h2','s2','v2','h3','s3','v3','img_path','label1_id','label2_id','label3_id'])

    def revised_rgb_to_hsv(self,r,g,b):
        (h, s, v) = colorsys.rgb_to_hsv(r/255, g/255, b/255)
        h *= 360
        s *= 100
        v *= 100
        return h, s, v

    #list2 의 값들만 list1 에 append
    def list_append_only_values(self,list1,list2):
        for x in list2:
            list1.append(x)
        return list1

    def recommend_pic(self): 
        """
        # 유사색의 명화 추천
        roomcolor_analog(유사색) : h는 +-30도(!=0) (AND) s는동일 v는 +-5 
        # 보색의 명화 추천
        roomcolor_compl(보색): h는 +-180도 (AND) s와v는 +-5
        # 단색의 명화 추천
        roomcolor_mono(단색) : h는 동일 (AND) s는 +-10, v는 고려하지 않음
        """
        #default 이미지 추천 - random select
        if self.default:
            df_shuffled = self.df.sample(frac=1).reset_index(drop=True) # radom shuffle
            df_analog = df_shuffled[1:30][['img_id','img_path']].to_dict('records') # 30개 선택
            return df_analog

        df_analog = [] #, df_compl, df_mono = [], [], []
        for i in range(1,4): 
            for center in self.clt.cluster_centers_:
                h,s,v = Recommendation.revised_rgb_to_hsv(self,center[0],center[1],center[2])
                h=int(h)
                s=int(s)
                v=int(v)

                roomcolor_analog= (abs(self.df['h'+str(i)]-h)>=0)&(abs(self.df['h'+str(i)]-h)<=30)&(abs(self.df['s'+str(i)]-s)==0)&(abs(self.df['v'+str(i)]-v)<=5)
                # roomcolor_compl=(abs(self.df['h'+str(i)]-h)==180)&(abs(self.df['s'+str(i)]-s)<=5)&(abs(self.df['v'+str(i)]-v)<=5)
                # roomcolor_mono=(self.df['h'+str(i)]==h)&(abs(self.df['s'+str(i)]-s)<=10)

                #유사색
                if len(self.df[roomcolor_analog]['img_path']):
                    df_analog.append( (self.df[roomcolor_analog][['img_id','img_path']].to_dict('records'))[0] )
                # #보색
                # if len(self.df[roomcolor_compl]['img_path']):
                #     df_compl.append( (self.df[roomcolor_compl][['img_id','img_path']].to_dict('records'))[0] )
                # #단색
                # if len(self.df[roomcolor_mono]['img_path']):
                #     df_mono.append( (self.df[roomcolor_mono][['img_id','img_path']].to_dict('records'))[0] )
                
        # return df_analog,df_compl,df_mono   
        return df_analog