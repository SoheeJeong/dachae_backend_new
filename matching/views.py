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
import datetime
import random
import base64

from dachae.models import TbArkworkInfo,TbCompanyInfo,TbLabelInfo,TbUploadInfo,TbUserInfo,TbUserLog,TbWishlistInfo
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
    명화 상세정보 가져오기
    '''
    data = {"data":"temp"}
    return Response(data)

@api_view(["GET"])
def get_label_list(request):
    '''
    느낌라벨 리스트 가져오기
    '''
    data = {"data":"temp"}
    return Response(data)

@csrf_exempt
@api_view(["POST"])
def set_user_image_upload(request):
    '''
    사용자 로컬이미지 업로드
    '''
    data = {"data":"temp"}
    return Response(data)

@csrf_exempt
@api_view(["POST"])
def exec_recommend(request):
    '''
    매칭 수행
    '''
    data = {"data":"temp"}
    return Response(data)

@api_view(["GET"])
def get_recommend_result(request):
    '''
    매칭 결과 보여주기
    '''
    data = {"data":"temp"}
    return Response(data)