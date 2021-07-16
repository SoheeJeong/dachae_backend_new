from django.urls import path
from . import views

app_name = 'matching'
urlpatterns = [
    path('getPictureDetailInfo/', views.get_picture_detail_info, name='getPictureDetailInfo'),
    path('setUploadAndRecommend/', views.set_upload_and_recommend, name='setUploadAndRecommend'),
    #path('execRecommend/', views.exec_recommend, name='execRecommend'),
]