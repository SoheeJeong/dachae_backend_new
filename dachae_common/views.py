
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from rest_framework.response import Response
from rest_framework.decorators import api_view

from dachae.models import TbArkworkInfo,TbUserInfo,TbUserLog  #TODO TbArtworkInfo 를 샘플사진리스트 테이블로 바꾸기
from dachae.exceptions import DataBaseException

#TODO: timezone error 수정
#TODO: 필요한곳에 권한체크 추가

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