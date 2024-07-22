from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.allgemein, name='allgemein'),
    path('registration/', views.register, name='registration'),
    path('login/', views.user_login, name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='allgemein'), name='logout'),
    path('admin-page/', views.admin, name='admin'),
    path('student/', views.student, name='student'),
    path('studentAusfall/', views.studentAusfall, name='studentAusfall'),
    path('create_student_ausfall/', views.create_student_ausfall, name='create_student_ausfall'),
    path('aerg/', views.aerg, name='aerg'),
    path('serg/', views.serg, name='serg'),
    path('adminaktuell/', views.adminaktuell, name='adminaktuell'),
    path('create_or_edit_hospital/', views.create_or_edit_hospital, name='create_or_edit_hospital'),
    path('create_or_edit_hospital/<int:organisation_id>/', views.create_or_edit_hospital, name='create_or_edit_hospital_with_id'),
    path('api/organisationsgruppen/', views.get_organisationsgruppen, name='get_organisationsgruppen'),
    path('api/schedule/', views.get_schedule, name='get_schedule'),
    path('api/objectiveweights/', views.set_objectiveweights, name='set_objectiveweights'),
    path('set_objectiveweights', views.set_objectiveweights, name='set_objectiveweights'),
    path('delete_organisation/<int:id>/', views.delete_organisation, name='delete_organisation'),
    path('detailansicht_auswertung/', views.detailansicht_auswertung, name='detailansicht_auswertung'),
    path('bloecke_auswertung/', views.bloecke_auswertung, name='bloecke_auswertung'),
    path('import_export/', views.import_export, name='import_export'),
    path('activate_admin_primary/', views.activate_admin_primary, name='activate_admin_primary'),
    path('activate_user_primary/', views.activate_user_primary, name='activate_user_primary'),
    path('import_file/', views.import_file, name='import_file'),
    path('export_file_default/', views.export_file_default, name='export_file_default'),
    path('export_file_only_datamodel/', views.export_file_only_datamodel, name='export_file_only_datamodel'),
    path('statistik_auswertung/', views.statistik_auswertung, name='statistik_auswertung'),
]