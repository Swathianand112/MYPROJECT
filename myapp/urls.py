from django.urls import path
from . import views

urlpatterns = [
    path('upload-and-compare/', views.upload_and_compare, name='upload_and_compare'),
]
