from django.urls import path,include
from . import views

app_name = 'common'
urlpatterns = [
    path('login/',views.login_page,name='login'), #frontend 로그인 버튼 임시 구현 - 추후 삭제 필요
    path('setKakaoSignup/', views.set_kakao_signup, name='setKakaoSignup'),
    path('setNaverSignup/', views.set_naver_signup, name='setNaverSignup'),
    path('setKakaoLogin/', views.set_kakao_login, name='setKakaoLogin'),
    path('setNaverLogin/', views.set_naver_login, name='setNaverLogin'),
    path('setLogOut/', views.set_logout, name='setLogOut'),
    path('refreshToken/',views.refresh_token,name='refreshToken'),
    path('setWithdrawal/',views.set_withdrawal,name='setWithdrawal')
]