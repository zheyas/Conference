from django.urls import path
from . import views

app_name = 'conference_admin'

urlpatterns = [
    # Панель управления
    path('', views.admin_dashboard, name='dashboard'),

    # Панель председателя жюри
    path('jury/', views.jury_chairman_dashboard, name='jury_dashboard'),
    path('jury/section/<uuid:section_id>/reports/', views.jury_section_reports, name='jury_section_reports'),

    # Управление докладами
    path('reports/', views.report_list_admin, name='report_list'),
    path('reports/<uuid:report_id>/', views.report_detail_admin, name='report_detail'),

    # Грамоты и сертификаты
    path('reports/<uuid:report_id>/certificates/', views.manage_certificates, name='manage_certificates'),
    path('certificates/<uuid:certificate_id>/delete/', views.delete_certificate, name='delete_certificate'),

    # Управление секциями
    path('sections/', views.manage_sections, name='manage_sections'),
    path('sections/<uuid:section_id>/data/', views.get_section_data, name='get_section_data'),
    path('sections/<uuid:section_id>/jury/', views.manage_section_jury, name='manage_section_jury'),
    path('sections/<uuid:section_id>/jury/add-user/<uuid:user_id>/', views.add_user_to_jury, name='add_user_to_jury'),

    # Управление пользователями и авторами
    path('authors/', views.author_list_admin, name='author_list'),
    path('users/', views.user_list_admin, name='user_list'),
    path('users/<uuid:user_id>/role/', views.change_user_role, name='change_user_role'),
    path('sections/<uuid:section_id>/edit/', views.edit_section, name='edit_section'),  # НОВЫЙ URL
    # Статистика
    path('statistics/', views.statistics, name='statistics'),
    path('statistics/api/', views.statistics_api, name='statistics_api'),
]
