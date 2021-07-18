from django.views import View
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect
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
from dachae.utils import age_range_calulator,get_expire_time_from_expires_in,check_token_isvalid,get_access_token,get_social_user_info


#TODO: service 구조로 refactoring
#TODO: 필요한곳에 권한체크 추가
#TODO: refresh token, delete token, naver logout

#frontend 역할 #TODO: 함수 제거
@csrf_exempt
def login_page(request):
    naver_login_data = {
        "CLIENT_ID": (os.getenv("NAVER_APP_KEY")),
        "REDIRECT_URI": (os.getenv("NAVER_LOGIN_REDIRECT_URI")),
        "SIGNUP_REDIRECT_URI": (os.getenv("NAVER_SIGNUP_REDIRECT_URI")),
        "STATE":os.getenv("NAVER_API_SECRET"),
    }
    kakao_login_data = {
        "REST_API_KEY":os.getenv("KAKAO_APP_KEY"),
        "REDIRECT_URI":os.getenv("KAKAO_LOGIN_REDIRECT_URI"),
        "SIGNUP_REDIRECT_URI": (os.getenv("KAKAO_SIGNUP_REDIRECT_URI")),
    }
    kakao_logout_data = {
        "REST_API_KEY":os.getenv("KAKAO_APP_KEY"),
        "LOGOUT_REDIRECT_URI":os.getenv("KAKAO_LOGOUT_REDIRECT_URI"),
    }
    return render(request,'login.html',{'login_data':kakao_login_data,'logout_data':kakao_logout_data,"naver_login_data":naver_login_data})

@api_view(["GET"])
def set_kakao_signup(request):
    '''
    새로운 회원 회원가입 실행
    소셜로그인에서 넘어온 회원가입 페이지
    '''
    #1.인증코드 요청
    access_code = request.GET.get('code',None)
    if not access_code: raise exceptions.InvalidAccessTokenException
    social_platform = "kakao"
    #2.access token 요청
    try:
        kakao_response_result = get_access_token(access_code,"kakao")
        access_token = kakao_response_result["access_token"]
        refresh_token = kakao_response_result["refresh_token"]
        expires_in = kakao_response_result["expires_in"]
    except:
        raise exceptions.ServerConnectionFailedException
    if not access_token: raise exceptions.InvalidAccessTokenException
    if not expires_in or not social_platform: raise exceptions.ParameterMissingException
    
    #3.사용자 정보 요청
    try:
        user_info_response = get_social_user_info(access_token,"kakao")
        social_id = user_info_response["id"] if "id" in user_info_response else None
        if not social_id: raise exceptions.InvalidAccessTokenException
    except:
        raise exceptions.ServerConnectionFailedException

    # 이미 존재하는 회원
    if TbUserInfo.objects.filter(social_platform=social_platform,social_id=social_id).exists():
        raise exceptions.ExistMemberException

    # age_range = age_range_calulator(birthday_date) 
    expire_time = get_expire_time_from_expires_in(expires_in)

    try:
        #insert into user DB
        user = TbUserInfo(
            social_platform = social_platform,
            social_id = social_id,
            # user_nm = user_nm,
            # email = email,
            rgst_date = datetime.now(),
            # state = "active",
            # level = "free", #default free #TODO: 유료회원 받는 란 -> 추후 추가
            # role = "member"
        )
        user.save()
        user_id = user.user_id
        #access token 정보 저장
        server_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        userauth = TbUserAuth(
            user_id = user_id,
            access_token = access_token,
            refresh_token = refresh_token,
            expire_time = expire_time,
            created_time = server_time
        )
        userauth.save()
    except:
       raise exceptions.DataBaseException

    #권한정보, 사용자정보 넘겨주기
    user_data = {
        'access_token':access_token,
        'refresh_token':refresh_token,
        'expires_in':expires_in,
        'user_id': user.user_id,
        'social_platform':user.social_platform,
        'social_id': user.social_id,
    }
    return Response(user_data)

@api_view(["GET"])
def set_naver_signup(request):
    '''
    네이버 회원가입 실행
    '''
    #1.인증코드 요청
    access_code = request.GET.get('code',None)
    if not access_code:  raise exceptions.InvalidAccessTokenException
    social_platform = "naver"

    #2. access token 요청
    try:
        naver_response_result = get_access_token(access_code,"naver")
        access_token = naver_response_result["access_token"]
        refresh_token = naver_response_result["refresh_token"]
        expires_in = naver_response_result["expires_in"]
    except:
        raise exceptions.ServerConnectionFailedException
    if not access_token: raise exceptions.InvalidAccessTokenException
    if not expires_in or not social_platform: raise exceptions.ParameterMissingException
    
    #3. 사용자 정보 요청
    try:
        user_info_response = get_social_user_info(access_token,"naver")
        social_id = user_info_response["id"] if "id" in user_info_response else None
        if not social_id: raise exceptions.InvalidAccessTokenException
    except:
        raise exceptions.ServerConnectionFailedException

    if TbUserInfo.objects.filter(social_platform=social_platform,social_id=social_id).exists():
        raise exceptions.ExistMemberException

    # age_range = age_range_calulator(birthday_date) 
    expire_time = get_expire_time_from_expires_in(expires_in)

    try:
        #insert into user DB
        user = TbUserInfo(
            social_platform = "naver",
            social_id = social_id,
            #user_nm = user_nm,
            #email = email,
            rgst_date = datetime.now(),
            #state = state,
            #level = "free", #default free #TODO: 유료회원 받는 란 -> 추후 추가
            #role = "member"
        )
        user.save()
        user_id = user.user_id
        #access token 정보 저장
        server_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        userauth = TbUserAuth(
            user_id = user_id,
            access_token = access_token,
            refresh_token = refresh_token,
            expire_time = expire_time,
            created_time = server_time
        )
        userauth.save()       
    except:
       raise exceptions.DataBaseException

    #권한정보, 사용자정보 넘겨주기
    user_data = {
        'access_token':access_token,
        'refresh_token':refresh_token,
        'expires_in':expires_in,
        'user_id': user_id,
        'social_platform':user.social_platform,
        'social_id': user.social_id,
    }
    return Response(user_data)

@api_view(["GET"])
def set_kakao_login(request): 
    """
    카카오 로그인
    """
    #1.인증코드 요청
    access_code = request.GET.get('code',None)
    if not access_code: raise exceptions.InvalidAccessTokenException
    social_platform = "kakao"
    #2.access token 요청
    try:
        kakao_response_result = get_access_token(access_code,"kakao")
        access_token = kakao_response_result["access_token"]
        refresh_token = kakao_response_result["refresh_token"]
        expires_in = kakao_response_result["expires_in"]
    except:
        raise exceptions.ServerConnectionFailedException
    if not access_token:  raise exceptions.InvalidAccessTokenException
    if not expires_in or not social_platform: raise exceptions.ParameterMissingException
    #3.사용자 정보 요청
    try:
        user_info_response = get_social_user_info(access_token,"kakao")
        social_id = user_info_response["id"] if "id" in user_info_response else None
        if not social_id:  raise exceptions.InvalidAccessTokenException
    except:
        raise exceptions.InvalidAccessTokenException
    
    #이미 존재하는 회원이면 - 로그인 실행
    if TbUserInfo.objects.filter(social_platform=social_platform,social_id=social_id).exists():
        user = TbUserInfo.objects.get(social_id=social_id)
        #TODO: 예외처리 추가
        #access token 정보 저장
        if TbUserAuth.objects.filter(user_id=user.user_id).exists(): #이미 로그인된 사용자
            raise exceptions.LoggedException
        expire_time = get_expire_time_from_expires_in(expires_in)
        server_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        TbUserAuth(
            user_id = user.user_id,
            access_token = access_token,
            refresh_token = refresh_token,
            expire_time = expire_time,
            created_time = server_time
        ).save()
        #권한정보, 사용자정보 넘겨주기
        user_data = {
            'access_token':access_token,
            'refresh_token':refresh_token,
            'expires_in':expires_in,
            'user_id': user.user_id,
            'social_platform':user.social_platform,
            'social_id': user.social_id,
        }
        return JsonResponse(user_data)
    #새로운 회원이면 - registered=0 으로 세팅 (바로 회원가입 페이지로)
    else:
        raise exceptions.NewMemberException

@api_view(["GET"])
def set_naver_login(request):
    '''
    네이버 로그인
    '''
    access_code = request.GET.get('code',None)
    if not access_code:  raise exceptions.InvalidAccessTokenException
    social_platform = "naver"

    #2. access token 요청
    try:
        naver_response_result = get_access_token(access_code,"naver")
        access_token = naver_response_result["access_token"]
        refresh_token = naver_response_result["refresh_token"]
        expires_in = naver_response_result["expires_in"]
    except:
        raise exceptions.ServerConnectionFailedException
    if not access_token: raise exceptions.InvalidAccessTokenException
    if not expires_in or not social_platform: raise exceptions.ParameterMissingException
    
    #3. 사용자 정보 요청
    try:
        user_info_response = get_social_user_info(access_token,"naver")
        social_id = user_info_response["id"] if "id" in user_info_response else None
        if not social_id: raise exceptions.InvalidAccessTokenException
    except:
        raise exceptions.ServerConnectionFailedException

    #이미 존재하는 회원이면 - 로그인 실행
    if TbUserInfo.objects.filter(social_platform=social_platform,social_id=social_id).exists():
        user = TbUserInfo.objects.get(social_platform=social_platform,social_id=social_id)
        #TODO: 예외처리 추가
        #access token 정보 저장
        if TbUserAuth.objects.filter(user_id=user.user_id).exists():
            raise exceptions.LoggedException
        expire_time = get_expire_time_from_expires_in(expires_in)
        server_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        TbUserAuth(
            user_id = user.user_id,
            access_token = access_token,
            refresh_token = refresh_token,
            expire_time = expire_time,
            created_time = server_time
        ).save()
        #권한정보, 사용자정보 넘겨주기
        user_data = {
            'access_token':access_token,
            'refresh_token':refresh_token,
            'expires_in':expires_in,
            'user_id': user.user_id,
            'social_platform':user.social_platform,
            'social_id': user.social_id,
        }
        return JsonResponse(user_data)

@api_view(["GET"])
def set_logout(request):
    '''
    로그아웃
    '''
    header = request.headers
    access_token = header['Authorization'] if 'Authorization' in header else None
    user_id = request.GET.get('user_id',None)
    social_platform = request.GET.get('social_platform',None)
    
    #valid user 인지 검사
    validation = check_token_isvalid(access_token,user_id)
    if validation == "not logged":
        raise exceptions.LoginRequiredException

    if social_platform == "kakao":
        url = "https://kapi.kakao.com/v1/user/logout"
        headers = {
                'Authorization':f'Bearer {access_token}',
                'Content-type':'application/x-www-form-urlencoded;charset=utf-8',
            }
        token_kakao_response = requests.post(url,headers=headers)
        kakao_response_result = json.loads(token_kakao_response.text)
        social_id = kakao_response_result["id"]
        #delete token
        TbUserAuth.objects.filter(user_id=user_id).delete()
    elif social_platform == "naver":
        #delete token
        TbUserAuth.objects.filter(user_id=user_id).delete()
        #return redirect("https://nid.naver.com/nidlogin.logout")

    data = {
        "social_platform":social_platform,
        "user_id":user_id,
        "result":"succ"
        }
    return Response(data)


@api_view(["GET"])
def refresh_token(request):
    '''
    토큰갱신
    '''
    header = request.headers
    refresh_token = header['Authorization'] if 'Authorization' in header else None
    user_id = request.GET.get("user_id",None)
    social_platform = request.GET.get("social_platform",None)

    if not user_id or not social_platform:  raise exceptions.ParameterMissingException
    
    if TbUserAuth.objects.filter(user_id=user_id).exists():
        userauth = TbUserAuth.objects.get(user_id=user_id)
        #다시 로그인 필요
        if not userauth.refresh_token: raise exceptions.ExpiredRefreshTokenException
        elif not refresh_token: raise exceptions.ParameterMissingException
    
    try:
        if social_platform == "kakao":
            url = "https://kauth.kakao.com/oauth/token"
            headers = {'Content-type':'application/x-www-form-urlencoded;charset=utf-8'}
            body = {
                "grant_type": "refresh_token",
                "client_id": os.getenv("KAKAO_APP_KEY"),
                "refresh_token" : refresh_token
            }
            token_kakao_response = requests.post(url,headers=headers,data=body)
            kakao_response_result = json.loads(token_kakao_response.text)
            new_access_token = kakao_response_result["access_token"]
            new_expires_in = kakao_response_result["expires_in"]
            new_refresh_token = None if "refresh_token" not in kakao_response_result else kakao_response_result["refresh_token"]

        elif social_platform == "naver":
            #TODO: 코드추가
            print("naver")
    except:
        raise exceptions.ServerConnectionFailedException

    expire_time = get_expire_time_from_expires_in(new_expires_in)
    server_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    #access token 정보 변경
    try:
        userauth = TbUserAuth.objects.get(user_id=user_id)
        #if not userauth: print("user not exist")
        userauth.access_token = new_access_token
        if new_refresh_token:
            userauth.refresh_token = new_refresh_token
        userauth.expire_time = expire_time
        userauth.modified_time = server_time
        userauth.save()
    except:
        raise exceptions.DatabaseException

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
    if validation == "not logged": raise exceptions.LoginRequiredException
    
    #TODO: 회원 DB에서 삭제

    data = {"result":"succ"}
    return Response(data)