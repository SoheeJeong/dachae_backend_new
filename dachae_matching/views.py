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
def get_best_image_list(request):
    '''
    메인화면에서 샘플사진 리스트 로드
    param example) start=0&end=2 이면 index 0,1,2 사진 로드 (1,2,3 번째 사진 로드)
    '''
    header = request.headers
    access_token = header['Authorization'] if 'Authorization' in header else None
    user_id = request.GET.get('user_id',None)
    start = request.GET.get("start",0)  
    end = request.GET.get("end",None)  

    # user validation check
    check_token_isvalid(access_token,user_id)

    try:
        best_image_list = models.TbSampleList.objects.values("sample_path","sample_id","img_id")
        end = len(best_image_list) if not end else min(len(best_image_list),int(end)+1)
        data_list = best_image_list[int(start):end+1]
        #s3 path 로 바꾸기
        for i in range(len(data_list)):
            img_key = data_list[i]["sample_path"]
            data_list[i]["sample_path"] = get_public_url(ARTWORK_BUCKET_NAME,SAMPLE_FOLDER_NAME+img_key)
    except:
        raise exceptions.DataBaseException
    
    data = {
            "data" : data_list,
            }
    return Response(data)

@csrf_exempt
@api_view(["POST"])
def get_picture_filtered_result(request):
    '''
    키워드 및 느낌라벨로 명화 검색
    '''
    #TODO: 라벨 최소개수 1개 지정
    header = request.headers
    access_token = header['Authorization'] if 'Authorization' in header else None
    body = json.loads(request.body.decode("utf-8"))
    label_list = body["label_list"]
    user_id = None if "user_id" not in body else body["user_id"]

    # user validation check
    check_token_isvalid(access_token,user_id)
    
    if len(label_list)==0:
        result_image_list = models.TbArtworkInfo.objects.values("img_path","img_id")

    else:
        #TODO: filter 기준 정립 필요
        result_image_list = get_label_filtered_result(label_list)
        
    #s3 파일 경로 얻기
    for i in range(len(result_image_list)):
        img_key = result_image_list[i]["img_path"] #get key
        result_image_list[i]["img_path"] = get_public_url(ARTWORK_BUCKET_NAME,img_key)

    #TODO: 추후에 sorting 기준 추가 (인기순, 가격순 등)
    
    #TODO: save into user log
    if user_id is None or not models.TbUserInfo.objects.filter(user_id=user_id).exists():
        print("save into user log with user=null")
    else:
        print("save into user log with user")
        
    data = {
        "data" : result_image_list,
    }
    return Response(data)

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

@api_view(["GET"])
def get_label_list(request):
    '''
    느낌라벨 리스트 가져오기
    param example) start=0&end=2 이면 index 0,1,2 라벨 로드 (1,2,3 번째 라벨 로드)
    '''
    header = request.headers
    access_token = header['Authorization'] if 'Authorization' in header else None
    user_id = request.GET.get('user_id',None)
    start = request.GET.get("start",0)  
    end = request.GET.get("end",None)  

    # user validation check
    check_token_isvalid(access_token,user_id)

    try:
        label_list = models.TbLabelInfo.objects.values("label_nm","label_id")
    except:
        raise exceptions.DataBaseException
    
    end = len(label_list) if not end else min(len(label_list),int(end)+1)
    data_list = label_list[int(start):end]
    data = {
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
    #try:
    #백엔드에 사용자 업로드 이미지 저장
    rand_str = get_random_string(8)
    if user_id:
        filename = server_time + user_id + rand_str + upload_files[0].name #저장할 파일명 지정 (서버타임+유저아이디+_파일명 형식)
        save_path = os.path.join(user_id, filename)
    else:
        filename = server_time + rand_str + upload_files[0].name 
        save_path = os.path.join(rand_str, filename)
    
    #default_storage.save(save_path, upload_files[0])
    #file_addr = os.path.join(settings.MEDIA_ROOT,save_path)

    key = s3connection.save_file_into_s3(upload_files[0],USER_BUCKET_NAME,filename)

    #백엔드에 저장된 파일을 aws s3 스토리지에 저장
    #접근 url 반환
    if key:
        s3_url = s3connection.get_presigned_url(USER_BUCKET_NAME,key) 
    else: 
        raise exceptions.StorageConnectionException      
    #models.Tb_UPLOAD_INFO 에 업로드 정보 저장
    if s3_url:
        #models.TbUploadInfo.objects.create(user_id=user_id,server_time=server_time,room_img=file_addr)
        upload_obj = models.TbUploadInfo(user_id=user_id,server_time=server_time,room_img=key) #key를 저장
        upload_obj.save()
        upload_id = upload_obj.upload_id
    else:
        exceptions.DataBaseException

    #백엔드에서 삭제
    if user_id:
        shutil.rmtree(os.path.join(settings.MEDIA_ROOT,user_id)) #user folder 전체를 삭제
    else:
        shutil.rmtree(os.path.join(settings.MEDIA_ROOT,rand_str))
    #default_storage.delete(upload_file_path) #업로드 file만 삭제
    
    #TODO: save into user log
    if user_id is None or not models.TbUserInfo.objects.filter(user_id=user_id).exists():
        print("save into user log with user=null")
    else:
        print("save into user log with user")

    # except: 
    #     raise exceptions.DataBaseException

    data = {
            "file_addr" : s3_url,
            "room_img" : key,
            "upload_id" : upload_id,
            }

    return Response(data)

@csrf_exempt
@api_view(["POST"])
def exec_recommend(request):
    '''
    매칭 수행
    '''
    header = request.headers
    access_token = header['Authorization'] if 'Authorization' in header else None
    body = json.loads(request.body.decode("utf-8"))
    user_id = None if "user_id" not in body else body["user_id"]
    upload_id = None if "upload_id" not in body else body["upload_id"] 
    room_img = None if "room_img" not in body else body["room_img"] 
    
    if not room_img or not upload_id:
        raise exceptions.ParameterMissingException

    # user validation check
    check_token_isvalid(access_token,user_id)

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

    upload_object = models.TbUploadInfo.objects.filter(upload_id=upload_id)
    if not upload_object.exists():
        raise exceptions.DataBaseException

    #load artwork data
    pic_data = models.TbArtworkInfo.objects.values('img_id','img_path','author','title','h1','s1','v1','h2','s2','v2','h3','s3','v3','label1_id','label2_id','label3_id')

    #exec recommend
    # try:
    room_img_url = s3connection.get_presigned_url(USER_BUCKET_NAME,room_img)
    getimgcolor = GetImageColor(room_img_url)
    clt =  getimgcolor.get_meanshift() #room color clt with meanshift
    clt_path = getimgcolor.centeroid_histogram(clt) #clustering result saved path (backend 임시저장 경로)
    #save clustering result into s3 storage
    clt_key = CLUSTER_FOLDER_NAME + room_img
    #s3connection.save_file_into_s3(clt_path,USER_BUCKET_NAME,clt_key)
    clt_url = get_public_url(USER_BUCKET_NAME,clt_key)

    #clustering result 사진 삭제
    #os.remove(clt_path)

    #선택된 label과 clustering 결과 이미지 path를 models.Tb_upload_info에 저장
    try:
        upload_object.update(clustering_img=clt_key,label1_id=label_id_list[0],label2_id=label_id_list[1],label3_id=label_id_list[2])
    except:
        raise exceptions.DataBaseException
    
    recommendation = Recommendation(clt,pic_data)
    analog,comp,mono = convert_recommended_img_path_into_s3_path(recommendation.recommend_pic())
    # except:
    #     raise exceptions.RecommendationException


    #TODO: 라벨 필터링 과정 추가 (filter criteria: label_list) -> count, label_list
    analog, comp, mono = get_label_filtered_result(label_list,(analog,comp,mono))
    
    if user_id:
        #TODO: user log 추가
        show_range = "all"
    else:
        #TODO: user log 추가 -> user=null
        show_range = "part"

    data = {
        'show_range':show_range,
        'upload_id':upload_object.values("upload_id")[0]["upload_id"],
        'room_img_url':room_img_url,
        'clustering_result_url':clt_url,
        'chosen_label':label_nm_list,
        'recommend_images':{ #img id,img_path(presigned uri path),count,label_list
            'analog':analog,
            'comp':comp,
            'mono':mono   
        }
    }
    return Response(data)


##### 찜, 구매 #####

@api_view(["GET"])
def set_wish_list(request):
    # server time 
    server_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # get param
    header = request.headers
    access_token = header['Authorization'] if 'Authorization' in header else None
    user_id = request.GET.get("user_id",None)
    img_id = request.GET.get("img_id",None)

    # param check
    if not img_id:
        raise exceptions.ParameterMissingException
    
    if not models.TbArtworkInfo.objects.filter(img_id=img_id).exists():
        raise exceptions.NoImageInfoException

    #valid user 인지 검사
    validation = check_token_isvalid(access_token,user_id)
    if validation == "not logged":
        raise exceptions.LoginRequiredException

    # img_id, user_id, server_time 를 wishlist table 에 넣기
    wish_item = models.TbWishlistInfo.objects.filter(user_id=user_id,img_id=img_id)
    if not wish_item.exists(): 
        #존재하지 않는 row 일 경우에만 -> 새로 table에 삽입
        models.TbWishlistInfo.objects.create(user_id=user_id,img_id=img_id,server_time=server_time)

    #사용자의 wishlist 정보 반환
    user_total_wishlist = models.TbWishlistInfo.objects.filter(user_id=user_id).values("img_id")
    user_wishlist = []
    for wish in user_total_wishlist:
        user_wishlist.append(wish["img_id"])

    #TODO: user log 추가
       
    data = {
            "user_wishlist":user_wishlist,
            }

    return Response(data)

@api_view(["GET"])
def del_wish_list(request):
    # get param
    header = request.headers
    access_token = header['Authorization'] if 'Authorization' in header else None
    user_id = request.GET.get("user_id",None)
    img_id = request.GET.get("img_id",None)

    # param check
    if not img_id:
        raise exceptions.ParameterMissingException
    
    #valid user 인지 검사
    validation = check_token_isvalid(access_token,user_id)
    if validation == "not logged":
        raise exceptions.LoginRequiredException

    # wishlist table 에서 삭제하기
    try:
        wish_item = models.TbWishlistInfo.objects.filter(user_id=user_id,img_id=img_id)
        if wish_item.exists(): #존재하는 item일 경우에만
            models.TbWishlistInfo.objects.filter(user_id=user_id,img_id=img_id).delete() #삭제 수행
    except: 
        raise exceptions.DataBaseException

    #TODO: user log 추가

    data = {
            "result": "succ"
            }
    return Response(data)

@api_view(["GET"])
def load_purchase_link(request):
    # server time 
    server_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # get params
    header = request.headers
    access_token = header['Authorization'] if 'Authorization' in header else None
    user_id = request.GET.get("user_id",None)
    img_id = request.GET.get("img_id",None)
    upload_id = request.GET.get("upload_id",None)

    # param check
    if not img_id:
        raise exceptions.ParameterMissingException

    # user validation check
    check_token_isvalid(access_token,user_id)

    try:
        # purchase_info table 에 새로운 row로 구매정보 저장
        if user_id:
            purchase_obj = models.TbPurchaseInfo(user_id=user_id, img_id=img_id, server_time=server_time)
            purchase_obj.save()
        else:
            purchase_obj = models.TbPurchaseInfo(img_id=img_id, server_time=server_time)
            purchase_obj.save()
        purchase_id = purchase_obj.purchase_id

        # matching 후 구매 시 models.models.Tb_UPLOAD_INFO 에 purchase_id 저장
        if upload_id and models.TbUploadInfo.objects.filter(upload_id=upload_id).exists():
            upload_info = models.TbUploadInfo.objects.get(upload_id=upload_id)
            upload_info.purchase_id = purchase_id
            upload_info.save()
        # 구매 링크
        try:
            product_id = models.TbArtworkInfo.objects.filter(img_id=img_id).values("product_id")[0]["product_id"]
            purchase_url = models.TbProductInfo.objects.filter(product_id=product_id).values("purchase_url")[0]
        except:
            raise exceptions.NoProductInfoException
    except:
        raise exceptions.DataBaseException

    #TODO: save into user log
    if user_id is None or not models.TbUserInfo.objects.filter(user_id=user_id).exists():
        print("save into user log with user=null")
    else:
        print("save into user log with user")

    data = {
        "purchase_link": purchase_url["purchase_url"]
        }
    return Response(data)