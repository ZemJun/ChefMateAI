from django.urls import path
from . import views

app_name = 'recipes'

urlpatterns = [
    path('test/', views.test_page, name='test_page'),
] 