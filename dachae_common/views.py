from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.decorators import api_view

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
    '''
    data = {"data":"temp"}
    return Response(data)