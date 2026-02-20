from django.urls import path
from . import views

app_name = 'docs'

urlpatterns = [
    path('info/', views.conference_info, name='info'),
    path('download/<int:doc_id>/', views.download_document, name='download_document'),
]
