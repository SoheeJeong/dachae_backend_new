from django.urls import path,include
from . import views

app_name = 'common'
urlpatterns = [
    path('login/',views.login_page,name='login'), #frontend 로그인 버튼 임시 구현 - 추후 삭제 필요
    path('setKakaoLoginSignup/', views.set_kakao_login_signup, name='setKakaoLoginSignup'),
    path('setNaverLoginSignup/', views.set_naver_login_signup, name='setNaverLoginSignup'),
    #path('setKakaoSignup/', views.set_kakao_signup, name='setKakaoSignup'),
    #path('setNaverSignup/', views.set_naver_signup, name='setNaverSignup'),
    #path('setKakaoLogin/', views.set_kakao_login, name='setKakaoLogin'),
    #path('setNaverLogin/', views.set_naver_login, name='setNaverLogin'),
    path('setLogout/', views.set_logout, name='setLogout'),
    path('refreshToken/',views.refresh_token,name='refreshToken'),
    path('setWithdrawal/',views.set_withdrawal,name='setWithdrawal')
]