from django.views import View
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from rest_framework.response import Response
from rest_framework.decorators import api_view

import os
import json
import requests

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
        #frontend 역할
        #1. 인증 코드 요청 (from frontend)
        kakao_access_code = request.GET.get('code',None)
        print(kakao_access_code)
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
        #여기부터 backend 역할
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
        #kakao_user_info_response = json.loads(kakao_response.text)
        #TODO: insert into user DB

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