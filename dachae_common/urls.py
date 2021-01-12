from django.urls import path,include
from . import views

app_name = 'common'
urlpatterns = [
    path('setSignUp/', views.set_signup, name='setSignUp'),
    path('setLogIn/', views.set_login, name='setLogIn'),
    path('setLogOut/', views.set_logout, name='setLogOut'),
    path('refreshToken/',views.refresh_token,name='refreshToken'),
    path('getUserInfo/', views.get_user_info, name='getUserInfo'),
]