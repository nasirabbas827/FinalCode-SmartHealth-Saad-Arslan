from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    # Authentication
    path('', views.index, name='index'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Dashboard & Profile
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('edit-profile/', views.edit_profile, name='edit_profile'),

    # Health Records CRUD
    path('health/', views.health_records_list, name='health_records_list'),
    path('health/add/', views.health_record_create, name='health_record_create'),
    path('health/edit/<int:record_id>/', views.health_record_edit, name='health_record_edit'),
    path('health/delete/<int:record_id>/', views.health_record_delete, name='health_record_delete'),
    path('health/import/', views.health_record_import, name='health_record_import'),

    # Reports & Exports
    path('health/reports/', views.reports_view, name='reports'),
    path('generate_pdf/', views.generate_pdf, name='generate_pdf'),
    path('export_csv/', views.export_csv, name='export_csv'),        # CSV export
    path('export_excel/', views.export_excel, name='export_excel'),  # Excel export
]

# Serve media files in debug mode
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)