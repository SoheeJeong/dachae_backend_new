from django.views import View
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.conf import settings

import os
import json
import jwt #json web tokens
import requests
from datetime import datetime

from dachae.models import TbArkworkInfo,TbUserInfo,TbUserLog  #TODO TbArtworkInfo 를 샘플사진리스트 테이블로 바꾸기
from dachae.exceptions import DataBaseException

#TODO: timezone error 수정
#TODO: 필요한곳에 권한체크 추가

#frontend 역할
@csrf_exempt
def kakao_login_page(request):
    kakao_login_data = {
        "REST_API_KEY":os.getenv("KAKAO_APP_KEY"),
        "REDIRECT_URI":os.getenv("LOGIN_REDIRECT_URI"),
    }
    kakao_logout_data = {
        "REST_API_KEY":os.getenv("KAKAO_APP_KEY"),
        "LOGOUT_REDIRECT_URI":os.getenv("LOGOUT_REDIRECT_URI"),
    }
    return render(request,'login.html',{'login_data':kakao_login_data,'logout_data':kakao_logout_data})

class KakaoLoginView(View):
    def get(self,request):
        ###frontend 역할
        #1. 인증 코드 요청 (from frontend)
        kakao_access_code = request.GET.get('code',None)
        #2. access token 요청
        url = 'https://kauth.kakao.com/oauth/token'
        headers = {'Content-type':'application/x-www-form-urlencoded;charset=utf-8'}
        body = {
            'grant_type' : 'authorization_code',
            'client_id' : os.getenv("KAKAO_APP_KEY"),
            'redirect_uri' : os.getenv("REDIRECT_URI"),
            'code' : kakao_access_code
        }
        token_kakao_response = requests.post(url,headers=headers,data=body)

        ###여기부터 backend 역할
        access_token = json.loads(token_kakao_response.text).get('access_token')
        #3. 사용자 정보 요청
        url = 'https://kapi.kakao.com/v2/user/me'
        headers = {
            'Authorization':f'Bearer {access_token}',
            'Content-type':'application/x-www-form-urlencoded;charset=utf-8',
        }
        body = {
            'property_keys':'["properties.nickname","properties.profile_image","properties.thumbnail_image","kakao_account.email","kakao_account.age_range","kakao_account.birthday","kakao_account.gender"]'
        }
        kakao_response = requests.post(url,headers=headers,data=body)
        kakao_user_info_response = json.loads(kakao_response.text)

        #TODO: signup 으로 redirect 여부 검사 - 우리 db에 있는 유저인가? id 검사
        #이미 존재하는 회원이면 - 로그인 실행
        if TbUserInfo.objects.filter(social_platform="kakao",social_id=kakao_user_info_response["id"]).exists():
            user = TbUserInfo.objects.get(social_id=kakao_user_info_response['id'])
            jwt_token = jwt.encode({'id':user.user_id},settings.SECRET_KEY,algorithm='HS256').decode('utf-8')
            #TODO: 권한정보, 프로필경로 등 넘겨주기
            return HttpResponse(f'id:{user.user_id},nickname:{user.user_nick},token:{jwt_token}')
        
        #새로운 회원 - 회원가입 실행ddd
        #TODO: insert into user DB
        TbUserInfo(
            user_id = kakao_user_info_response["id"],#TODO: 바꾸기 or social_id 와 합치기
            social_platform = "kakao",
            social_id = kakao_user_info_response["id"],
            user_nm = kakao_user_info_response["properties"]["nickname"],#TODO: 바꾸기 or user_nick 과 합치기
            user_nick = kakao_user_info_response["properties"]["nickname"],
            birthday_date = kakao_user_info_response["kakao_account"]["birthday"],
            birthday_type = kakao_user_info_response["kakao_account"]["birthday_type"],
            email = kakao_user_info_response["kakao_account"]["email"],
            gender = kakao_user_info_response["kakao_account"]["gender"],
            age_range = kakao_user_info_response["kakao_account"]["age_range"],
            rgst_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            state = "삭제될 attribute",
            level = "free", #default free #TODO: 유료회원 받는 란? -> 추후 추가
            role = "member"
        ).save()
        return HttpResponse(f'{kakao_response.text}')

@csrf_exempt
@api_view(["POST"])
def set_signup(request):
    '''
    회원가입
    '''
    data = {"data":"temp"}
    return Response(data)

@csrf_exempt
@api_view(["POST"])
def set_signin(request):
    '''
    로그인
    '''
    data = {"data":"temp"}
    return Response(data)

@csrf_exempt
@api_view(["POST"])
def set_signout(request):
    '''
    로그아웃
    '''
    data = {"data":"temp"}
    return Response(data)

@api_view(["GET"])
def get_best_image_list(request):
    '''
    메인화면에서 샘플사진 리스트 로드
    param example) start=0&end=2 이면 index 0,1,2 사진 로드 (1,2,3 번째 사진 로드)
    '''
    start = request.GET.get("start",0)  
    end = request.GET.get("end",None)  

    #TODO: best image list table 로 바꾸기
    best_image_list = TbArkworkInfo.objects.values("img_path","image_id")
    end = len(best_image_list) if not end else int(end)

    data_list = best_image_list[int(start):end+1]
    data = {
            "result": "succ",
            "msg": "메세지",
            "data" : data_list,
            }
    return Response(data)