from django.conf import settings
from django.core.files.storage import default_storage
from django.views.decorators.csrf import csrf_exempt
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

from dachae.utils import S3Connection,check_token_isvalid

s3connection = S3Connection()

MAX_LABEL_NUM = 3 #라벨 선택 최대 허용 개수
ARTWORK_LABEL_NUM = 3 #명화 1개당 라벨 개수

ARTWORK_BUCKET_NAME = os.getenv("ARTWORK_BUCKET_NAME")
USER_BUCKET_NAME = os.getenv("USER_BUCKET_NAME")
CLUSTER_BUCKET_NAME = os.getenv("CLUSTER_BUCKET_NAME")
CLUSTER_FOLDER_NAME = os.getenv("CLUSTER_FOLDER_NAME")
SAMPLE_BUCKET_NAME = os.getenv("SAMPLE_BUCKET_NAME")

#TODO: service 구조로 refactoring
#TODO: 필요한곳에 권한체크 추가 - 찜, 구매
#TODO: 예외처리 체크

##### 검색, 업로드, 매칭 #####
@api_view(["GET"])
def get_best_image_list(request):
    '''
    메인화면에서 샘플사진 리스트 로드
    param example) start=0&end=2 이면 index 0,1,2 사진 로드 (1,2,3 번째 사진 로드)
    '''
    start = request.GET.get("start",0)  
    end = request.GET.get("end",None)  

    best_image_list = models.TbSampleList.objects.values("sample_path","sample_id","product_id")
    end = len(best_image_list) if not end else int(end)
    data_list = best_image_list[int(start):end+1]
    #s3 path 로 바꾸기
    for i in range(len(data_list)):
        img_key = data_list[i]["sample_path"]
        print(img_key)
        data_list[i]["sample_path"] = s3connection.get_presigned_url(SAMPLE_BUCKET_NAME,img_key)

    data = {
            "result": "succ",
            "msg": "메세지",
            "data" : data_list,
            }
    return Response(data)

@csrf_exempt
@api_view(["POST"])
def get_picture_filtered_result(request):
    '''
    키워드 및 느낌라벨로 명화 검색
    '''
    body = json.loads(request.body.decode("utf-8"))
    label_list = body["label_list"]

    if len(label_list)==0:
        result_image_list = models.TbArtworkInfo.objects.values("img_path","img_id")

    else:
        #TODO: filter 기준 정립 필요
        #label_query 초기화 - empty result
        first_label = label_list[0]["label_id"]
        label_query = models.TbArtworkInfo.objects.filter(label1_id=first_label,label2_id=first_label,label3_id=first_label) 
        #입력으로 받은 라벨 하나에 대해 해당 라벨을 포함하고 있는 artwork object들의 합집합
        for label_dict in label_list: 
            #TODO: artwork 별로 몇개의 라벨이 포함되어 있는지 count 정보 저장 필요. 이 기준으로 sorting 필요.
            label_query = label_query.union(models.TbArtworkInfo.objects.filter(label1_id=label_dict["label_id"]))
            label_query = label_query.union(models.TbArtworkInfo.objects.filter(label2_id=label_dict["label_id"]))
            label_query = label_query.union(models.TbArtworkInfo.objects.filter(label3_id=label_dict["label_id"]))

        #TODO: order by 라벨이 많이 포함되어 있는 순으로 (count 정보)
        result_image_list = label_query.order_by("img_id").values("img_path","img_id")
        
        #s3 파일 경로 얻기
        for i in range(len(result_image_list)):
            img_key = result_image_list[i]["img_path"] #get key
            result_image_list[i]["img_path"] = s3connection.get_presigned_url(ARTWORK_BUCKET_NAME,img_key)

        #TODO: 추후에 sorting 기준 추가 (인기순, 가격순 등)

    data = {
        "result": "succ",
        "msg": "메세지",
        "data" : result_image_list,
    }
    return Response(data)

@api_view(["GET"])
def get_picture_detail_info(request):
    '''
    명화 1개의 상세정보 가져오기 (이미지 클릭 시 명화 상세정보 페이지로 이동)
    '''
    img_id = request.GET.get("img_id",None)  
    if not img_id:
        raise exceptions.ParameterMissingException

    image_data = models.TbArtworkInfo.objects.filter(img_id=img_id).values("img_path","title","author","era","style","company_id","price","label1_id","label2_id","label3_id")[0] #,"label4_id","label5_id")
    company_nm = models.TbCompanyInfo.objects.filter(company_id=image_data["company_id"]).values("company_nm")
    
    del image_data["company_id"]
    image_data.update(company_nm[0])

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

    #presigned url 생성
    bucket = ARTWORK_BUCKET_NAME
    key = image_data["img_path"]
    s3_url = s3connection.get_presigned_url(bucket,key)

    #response 를 위한 img path 데이터 변경
    image_data["img_path"]=s3_url

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

    label_list = models.TbLabelInfo.objects.values("label_nm","label_id")
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
    사용자 로컬이미지 업로드 -> set into storage -> 로컬데이터 삭제
    '''
    # server time 
    server_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    upload_files = request.FILES.getlist('file')
    user_id = request.POST.get("user_id", None) 
    access_token = request.POST.get("access_token",None)

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

    token_validation = check_token_isvalid(access_token,user_id)
    if token_validation == "not logged":
        print("로그인 안된 유저 버전")

    #파일 저장 
    try:
        #백엔드에 사용자 업로드 이미지 저장
        filename = server_time + user_id + upload_files[0].name #저장할 파일명 지정 (서버타임+유저아이디+_파일명 형식)
        save_path = os.path.join(user_id, filename)
        default_storage.save(save_path, upload_files[0])
        file_addr = os.path.join(settings.MEDIA_ROOT,save_path)

        #백엔드에 저장된 파일을 aws s3 스토리지에 저장
        bucket = USER_BUCKET_NAME
        key = s3connection.upload_file_into_s3(file_addr,bucket,filename)
        #접근 url 반환
        if key:
            s3_url = s3connection.get_presigned_url(bucket,key) 
        else: 
            raise exceptions.StorageConnectionException      
        #models.Tb_UPLOAD_INFO 에 업로드 정보 저장
        if s3_url:
            #models.TbUploadInfo.objects.create(user_id=user_id,server_time=server_time,room_img=file_addr)
            models.TbUploadInfo.objects.create(user_id=user_id,server_time=server_time,room_img=key) #key를 저장
        else:
            exceptions.DataBaseException

        #백엔드에서 삭제
        shutil.rmtree(os.path.join(settings.MEDIA_ROOT,user_id)) #user folder 전체를 삭제
        #default_storage.delete(upload_file_path) #업로드 file만 삭제

    except: 
        raise exceptions.DataBaseException

    data = {
            "result": "succ",
            "msg": "메세지",
            "file_addr" : s3_url,
            "room_img" : key
            }

    return Response(data)

@csrf_exempt
@api_view(["POST"])
def exec_recommend(request):
    '''
    매칭 수행
    '''
    body = json.loads(request.body.decode("utf-8"))
    user_id = body["user_id"]
    room_img = body["room_img"]

    if not user_id or not room_img:
        raise exceptions.ParameterMissingException

    label_list = body["label_list"]
    if len(label_list) > MAX_LABEL_NUM:
        raise exceptions.TooMuchLabelSeletedException

    label_nm_list, label_id_list = [],[]
    for i in range(MAX_LABEL_NUM):
        if i<len(label_list):
            label_nm_list.append(label_list[i]["label_nm"]) 
            label_id_list.append(label_list[i]["label_id"])
        else:
            label_id_list.append(None)   

    upload_object = models.TbUploadInfo.objects.filter(user_id=user_id,room_img=room_img)
    if not upload_object.exists():
        raise exceptions.DataBaseException
    room_img_url = s3connection.get_presigned_url(USER_BUCKET_NAME,room_img)

    #load artwork data
    pic_data = models.TbArtworkInfo.objects.values('img_id','author','title','h1','s1','v1','h2','s2','v2','h3','s3','v3','img_path')

    #exec recommend
    getimgcolor = GetImageColor(room_img_url)
    clt =  getimgcolor.get_meanshift() #room color clt with meanshift
    clt_path = getimgcolor.centeroid_histogram(clt) #clustering result saved path (backend 임시저장 경로)

    #save clustering result into s3 storage
    clt_key = CLUSTER_FOLDER_NAME + room_img
    s3connection.upload_file_into_s3(clt_path,CLUSTER_BUCKET_NAME,clt_key)
    clt_url = s3connection.get_presigned_url(CLUSTER_BUCKET_NAME,clt_key)

    #TODO: 예외처리 추가
    #clustering result 사진 삭제
    os.remove(clt_path)

    #선택된 label과 clustering 결과 이미지 path를 models.Tb_upload_info에 저장
    try:
        upload_object.update(clustering_img=clt_key,label1_id=label_id_list[0],label2_id=label_id_list[1],label3_id=label_id_list[2])
    except:
        raise exceptions.DataBaseException

    analog,comp,mono = Recommendation(clt,pic_data).recommend_pic() #recommended images list
    
    #TODO: 라벨 필터링 과정 추가 (filter criteria: label_list)
    #matching.py 에서 아얘 라벨 필터링까지 한 결과를 반환하도록 할지? 아니면 여기서 필터링할지?

    data = {
        'result':'succ',
        'msg':'message',
        'upload_id':upload_object.values("upload_id")[0]["upload_id"],
        'room_img':room_img_url,
        'clustering_result':clt_url,
        'chosen_label':label_nm_list,
        'recommend_images':{
            'analog':analog['img_path'],
            'comp':comp['img_path'],
            'mono':mono['img_path']   
        }
    }
    return Response(data)


##### 찜, 구매 #####

@csrf_exempt
@api_view(["POST"])
def set_wish_list(request):
    # server time 
    server_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    body = json.loads(request.body.decode("utf-8"))
    user_id = body["user_id"]
    img_id = body["img_id"]

    #TODO: valid user 인지 token 검사-토큰 만료 검사
    
    if not user_id or not img_id:
        raise exceptions.ParameterMissingException
    
    # img_id, user_id, server_time 를 wishlist table 에 넣기
    #try:
    wish_item = models.TbWishlistInfo.objects.filter(user_id=user_id,img_id=img_id).values()
    if len(wish_item)==0: #존재하지 않는 row -> 새로 table에 삽입
        models.TbWishlistInfo.objects.create(user_id=user_id,img_id=img_id,server_time=server_time)
    else: 
        raise exceptions.AlreadyInWishlistException
    #except: 
    #   raise DataBaseException

    #사용자의 wishlist 정보 반환
    user_total_wishlist = models.TbWishlistInfo.objects.filter(user_id=user_id).values("img_id")
    user_wishlist = []
    for wish in user_total_wishlist:
        user_wishlist.append(wish["img_id"])

    data = {
            "result": "succ",
            "msg": "메세지",
            "user_wishlist":user_wishlist,
            }

    return Response(data)

@csrf_exempt
@api_view(["POST"])
def del_wish_list(request):
    body = json.loads(request.body.decode("utf-8"))
    user_id = body["user_id"]
    img_id = body["img_id"]
    access_token = body["access_token"]

    # param check
    if not user_id or not img_id:
        raise exceptions.ParameterMissingException
    
    #TODO: valid user 인지 token 검사-토큰 만료 검사

    # wishlist table 에서 삭제하기
    try:
        wish_item = models.TbWishlistInfo.objects.filter(user_id=user_id,img_id=img_id).values()
        if len(wish_item)==0: #존재하지 않는 item
            raise exceptions.NotInWishlistException
        models.TbWishlistInfo.objects.filter(user_id=user_id,img_id=img_id).delete() #삭제 수행
    except: 
        raise exceptions.DataBaseException

    data = {
            "result": "succ",
            "msg": "메세지"
            }
    return Response(data)

@csrf_exempt
@api_view(["POST"])
def load_purchase_link(request):
    # server time 
    server_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # get params
    body = json.loads(request.body.decode("utf-8"))
    user_id = body["user_id"]
    access_token = body["access_token"]
    img_id = body["img_id"]
    room_img = body["room_img"] #매칭에서 넘어온 경우만 room_img가 not None
    company_id = body["company_id"]

    # param check
    if not user_id or not img_id:
        raise exceptions.ParameterMissingException
    if not company_id:
        raise exceptions.NoCompanyInfoException

    #valid user 인지 token 검사-토큰 만료 검사
    check_token_isvalid(access_token,user_id)

    try:
        # purchase_info table 에 새로운 row로 구매정보 저장
        models.TbPurchaseInfo.objects.create(user_id=user_id, img_id=img_id, server_time=server_time)
        purchase_item = models.TbPurchaseInfo.objects.filter(user_id=user_id, img_id=img_id, server_time=server_time)
        purchase_id = purchase_item.values("purchase_id")[0]["purchase_id"] #TODO: 방금 생성한 item 의 pk 얻는법 이게 최선?

        # matching 후 구매 시 models.models.Tb_UPLOAD_INFO 에 purchase_id 저장
        if room_img != "":
            upload_info = models.TbUploadInfo.objects.get(user_id=user_id, room_img=room_img)
            if upload_info.exists():
                upload_info.purchase_id = purchase_id
                upload_info.save()
            else:
                print('here')
    except:
        raise exceptions.DataBaseException

    # 구매 링크
    try:
        product_id = models.TbArtworkInfo.objects.filter(img_id=img_id).values("product_id")[0]["product_id"]
        purchase_url = models.TbProductInfo.objects.filter(product_id=product_id).values("purchase_url")[0]
    except:
        raise exceptions.NoProductInfoException
    data = {
        "result": "succ",
        "msg": "메세지",
        "data":{
        "purchase_link": purchase_url["purchase_url"]
        }
    }
    return Response(data)