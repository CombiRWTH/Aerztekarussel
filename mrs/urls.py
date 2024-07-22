from django.contrib import admin
from django.urls import include, path
from rest_framework import routers

from datamodel import views

router = routers.DefaultRouter()
router.register(r'fachgebiete', views.FachgebieteViewSet, basename='fachgebiet')
router.register(r'ausbildungsbloecke', views.AusbildungsbloeckeViewSet, basename='ausbildungsblock')
router.register(r'ausbildungserfordernisse', views.AusbildungserfordernisseViewSet, basename='ausbildungserfordernis')
router.register(r'ausbildungsinhalte', views.AusbildungsinhalteViewSet, basename='ausbildungsinhalt')
router.register(r'ausbildungsinhaltetags', views.AusbildungsinhalteTagsViewSet, basename='ausbildungsinhalttag')
router.register(r'ausbildungsstellenanforderungen', views.AusbildungsStellenAnforderungenViewSet, basename='ausbildungsstellenanforderung')
router.register(r'occupationalgroups', views.OccupationalGroupsViewSet, basename="occupationalgroup")
router.register(r'organisationsgruppen', views.OrganisationsgruppeViewSet, basename='organisationsgruppe')
router.register(r'ausbildungsstaette', views.AusbildungsstaetteViewSet, basename='ausbildungsstaette')
router.register(r'ausbildungsstaettentags', views.AusbildungsstaettenTagsViewSet, basename='ausbildungsstaettetags')
router.register(r'dienstposten', views.DienstpostenViewSet, basename='dienstposten')
router.register(r'occupationalgroupsdienstposten', views.OccupationalGroupsDienstpostenViewSet, basename='occupationalgroupdienstposten')
router.register(r'associatedausbildungsbloecke', views.AssociatedAusbildungsbloeckeViewSet, basename='associatedausbildungsblock')
router.register(r'planbareausbildungsbloecke', views.PlanbareAusbildungsbloeckeViewSet, basename='planbarerausbildungsblock')
router.register(r'ausbildungsstelle', views.AusbildungsstelleViewSet, basename='ausbildungsstelle')
router.register(r'genehmigtefachgebiete', views.GenehmigteFachgebieteViewSet, basename='genehmigtesfachgebiet')
router.register(r'personen', views.PersonenViewSet, basename='person')
router.register(r'planungsparameter', views.PlanungsParameterViewSet, basename='planungsparameter')
router.register(r'allowedorganisationunits', views.AllowedOrganisationUnitsViewSet, basename='allowedorganisationunit')
router.register(r'ausbildungspfade', views.AusbildungsPfadeViewSet, basename='ausbildungspfad')
router.register(r'organisationsgruppenpriorities', views.OrganisationsGruppenPrioritiesViewSet, basename='organisationsgruppenpriority')
router.register(r'unterbrechungszeiten', views.UnterbrechungszeitenViewSet, basename='unterbrechungszeit')
router.register(r'ausbildungsbloeckepfad', views.AusbildungsbloeckePfadViewSet, basename='ausbildungsblockpfad')
router.register(r'ausbildungserfordernissepfad', views.AusbildungserfordernissePfadViewSet, basename='ausbildungserfordernispfad')
router.register(r'ausbildungsinhaltepfad', views.AusbildungsinhaltePfadViewSet, basename='ausbildungsinhaltpfad')
router.register(r'plannedausbildungsstellebyfachgebietemonths', views.PlannedAusbildungsstelleByFachgebieteMonthsViewSet, basename='plannedausbildungsstellebyfachgebietemonth')
router.register(r'parameter', views.ParameterViewSet, basename='parameter')
router.register(r'consideredausbildungstypen', views.ConsideredAusbildungstypenViewSet, basename='consideredausbildungstyp')
router.register(r'schedule', views.ScheduleViewSet, basename='schedule')
router.register(r'schedulestatistics', views.ScheduleStatisticsViewSet, basename='schedulestatistics')

urlpatterns = [
    path("datamodel/", include("datamodel.urls")),
    path('api/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path("admin/", admin.site.urls),
    path('', include('frontend.urls')),  # Hinzufügen der Frontend-URLs
]