import random
from django.db.models import Max, Min

from django.shortcuts import render
from django.http import HttpResponse
from django.http import JsonResponse

from datamodel.importer import load_file
from datamodel.reader import read_db
from datamodel.schedule_service import save_schedule
from datamodel.models import *
from datamodel.serializers import *

from rest_framework import permissions, viewsets, mixins

class FachgebieteViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Fachgebiete to be viewed or edited.
    """
    queryset = Fachgebiete.objects.all()
    serializer_class = FachgebieteSerializer
    permission_classes = [permissions.IsAuthenticated]

class AusbildungsbloeckeViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Ausbildungsblöcke to be viewed or edited.
    """
    queryset = Ausbildungsbloecke.objects.all()
    serializer_class = AusbildungsbloeckeSerializer
    permission_classes = [permissions.IsAuthenticated]

class AusbildungserfordernisseViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Ausbildungserfordernisse to be viewed or edited.
    """
    queryset = Ausbildungserfordernisse.objects.all()
    serializer_class = AusbildungserfordernisseSerializer
    permission_classes = [permissions.IsAuthenticated]

class AusbildungsinhalteViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Ausbildungsinhalte to be viewed or edited.
    """
    queryset = Ausbildungsinhalte.objects.all()
    serializer_class = AusbildungsinhalteSerializer
    permission_classes = [permissions.IsAuthenticated]

class AusbildungsinhalteTagsViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows AusbildungsinhalteTags to be viewed or edited.
    """
    queryset = AusbildungsinhalteTags.objects.all()
    serializer_class = AusbildungsinhalteTagsSerializer
    permission_classes = [permissions.IsAuthenticated]

class AusbildungsStellenAnforderungenViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows AusbildungsStellenAnforderungen to be viewed or edited.
    """
    queryset = AusbildungsStellenAnforderungen.objects.all()
    serializer_class = AusbildungsStellenAnforderungenSerializer
    permission_classes = [permissions.IsAuthenticated]

class OccupationalGroupsViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Occupational Groups to be viewed or edited.
    """
    queryset = OccupationalGroups.objects.all()
    serializer_class = OccupationalGroupsSerializer
    permission_classes = [permissions.IsAuthenticated]

##########################################
class OrganisationsgruppeViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows organisation groups to be viewed or edited.
    """
    queryset = Organisationsgruppe.objects.all()
    serializer_class = OrganisationsgruppeSerializer
    permission_classes = [permissions.IsAuthenticated]


class AusbildungsstaetteViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Ausbildungsstaette to be viewed or edited.
    """
    queryset = Ausbildungsstaette.objects.all()
    serializer_class = AusbildungsstaetteSerializer
    permission_classes = [permissions.IsAuthenticated]

class AusbildungsstaettenTagsViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows AusbildungsstaettenTags to be viewed or edited.
    """
    queryset = AusbildungsstaettenTags.objects.all()
    serializer_class = AusbildungsstaettenTagsSerializer
    permission_classes = [permissions.IsAuthenticated]

class DienstpostenViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Dienstposten to be viewed or edited.
    """
    queryset = Dienstposten.objects.all()
    serializer_class = DienstpostenSerializer
    permission_classes = [permissions.IsAuthenticated]

class OccupationalGroupsDienstpostenViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows OccupationalGroupsDienstposten to be viewed or edited.
    """
    queryset = OccupationalGroupsDienstposten.objects.all()
    serializer_class = OccupationalGroupsDienstpostenSerializer
    permission_classes = [permissions.IsAuthenticated]

class AssociatedAusbildungsbloeckeViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows AssociatedAusbildungsbloecke to be viewed or edited.
    """
    queryset = AssociatedAusbildungsbloecke.objects.all()
    serializer_class = AssociatedAusbildungsbloeckeSerializer
    permission_classes = [permissions.IsAuthenticated]

class PlanbareAusbildungsbloeckeViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows PlanbareAusbildungsbloecke to be viewed or edited.
    """
    queryset = PlanbareAusbildungsbloecke.objects.all()
    serializer_class = PlanbareAusbildungsbloeckeSerializer
    permission_classes = [permissions.IsAuthenticated]

class AusbildungsstelleViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Ausbildungsstellen to be viewed or edited.
    """
    queryset = Ausbildungsstelle.objects.all()
    serializer_class = AusbildungsstelleSerializer
    permission_classes = [permissions.IsAuthenticated]

class GenehmigteFachgebieteViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows GenehmigteFachgebiete to be viewed or edited.
    """
    queryset = GenehmigteFachgebiete.objects.all()
    serializer_class = GenehmigteFachgebieteSerializer
    permission_classes = [permissions.IsAuthenticated]

class PersonenViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Personen to be viewed or edited.
    """
    queryset = Personen.objects.all()
    serializer_class = PersonenSerializer
    permission_classes = [permissions.IsAuthenticated]

class PlanungsParameterViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows PlanungsParameter to be viewed or edited.
    """
    queryset = PlanungsParameter.objects.all()
    serializer_class = PlanungsParameterSerializer
    permission_classes = [permissions.IsAuthenticated]

class AllowedOrganisationUnitsViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows AllowedOrganisationUnits to be viewed or edited.
    """
    queryset = AllowedOrganisationUnits.objects.all()
    serializer_class = AllowedOrganisationUnitsSerializer
    permission_classes = [permissions.IsAuthenticated]

class AusbildungsPfadeViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows AusbildungsPfade to be viewed or edited.
    """
    queryset = AusbildungsPfade.objects.all()
    serializer_class = AusbildungsPfadeSerializer
    permission_classes = [permissions.IsAuthenticated]

class OrganisationsGruppenPrioritiesViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows OrganisationsGruppenPriorities to be viewed or edited.
    """
    queryset = OrganisationsGruppenPriorities.objects.all()
    serializer_class = OrganisationsGruppenPrioritiesSerializer
    permission_classes = [permissions.IsAuthenticated]

class UnterbrechungszeitenViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Unterbrechungszeiten to be viewed or edited.
    """
    queryset = Unterbrechungszeiten.objects.all()
    serializer_class = UnterbrechungszeitenSerializer
    permission_classes = [permissions.IsAuthenticated]

class AusbildungsbloeckePfadViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows AusbildungsbloeckePfad to be viewed or edited.
    """
    queryset = AusbildungsbloeckePfad.objects.all()
    serializer_class = AusbildungsbloeckePfadSerializer
    permission_classes = [permissions.IsAuthenticated]

class AusbildungserfordernissePfadViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Ausbildungserfordernisse to be viewed or edited.
    """
    queryset = AusbildungserfordernissePfad.objects.all()
    serializer_class = AusbildungserfordernissePfadSerializer
    permission_classes = [permissions.IsAuthenticated]

class AusbildungsinhaltePfadViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows AusbildungsinhaltePfad to be viewed or edited.
    """
    queryset = AusbildungsinhaltePfad.objects.all()
    serializer_class = AusbildungsinhaltePfadSerializer
    permission_classes = [permissions.IsAuthenticated]

class PlannedAusbildungsstelleByFachgebieteMonthsViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows PlannedAusbildungsstelleByFachgebieteMonths to be viewed or edited.
    """
    queryset = PlannedAusbildungsstelleByFachgebieteMonths.objects.all()
    serializer_class = PlannedAusbildungsstelleByFachgebieteMonthsSerializer
    permission_classes = [permissions.IsAuthenticated]

###################################################
class ParameterViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Parameter to be viewed or edited.
    """
    queryset = Parameter.objects.all()
    serializer_class = ParameterSerializer
    permission_classes = [permissions.IsAuthenticated]
    
class ConsideredAusbildungstypenViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows ConsideredAusbildungstypen to be viewed or edited.
    """
    queryset = ConsideredAusbildungstypen.objects.all()
    serializer_class = ConsideredAusbildungstypenSerializer
    permission_classes = [permissions.IsAuthenticated]
###################################################
class ScheduleViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Schedule to be viewed or edited.
    """
    queryset = Schedule.objects.all()
    serializer_class = ScheduleSerializer
    permission_classes = [permissions.IsAuthenticated]

class ScheduleStatisticsViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows ScheduleStatistics to be viewed or edited.
    """
    queryset = ScheduleStatistics.objects.all()
    serializer_class = ScheduleStatisticsSerializer
    permission_classes = [permissions.IsAuthenticated]
###################################################

class ZuweisungenViewSet(viewsets.ModelViewSet):
    """
       API endpoint that allows Zuweisungen to be viewed or edited.
       """
    queryset = Zuweisungen.objects.all()
    serializer_class = ZuweisungenSerializer
    permission_classes = [permissions.IsAuthenticated]

class DienstpostenZuweisungenViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Dienstpostenzuweisungen to be viewed or edited.
    """
    queryset = DienstpostenZuweisungen.objects.all()
    serializer_class = DienstpostenZuweisungenSerializer
    permission_classes = [permissions.IsAuthenticated]

class AusbildungsstellenZuweisungViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Ausbildungsstellenzuweisungen to be viewed or edited.
    """
    queryset = AusbildungsstellenZuweisungen.objects.all()
    serializer_class = AusbildungsstellenZuweisungSerializer
    permission_classes = [permissions.IsAuthenticated]
