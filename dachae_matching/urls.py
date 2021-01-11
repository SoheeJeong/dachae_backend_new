from django.urls import path
from . import views

app_name = 'matching'
urlpatterns = [
    path('getBestImageList/', views.get_best_image_list, name='getBestImageList'),
    path('getPictureFilteredResult/', views.get_picture_filtered_result, name='getPictureFilteredResult'),
    path('getPictureDetailInfo/', views.get_picture_detail_info, name='getInferenceSetting'),
    path('getLabelList/', views.get_label_list, name='getLabelList'),
    path('setUserImageUpload/', views.set_user_image_upload, name='setUserImageUpload'),
    path('execRecommend/', views.exec_recommend, name='execRecommend'),
    path('setWishList/', views.set_wish_list, name='setWishList'),
    path('delWishList/<str:user_id>/<int:img_id>/', views.del_wish_list, name='delWishList'),
    path('execPurchase/', views.exec_purchase, name='execPurchase'),
]