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

from dachae import models

@api_view(["GET"])
def get_picture_detail_info(request):
    data = {"data":"temp"}
    return Response(data)