from django.urls import path,include
from . import views

app_name = 'common'
urlpatterns = [
    path('setSignUp/', views.set_signup, name='setSignUp'),
    path('setSignIn/', views.set_signin, name='setSignIn'),
    path('setSignOut/', views.set_signout, name='setSignOut'),
    path('getBestImageList/', views.get_best_image_list, name='getBestImageList'),
]