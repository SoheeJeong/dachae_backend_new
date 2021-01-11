from django.contrib import admin
from django.urls import path,include
from django.conf.urls.static import static
from django.conf import settings

from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

import dachae_common.urls
import dachae_common.views
import dachae_matching.urls

schema_view = get_schema_view(
   openapi.Info(
      title="Dachae API",
      default_version='v1',
      description="엑셀 api 문서 링크: https://docs.google.com/spreadsheets/d/1IspLKL2Z2obXS_n2nJ3AK0zWLfWgUYGQnupBsiZTxJA/edit#gid=0",
      terms_of_service="https://www.google.com/policies/terms/", #TODO change
      contact=openapi.Contact(email="jshgooacc@gmail.com"),
      license=openapi.License(name="BSD License"), #TODO change
   ),
   public=False,
   permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    path('login/',dachae_common.views.login_page,name='login'), #frontend 로그인 버튼 임시 구현 - 추후 삭제 필요
    path('admin/', admin.site.urls),
    path('kakao/',dachae_common.views.KakaoLoginView.as_view(),name='kakaologin'), #kakao login
    path('naver/',dachae_common.views.NaverLoginView.as_view(),name='naverlogin'), #naver login
    path('swagger/',schema_view.with_ui(cache_timeout=0),name='swagger'),
    path('dachae/',include(dachae_common.urls,namespace='common')),
    path('dachae/matching/',include(dachae_matching.urls,namespace='macthing'))
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
