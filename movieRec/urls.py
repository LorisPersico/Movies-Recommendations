from django.urls import path

from . import views

app_name = 'movieRec'
urlpatterns = [
    path('', views.index, name='index'),
]
