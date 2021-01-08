from django.contrib import messages
from django.db import DatabaseError, connection
from django.http import HttpResponse, HttpResponseNotFound, JsonResponse
from django.shortcuts import render, redirect
from django.conf import settings
from django.core import serializers
from django.core.files.storage import default_storage
from django.views.decorators.csrf import csrf_exempt
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status

import os
import requests
import json
import pytz
from datetime import datetime,timezone,timedelta
import time
import random
import base64

from .matching import GetImageColor, Recommendation
from dachae.models import TbArkworkInfo,TbCompanyInfo,TbLabelInfo,TbUploadInfo,TbUserInfo,TbUserLog,TbWishlistInfo,TbPurchaseInfo
from dachae.exceptions import DataBaseException

@api_view(["GET"])
def get_picture_filtered_result(request):
    '''
    키워드 및 느낌라벨로 명화 검색
    '''
    data = {"data":"temp"}
    return Response(data)

@api_view(["GET"])
def get_picture_detail_info(request):
    '''
    명화 1개의 상세정보 가져오기 (이미지 클릭 시 명화 상세정보 페이지로 이동)
    '''
    img_id = request.GET.get("img_id",None)  
    if not img_id:
        raise DataBaseException

    image_info = TbArkworkInfo.objects.filter(image_id=img_id).values("img_path","title","author","era","style","company_id","price")
    image_data = image_info[0] #unique item
    company_nm = TbCompanyInfo.objects.filter(company_id=image_data["company_id"]).values("company_nm")
    
    del image_data["company_id"]
    image_data.update(company_nm[0])

    data = {
            "result": "succ",
            "msg": "메세지",
            "data": image_data,
            }
    return Response(data)

@api_view(["GET"])
def get_label_list(request):
    '''
    느낌라벨 리스트 가져오기
    param example) start=0&end=2 이면 index 0,1,2 라벨 로드 (1,2,3 번째 라벨 로드)
    '''
    start = request.GET.get("start",0)  
    end = request.GET.get("end",None)  

    label_list = TbLabelInfo.objects.values("label_nm","label_id")
    end = len(label_list) if not end else min(len(label_list),int(end)+1)

    data_list = label_list[int(start):end]
    data = {
            "result": "succ",
            "msg": "메세지",
            "data" : data_list,
            }

    return Response(data)

@csrf_exempt
@api_view(["POST"])
def set_user_image_upload(request):
    '''
    사용자 로컬이미지 업로드 -> set into storage
    '''
    # server time 
    tz = pytz.timezone('Asia/Seoul')
    server_time = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
    
    user_id = request.POST.get("user_id", None) 
    upload_files = request.FILES.getlist('file')
    upload_file_path = os.path.join(user_id)

    if not upload_files: #업로드된 파일이 없을 경우
        raise DataBaseException #TODO : 업로드된 파일이 없습니다 exception 추가 후 바꾸기
    if len(upload_files)>1:
        raise DataBaseException #TODO : 파일을 1장만 업로드해주세요 exception 추가 후 바꾸기
    
    #파일 확장자 검사
    filename = upload_files[0].name.split('.')
    if filename[len(filename)-1] not in ['jpg','jpeg','png']: #TODO : 허용되는 확장자 지정
        raise DataBaseException #TODO : 허용되는 파일 형식이 아닙니다 exception 으로 바꾸기

    filename = server_time + upload_files[0].name #저장할 파일명 지정
    save_path = os.path.join(upload_file_path, filename)
    default_storage.save(save_path, upload_files[0])
    file_addr = settings.MEDIA_ROOT+save_path
    
    #TODO : TB_UPLOAD_INFO 에 정보 저장

    data = {
            "result": "succ",
            "msg": "메세지",
            "file_addr" : file_addr,
            }
    return Response(data)

@csrf_exempt
@api_view(["POST"])
def exec_recommend(request):
    '''
    매칭 수행
    '''
    body = json.loads(request.body.decode("utf-8"))
    upload_id = None if not body["upload_id"] else body["upload_id"]
    if not upload_id:
        raise DataBaseException #TODO: no parameter exception 으로 바꾸기

    label_list = body["label_list"]
    chosen_label = []
    for label in label_list:
        chosen_label.append(label["label_nm"])    

    room_img_info = TbUploadInfo.objects.values("room_img") #user upload image path (backend)
    room_img_path = room_img_info[0]["room_img"]

    #temp path for debug - TODO: MUST delete below line after debug
    room_img_path = os.path.join(settings.MEDIA_ROOT,"sohee/101104index.jpeg")

    #load artwork data
    pic_data = TbArkworkInfo.objects.values('image_id','author','title','h1','s1','v1','h2','s2','v2','h3','s3','v3','img_path')

    #exec recommend
    getimgcolor = GetImageColor(room_img_path)
    clt =  getimgcolor.get_meanshift() #room color clt with meanshift
    clt_path = getimgcolor.centeroid_histogram(clt) #clustering result saved path
    #TODO: set chosen label data and clustering result data in Tb_upload_info

    analog,comp,mono = Recommendation(clt,pic_data).recommend_pic() #recommended images list
    #TODO: add filtering by label function here (filter criteria: label_list)

    data = {
        'result':'succ',
        'msg':'message',
        'recommend':{
            'upload_id':upload_id,
            'room_img':room_img_path,
            'clustering_result':clt_path,
            'chosen_label':chosen_label,
            'recommend_images':{
                'analog':analog['img_path'],
                'comp':comp['img_path'],
                'mono':mono['img_path']   
            }
        }
    }
    return Response(data)

# 찜, 구매
@api_view(["GET"])
def set_wish_list(request):
    # server time 
    tz = pytz.timezone('Asia/Seoul')
    server_time = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
    
    user_id = request.GET.get("user_id",None)
    img_id = request.GET.get("img_id",None)
    if not user_id or not img_id:
        raise DatabaseError #TODO: no parameter error 로 변경
    
    try:
        print("wishlist table 삽입")
        #TODO: img_id, user_id, server_time 를 wishlist table 에 넣기
    except: 
        raise DatabaseError

    data = {
            "result": "succ",
            "msg": "메세지"
            }

    return Response(data)

@api_view(["DELETE"])
def del_wish_list(request):
    # server time 
    tz = pytz.timezone('Asia/Seoul')
    server_time = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")

    user_id = request.GET.get("user_id",None)
    img_id = request.GET.get("img_id",None)
    if not user_id or not img_id:
        raise DatabaseError #TODO: no parameter error 로 변경
    
    try:
        print("wishlist table 에서 삭제")
        #TODO: img_id, user_id 에 해당하는 row를 wishlist table 에서 삭제하기
    except: 
        raise DatabaseError

    data = {
            "result": "succ",
            "msg": "메세지"
            }
    return Response(data)

@api_view(["GET"])
def exec_purchase(request):
    # server time 
    tz = pytz.timezone('Asia/Seoul')
    server_time = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")

    # get params
    user_id = request.GET.get("user_id",None)
    img_id = request.GET.get("img_id",None)
    room_img = request.GET.get("room_img",None) #매칭에서 넘어온 경우 room_img is not None
    company_id = request.GET.get("company_id",None)
    # param check
    if not user_id or not img_id:
        raise DataBaseException #TODO: no parameter error 로 변경
    if not company_id:
        raise DataBaseException #TODO: 제휴사 없음 팝업?
    
    # purchase_info table 에 새로운 row로 구매정보 저장
    try:
        TbPurchaseInfo.objects.create(user_id=user_id, image_id=img_id, server_time=server_time, company_id=company_id,price=3000) #TODO : price 변경 (어떡할지?)
        purchase_item = TbPurchaseInfo.objects.filter(user_id=user_id, image_id=img_id, server_time=server_time, company_id=company_id,price=3000)
        purchase_id = purchase_item.values("purchase_id")[0]["purchase_id"] #TODO: 방금 생성한 item 의 pk 얻는법 이게 최선?
    except:
        raise DataBaseException

    # matching 후 구매 시 TB_UPLOAD_INFO 에 purchase_id 저장
    try:
        if room_img is not None:
            upload_info = TbUploadInfo.objects.get(user_id=user_id, room_img=room_img)
            upload_info.purchase_id = purchase_id
            upload_info.save()
    except:
        raise DataBaseException

    data = {
        "result": "succ",
        "msg": "메세지",
        "data":{
        "link": "https://artvee.com/dl/alma-parens" #TODO: 실제 제휴사 링크로 바꾸기
        }
    }
    return Response(data)