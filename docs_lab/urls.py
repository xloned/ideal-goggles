"""URL-маршруты для Лаб. №6 — документирование кода."""

from django.urls import path
from . import views

app_name = 'docs_lab'

urlpatterns = [
    path('', views.docs_index, name='index'),
    path('<str:module_key>/', views.docs_source, name='source'),
]
