from django.urls import path,include
from . import views

app_name = 'common'
urlpatterns = [
    path('login/',views.login_page,name='login'), #frontend 로그인 버튼 임시 구현 - 추후 삭제 필요
    path('kakao/',views.set_login,name='kakaologin'), #kakao login(temp) - 추후삭제
    path('naver/',views.NaverLoginView.as_view(),name='naverlogin'), #naver login(temp) - 추후삭제
    path('setSignUp/', views.set_signup, name='setSignUp'),
    path('setLogIn/', views.set_login, name='setLogIn'),
    path('setLogOut/', views.set_logout, name='setLogOut'),
    path('refreshToken/',views.refresh_token,name='refreshToken'),
    path('setWithdrawal/',views.set_withdrawal,name='setWithdrawal')
]