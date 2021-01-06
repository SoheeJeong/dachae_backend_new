from django.urls import path
from . import views

app_name = 'matching'
urlpatterns = [
    path('getPictureDetailInfo/', views.get_picture_detail_info, name='getInferenceSetting'),
]