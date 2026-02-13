# talks/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('reports/', views.report_list, name='report_list'),
    path('reports/create/', views.report_create, name='report_create'),
    path('reports/<uuid:report_id>/', views.report_detail, name='report_detail'),
    path('reports/<uuid:report_id>/edit/', views.report_edit, name='report_edit'),
    path('reports/<uuid:report_id>/authors/', views.report_edit_authors, name='report_edit_authors'),
    path('reports/<uuid:report_id>/resubmit/', views.report_resubmit, name='report_resubmit'),
]
