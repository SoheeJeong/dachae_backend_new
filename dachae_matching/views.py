from django.conf import settings
from django.core.files.storage import default_storage
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import redirect
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status

import os
import shutil
import requests
import sys
import json
from datetime import datetime

from .matching import GetImageColor, Recommendation
from dachae import models
from dachae import exceptions

from dachae.utils import S3Connection,check_token_isvalid,get_random_string,get_label_filtered_result,get_public_url,convert_recommended_img_path_into_s3_path

s3connection = S3Connection()

MAX_LABEL_NUM = 3 #라벨 선택 최대 허용 개수
ARTWORK_LABEL_NUM = 3 #명화 1개당 라벨 개수

ARTWORK_BUCKET_NAME = os.getenv("ARTWORK_BUCKET_NAME")
USER_BUCKET_NAME = os.getenv("USER_BUCKET_NAME")
CLUSTER_FOLDER_NAME = os.getenv("CLUSTER_FOLDER_NAME")
SAMPLE_FOLDER_NAME = os.getenv("SAMPLE_FOLDER_NAME")

#TODO: service 구조로 refactoring
#TODO: 예외처리 체크

##### 검색, 업로드, 매칭 #####
@api_view(["GET"])
def get_picture_detail_info(request):
    '''
    명화 1개의 상세정보 가져오기 (이미지 클릭 시 명화 상세정보 페이지로 이동)
    '''
    header = request.headers
    access_token = header['Authorization'] if 'Authorization' in header else None
    user_id = request.GET.get('user_id',None)
    img_id = request.GET.get("img_id",None)  
        
    if not img_id:
        raise exceptions.ParameterMissingException

    # user validation check
    check_token_isvalid(access_token,user_id)
    
    image_data = models.TbArtworkInfo.objects.filter(img_id=img_id).values("img_path","title","author","era","style","product_id","label1_id","label2_id","label3_id") #,"label4_id","label5_id")
    if image_data.exists():
        image_data = image_data[0]
        company_info = models.TbProductInfo.objects.filter(product_id=image_data["product_id"]).values("company_id","price")
        if company_info.exists():
            company_nm = models.TbCompanyInfo.objects.filter(company_id=company_info[0]["company_id"]).values("company_nm")
        else:
            raise exceptions.NoProductInfoException
        
        image_data.update(company_info[0])
        image_data.update(company_nm[0])
        del image_data["product_id"]
        del image_data["company_id"]
    else:
        raise exceptions.NoImageInfoException

    # 명화의 라벨 리스트 생성
    label_list = []
    for i in range(1,ARTWORK_LABEL_NUM+1):
        col_nm = "label"+str(i)+"_id"
        label_id = image_data[col_nm]
        del image_data[col_nm]

        if label_id is not None:
            try:
                label_nm = models.TbLabelInfo.objects.filter(label_id=label_id).values("label_nm")[0]
                label_list.append(label_nm["label_nm"])
            except:
                raise exceptions.DataBaseException

    image_data.update({
        "label_list":label_list
    })

    #s3 image path
    img_key = image_data["img_path"]
    public_url = get_public_url(ARTWORK_BUCKET_NAME,img_key)
    #response 를 위한 img path 데이터 변경
    image_data["img_path"]=public_url

    data = {
            "data": image_data,
            }
    return Response(data)


@csrf_exempt
@api_view(["POST"])
def set_upload_and_recommend(request):
    '''
    사용자 로컬이미지 업로드 -> set into storage -> 로컬데이터 삭제
    '''
    # server time 
    server_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # get params
    header = request.headers
    access_token = header['Authorization'] if 'Authorization' in header else None
    upload_files = request.FILES.getlist('file')
    user_id = request.POST.get("user_id", None) 

    # user validation check
    check_token_isvalid(access_token,user_id)

    #업로드된 파일이 없을 경우
    if not upload_files: 
        raise exceptions.NoFileUploadedException
    #업로드된 파일이 1개보다 많은 경우
    if len(upload_files)>1:
        raise exceptions.TooManyFileUploadedException  
    #파일 확장자 검사
    filename = upload_files[0].name.split('.')
    if filename[len(filename)-1] not in ['jpg','jpeg','png']: #TODO : 허용되는 확장자 지정
        raise exceptions.WrongFileFormatException

    #파일 저장 
    try:
        rand_str = get_random_string(8)
        #저장할 파일명 지정 (서버타임+유저아이디+_파일명 형식)
        filename = server_time + user_id + rand_str + upload_files[0].name if user_id else server_time + rand_str + upload_files[0].name 
        #s3에 저장
        key = s3connection.save_file_into_s3(upload_files[0],USER_BUCKET_NAME,filename)  
        #접근 url 얻기
        s3_url = s3connection.get_presigned_url(USER_BUCKET_NAME,key)
    
        #models.Tb_UPLOAD_INFO 에 업로드 정보 저장
        if s3_url:
            upload_obj = models.TbUploadInfo(user_id=user_id,server_time=server_time,room_img=key) #key를 저장
            upload_obj.save()
            upload_id = upload_obj.upload_id
        else:
            exceptions.DataBaseException
        
        #TODO: save into user log
        if user_id is None or not models.TbUserInfo.objects.filter(user_id=user_id).exists():
            print("save into user log with user=null")
        else:
            print("save into user log with user")

    except: 
        raise exceptions.DataBaseException

    '''
    매칭 수행 (exec recommend)
    '''
    file_addr = s3_url
    room_img = key
    
    if not room_img or not upload_id:
        raise exceptions.ParameterMissingException

    # user validation check
    #check_token_isvalid(access_token,user_id)

    upload_object = models.TbUploadInfo.objects.filter(upload_id=upload_id)
    if not upload_object.exists():
        raise exceptions.DataBaseException

    #load artwork data
    pic_data = models.TbArtworkInfo.objects.values('img_id','img_path','author','title','h1','s1','v1','h2','s2','v2','h3','s3','v3','label1_id','label2_id','label3_id')

    try:
        room_img_url = s3connection.get_presigned_url(USER_BUCKET_NAME,room_img)
        #exec recommend
        getimgcolor = GetImageColor(room_img_url)
        clt =  getimgcolor.get_meanshift() #room color clt with meanshift
        img_data = getimgcolor.centeroid_histogram(clt) 

        #save clustering result into s3 storage
        clt_key = CLUSTER_FOLDER_NAME + room_img
        s3connection.save_file_into_s3(img_data,USER_BUCKET_NAME,clt_key)
        clt_url = s3connection.get_presigned_url(USER_BUCKET_NAME,clt_key)

        #clustering 결과 이미지 path를 models.Tb_upload_info에 저장
        try:
            upload_object.update(clustering_img=clt_key)
        except:
            raise exceptions.DataBaseException
        
        recommendation = Recommendation(clt,pic_data)
        analog = convert_recommended_img_path_into_s3_path(recommendation.recommend_pic())
    except:
        raise exceptions.RecommendationException

    #라벨 필터링 과정
    #analog = get_label_filtered_result(label_list,analog)

    data = {
        'upload_id':upload_object.values("upload_id")[0]["upload_id"],
        'room_img_url':room_img_url,
        'clustering_result_url':clt_url,
        'recommend_images':analog
    }

    return Response(data)
