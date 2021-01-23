from django.views import View
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.conf import settings

import os
import json
#import jwt #json web tokens
import requests
import urllib
from datetime import datetime

from dachae.models import TbUserInfo,TbUserLog,TbUserAuth
from dachae import exceptions
from dachae.utils import age_range_calulator,get_expire_time_from_expires_in,check_token_isvalid


#TODO: service 구조로 refactoring
#TODO: 필요한곳에 권한체크 추가
#TODO: refresh token, delete token, naver logout
#TODO: 카카오톡 메시지 연동 (FAQ, 문의하기)

@api_view(["POST"])
def set_signup(request):
    '''
    새로운 회원 회원가입 실행
    소셜로그인에서 넘어온 회원가입 페이지
    '''
    header = request.headers
    access_token = header['Authorization'] if 'Authorization' in header else None
    body = json.loads(request.body.decode("utf-8"))
    #TODO: frontend에서 입력형식 체크 요청
    #TODO: default None 추가
    social_platform = None if "social_platform" not in body else body["social_platform"]
    social_id = None if "social_id" not in body else body["social_id"]
    user_nm = None if "user_nm" not in body else body["user_nm"]
    level = None if "level" not in body else body["level"]
    role = None if "role" not in body else body["role"]
    birthday_date = None if "birthday_date" not in body else body["birthday_date"] 
    email = None if "email" not in body else body["email"]
    gender = None if "gender" not in body else body["gender"]
    expires_in = None if "expires_in" not in body else body["expires_in"]

    if social_platform and social_id and user_nm and level and role and birthday_date and email and gender and expires_in is None:
        raise exceptions.ParameterMissingException

    age_range = age_range_calulator(birthday_date) 
    expire_time = get_expire_time_from_expires_in(expires_in)

    #try:
    #insert into user DB
    user_info = TbUserInfo(
        social_platform = social_platform,
        social_id = social_id,
        user_nm = user_nm,
        birthday_date = birthday_date,
        email = email,
        gender = gender,
        age_range = age_range,
        rgst_date = datetime.now(),
        state = "active",
        level = "free", #default free #TODO: 유료회원 받는 란 -> 추후 추가
        role = "member"
    )
    user_info.save()
    user_id = user_info.user_id
    #access token 정보 저장
    server_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    TbUserAuth(
        user_id = user_id,
        access_token = access_token,
        expire_time = expire_time,
        created_time = server_time
    ).save()

    #except:
    #   raise exceptions.DataBaseException


    response = {
        "result": "succ",
        "msg": "메세지"
    }
    return Response(response)

#frontend 역할 #TODO: 함수 제거
@csrf_exempt
def login_page(request):
    naver_login_data = {
        "CLIENT_ID": (os.getenv("NAVER_APP_KEY")),
        "REDIRECT_URI": (os.getenv("NAVER_LOGIN_REDIRECT_URI")),
        "STATE":os.getenv("NAVER_API_SECRET"),
    }
    kakao_login_data = {
        "REST_API_KEY":os.getenv("KAKAO_APP_KEY"),
        "REDIRECT_URI":os.getenv("KAKAO_LOGIN_REDIRECT_URI"),
    }
    kakao_logout_data = {
        "REST_API_KEY":os.getenv("KAKAO_APP_KEY"),
        "LOGOUT_REDIRECT_URI":os.getenv("LOGOUT_REDIRECT_URI"),
    }
    return render(request,'login.html',{'login_data':kakao_login_data,'logout_data':kakao_logout_data,"naver_login_data":naver_login_data})

###frontend 역할 -> TODO: 코드 제거
class NaverLoginView(View):
    def get(self,request):
        # #1. 인증 코드 요청 (from frontend)
        # kakao_access_code = request.GET.get('code',None)
        # #2. access token 요청
        # url = 'https://kauth.kakao.com/oauth/token'
        # headers = {'Content-type':'application/x-www-form-urlencoded;charset=utf-8'}
        # body = {
        #     'grant_type' : 'authorization_code',
        #     'client_id' : os.getenv("KAKAO_APP_KEY"),
        #     'redirect_uri' : os.getenv("REDIRECT_URI"),
        #     'code' : kakao_access_code
        # }
        # token_kakao_response = requests.post(url,headers=headers,data=body)
        #frontend - for test
        naver_access_code = request.GET.get('code',None)
        #2. access token 요청
        url = 'https://nid.naver.com/oauth2.0/token'
        headers = {'Content-type':'application/x-www-form-urlencoded;charset=utf-8'}
        body = {
            'grant_type' : 'authorization_code',
            'client_id' : os.getenv("NAVER_APP_KEY"),
            'client_secret' : os.getenv("NAVER_API_SECRET"),
            'redirect_uri' : os.getenv("NAVER_LOGIN_REDIRECT_URI"),
            'code' : naver_access_code
        }
        token_naver_response = requests.post(url,headers=headers,data=body)
        naver_response_result = json.loads(token_naver_response.text)
        return HttpResponse(f'{naver_response_result}')

@api_view(["GET"])
def set_login(request):
    '''
    카카오, 네이버 로그인
    '''
    ###여기부터 backend 역할
    header = request.headers
    access_token = header['Authorization'] if 'Authorization' in header else None
    expires_in = request.GET.get("expires_in",None)
    social_platform = request.GET.get("social_platform",None)

    if not access_token:
        raise exceptions.InvalidAccessTokenException
    if not expires_in or not social_platform:
        raise exceptions.ParameterMissingException
    
    #3. 사용자 정보 요청
    try:
        if social_platform == "kakao":
            url = 'https://kapi.kakao.com/v2/user/me'
        
            headers = {
                'Authorization':f'Bearer {access_token}',
                'Content-type':'application/x-www-form-urlencoded;charset=utf-8',
            }
            body = {
                #'property_keys':'["properties.nickname","properties.profile_image","properties.thumbnail_image"]'
            }
            login_response = requests.post(url,headers=headers,data=body)
            user_info_response = json.loads(login_response.text)
            social_id = user_info_response["id"] if "id" in user_info_response else None
            if not social_id:
                raise exceptions.InvalidAccessTokenException

        elif social_platform == "naver":
            url = "https://openapi.naver.com/v1/nid/me"
            header = "Bearer " + access_token # Bearer 다음에 공백 추가
            request = urllib.request.Request(url)
            request.add_header("Authorization", header)
            response = urllib.request.urlopen(request)
            rescode = response.getcode()
            if(rescode==200):
                user_info_response = json.loads(response.read().decode('utf-8'))["response"]
            social_id = user_info_response["id"] if "id" in user_info_response else None
            if not social_id:
                raise exceptions.InvalidAccessTokenException
    except:
        raise exceptions.InvalidAccessTokenException
    
    #이미 존재하는 회원이면 - 로그인 실행
    if TbUserInfo.objects.filter(social_platform=social_platform,social_id=social_id).exists():
        user = TbUserInfo.objects.get(social_id=social_id)
        #jwt_token = jwt.encode({'id':user.user_id},settings.SECRET_KEY,algorithm='HS256').decode('utf-8')
        
        #TODO: 예외처리 추가
        #TODO: 이미 다른 기기에서 로그인 되어있는지 검사 (TbUserAuth 테이블 검사) - 새로 로그인 하시겠습니까? -> ok시 UserAuth 에서 row 삭제
        #TODO: TbUserAuth table의 access token, expire_time, modified_time 정보 update
        expire_time = get_expire_time_from_expires_in(expires_in)

        #권한정보, 사용자정보 넘겨주기
        user_data = {
            'registered':1, #이미 회원가입된 사용자 -> 추가 회원가입 페이지 불필요, 메인페이지로 redirect
            'user_id': user.user_id,
            'social_platform':user.social_platform,
            'social_id': user.social_id,
            'user_nm' : user.user_nm,
            'level' : user.level, #default free 
            'role' : user.role,
        }
        return JsonResponse(user_data)

    #새로운 회원이면 - registered=0 으로 세팅 (바로 회원가입 페이지로)
    else:
        user_data = {
            'registered':0,
            'social_id': social_id,
            'social_platform':social_platform
        }
        return JsonResponse(user_data)

@api_view(["GET"])
def set_logout(request):
    '''
    로그아웃
    '''
    header = request.headers
    access_token = header['Authorization'] if 'Authorization' in header else None
    user_id = request.GET.get("user_id",None)

    #valid user 인지 검사
    validation = check_token_isvalid(access_token,user_id)
    if validation == "not logged":
        raise exceptions.LoginRequiredException
    
    # kakao logout
    # "https://kauth.kakao.com/oauth/logout?client_id={{logout_data.REST_API_KEY}}&logout_redirect_uri={{logout_data.LOGOUT_REDIRECT_URI}}"
    
    #TODO: delete token

    data = {"result":"succ"}
    return Response(data)


@api_view(["GET"])
def refresh_token(request):
    '''
    토큰갱신
    '''
    header = request.headers
    refresh_token = header['Authorization'] if 'Authorization' in header else None
    user_id = request.GET.get("user_id",None)

    #TODO: token 변경

    data = {"result":"succ"}
    return Response(data)


@api_view(["GET"])
def set_withdrawal(request):
    '''
    회원탈퇴
    '''
    header = request.headers
    access_token = header['Authorization'] if 'Authorization' in header else None
    user_id = request.GET.get("user_id",None)

    #valid user 인지 검사
    validation = check_token_isvalid(access_token,user_id)
    if validation == "not logged":
        raise exceptions.LoginRequiredException
    
    #TODO: 회원 DB에서 삭제

    data = {"result":"succ"}
    return Response(data)

@api_view(["GET"])
def get_user_info(request):
    '''
    사용자 정보 가져오기
    '''
    header = request.headers
    access_token = header['Authorization'] if 'Authorization' in header else None
    user_id = request.GET.get("user_id",None)

    #valid user 인지 검사
    validation = check_token_isvalid(access_token,user_id)
    if validation == "not logged":
        raise exceptions.LoginRequiredException
    
    #TODO: 사용자 정보 가져오기
    data = {
        'user_id': 123456,
        'social_platform': 'naver',
        'user_nm' : "닉네임",            
        'level' : 'free', 
        'role' : 'member',
        "email":"wjdthgmlgo@naver.com",
        "gender":"female",
        "birthday_date":"1998-06-16",
        "rgst_date":"2021-01-11 22:09:38",
    }
    return Response(data)