from django.urls import path
from . import views

app_name = 'matching'
urlpatterns = [
    path('setUploadAndRecommend/', views.set_upload_and_recommend, name='setUploadAndRecommend'),
    path('getDefaultRecommend/', views.get_default_recommend, name='getDefaultRecommend')
]