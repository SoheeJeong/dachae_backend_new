from django.urls import path
from . import views

app_name = 'matching'
urlpatterns = [
    path('getPictureFilteredResult/', views.get_picture_filtered_result, name='getPictureFilteredResult'),
    path('getPictureDetailInfo/', views.get_picture_detail_info, name='getInferenceSetting'),
    path('getLabelList/', views.get_label_list, name='getLabelList'),
    path('setUserImageUpload/', views.set_user_image_upload, name='setUserImageUpload'),
    path('execRecommend/', views.exec_recommend, name='execRecommend'),
    path('getRecommendResult/', views.get_recommend_result, name='getRecommendResult'),
]