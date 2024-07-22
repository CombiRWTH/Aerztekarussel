from rest_framework import serializers
from .models import *


###################################################
class FachgebieteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Fachgebiete
        fields = '__all__'


class AusbildungsbloeckeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ausbildungsbloecke
        fields = '__all__'


class AusbildungserfordernisseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ausbildungserfordernisse
        fields = '__all__'


class AusbildungserfordernisseExportSerializer(serializers.ModelSerializer):
    minimalNumberOfPicks = serializers.IntegerField(source='min_number_of_picks')
    maximumNumberOfPicks = serializers.IntegerField(source='max_number_of_picks')

    class Meta:
        model = Ausbildungserfordernisse
        fields = ('name', 'duration', 'minimalNumberOfPicks', 'maximumNumberOfPicks')


class AusbildungsinhalteSerializer(serializers.ModelSerializer):
    ausbildungsinhaltetags_set = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    ausbildungsstellenanforderungen_set = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = Ausbildungsinhalte
        fields = '__all__'


class AusbildungsinhalteExportSerializer(serializers.ModelSerializer):
    minDuration = serializers.IntegerField(source='min_duration')
    maxDuration = serializers.IntegerField(source='max_duration')

    class Meta:
        model = Ausbildungsinhalte
        fields = ('name', 'minDuration', 'maxDuration', 'preferred')


class AusbildungsinhalteTagsSerializer(serializers.ModelSerializer):
    class Meta:
        model = AusbildungsinhalteTags
        fields = '__all__'


class AusbildungsinhalteTagsExportSerializer(serializers.ModelSerializer):
    class Meta:
        model = AusbildungsinhalteTags
        fields = 'required_tag'


class AusbildungsStellenAnforderungenSerializer(serializers.ModelSerializer):
    class Meta:
        model = AusbildungsStellenAnforderungen
        fields = '__all__'


class AusbildungsStellenAnforderungenExportSerializer(serializers.ModelSerializer):
    anrechenbareFachgebiete = serializers.IntegerField(source='fachgebiet_id')
    anrechenbareDauerInMonths = serializers.IntegerField(source='anrechendbare_duration_in_month')

    class Meta:
        model = AusbildungsStellenAnforderungen
        fields = ('anrechenbareFachgebiete', 'anrechenbareDauerInMonths')


class OccupationalGroupsSerializer(serializers.ModelSerializer):
    class Meta:
        model = OccupationalGroups
        fields = '__all__'


class Personal(serializers.ModelSerializer):
    class Meta:
        model = Personal
        fields = '__all__'


###################################################

class OrganisationsgruppeSerializer(serializers.ModelSerializer):
    ausbildungsstaette_set = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    dienstposten_set = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = Organisationsgruppe
        fields = '__all__'


class OrganisationsgruppeExportSerializer(serializers.ModelSerializer):
    # django-rest-framework serializer field types: https://www.django-rest-framework.org/api-guide/fields/
    # rename -> source is original name of model field (is_kooperationspartner) -> variable name is the serialized name (isKooperationspartner)
    isKooperationspartner = serializers.BooleanField(source='is_kooperationspartner')

    class Meta:
        model = Organisationsgruppe
        fields = ('id', 'name', 'isKooperationspartner')


class AusbildungsstaetteSerializer(serializers.ModelSerializer):
    ausbildungsstaettentags_set = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    dienstposten_set = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    planbareausbildungsbloecke_set = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = Ausbildungsstaette
        fields = '__all__'


class AusbildungsstaetteExportSerializer(serializers.ModelSerializer):
    organisationsgruppenId = serializers.IntegerField(source='organisationsgruppe_id')

    class Meta:
        model = Ausbildungsstaette
        fields = ('id', 'name', 'organisationsgruppenId')


class AusbildungsstaettenTagsSerializer(serializers.ModelSerializer):
    class Meta:
        model = AusbildungsstaettenTags
        fields = '__all__'


# ausbildungsstaettenId = serializers.IntegerField(source='ausbildungsstaette_id')
class AusbildungsstaettenTagsExportSerializer(serializers.ModelSerializer):
    class Meta:
        model = AusbildungsstaettenTags
        fields = ['tag']


class DienstpostenSerializer(serializers.ModelSerializer):
    occupationalgroupsdienstposten_set = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    associatedausbildungsbloecke_set = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = Dienstposten
        fields = '__all__'


class DienstpostenExportSerializer(serializers.ModelSerializer):
    startDate = serializers.DateField(source='start_date')
    endDate = serializers.DateField(source='end_date')

    class Meta:
        model = Dienstposten
        fields = ('id', 'startDate', 'endDate', 'hours')


class OccupationalGroupsDienstpostenSerializer(serializers.ModelSerializer):
    class Meta:
        model = OccupationalGroupsDienstposten
        fields = '__all__'


class OccupationalGroupsDienstpostenExportSerializer(serializers.ModelSerializer):
    class Meta:
        model = OccupationalGroupsDienstposten
        fields = ['occupational_group_id']


class AssociatedAusbildungsbloeckeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssociatedAusbildungsbloecke
        fields = '__all__'


class AssociatedAusbildungsbloeckeExportSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssociatedAusbildungsbloecke
        fields = ['ausbildungsblock_id']


class PlanbareAusbildungsbloeckeSerializer(serializers.ModelSerializer):
    ausbildungsstelle_set = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    genehmigtefachgebiete_set = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = PlanbareAusbildungsbloecke
        fields = '__all__'


class PlanbareAusbildungsbloeckeExportSerializer(serializers.ModelSerializer):
    startDate = serializers.DateField(source='start_date')
    ausbildungsBlockId = serializers.IntegerField(source='ausbildungsblock_id')

    class Meta:
        model = PlanbareAusbildungsbloecke
        fields = ('startDate', 'ausbildungsBlockId')


class AusbildungsstelleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ausbildungsstelle
        fields = '__all__'


class AusbildungsstelleExportSerializer(serializers.ModelSerializer):
    startDate = serializers.DateField(source='start_date')
    durationInMonths = serializers.IntegerField(source='duration_in_month')

    class Meta:
        model = Ausbildungsstelle
        fields = ('id', 'startDate', 'durationInMonths')


class GenehmigteFachgebieteSerializer(serializers.ModelSerializer):
    class Meta:
        model = GenehmigteFachgebiete
        fields = '__all__'


class GenehmigteFachgebieteExportSerializer(serializers.ModelSerializer):
    fachgebietId = serializers.IntegerField(source='fachgebiet_id')
    durationInMonths = serializers.IntegerField(source='duration_in_month')

    class Meta:
        model = GenehmigteFachgebiete
        fields = ('fachgebietId', 'durationInMonths')


###################################################

###################################################
class PersonenSerializer(serializers.ModelSerializer):
    planungsparameter_set = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    unterbrechungszeiten_set = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    ausbildungspfade_set = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    organisationsgruppenpriorities_set = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    plannedausbildungsstellebyfachgebietemonths_set = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = Personen
        fields = '__all__'


class PersonenExportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Personen
        fields = ('id', 'name')


class PlanungsParameterSerializer(serializers.ModelSerializer):
    allowedorganisationunits_set = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = PlanungsParameter
        fields = '__all__'


class PlanungsParameterExportSerializer(serializers.ModelSerializer):
    occupationalGroupId = serializers.IntegerField(source='occupational_group_id')
    hoursPerWeek = serializers.IntegerField(source='hours_per_week')
    startDate = serializers.DateField(source='start_date')
    endDate = serializers.DateField(source='end_date')
    status = serializers.BooleanField(source='status_active')

    class Meta:
        model = PlanungsParameter
        fields = ('occupationalGroupId', 'hoursPerWeek', 'startDate', 'endDate', 'status')


class AllowedOrganisationUnitsSerializer(serializers.ModelSerializer):
    class Meta:
        model = AllowedOrganisationUnits
        fields = '__all__'


class AllowedOrganisationUnitsExportSerializer(serializers.ModelSerializer):
    class Meta:
        model = AllowedOrganisationUnits
        fields = ['organisationsgruppe_id']


class AusbildungsPfadeSerializer(serializers.ModelSerializer):
    ausbildungsbloeckepfad_set = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = AusbildungsPfade
        fields = '__all__'


class AusbildungsPfadeExportSerializer(serializers.ModelSerializer):
    startDate = serializers.DateField(source='start_date')
    personId = serializers.IntegerField(source='person_id')

    class Meta:
        model = AusbildungsPfade
        fields = ('id', 'startDate', 'personId')


class OrganisationsGruppenPrioritiesSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganisationsGruppenPriorities
        fields = '__all__'


class UnterbrechungszeitenSerializer(serializers.ModelSerializer):
    class Meta:
        model = Unterbrechungszeiten
        fields = '__all__'


class UnterbrechungszeitenExportSerializer(serializers.ModelSerializer):
    startDate = serializers.DateField(source='start_date')
    endDate = serializers.DateField(source='end_date')

    class Meta:
        model = Unterbrechungszeiten
        fields = ('startDate', 'endDate')


class AusbildungsbloeckePfadSerializer(serializers.ModelSerializer):
    ausbildungserfordernissepfad_set = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = AusbildungsbloeckePfad
        fields = '__all__'


class AusbildungsbloeckePfadExportSerializer(serializers.ModelSerializer):
    personalBlockId = serializers.IntegerField(source='personal_block_id')
    ausbildungsBlockId = serializers.IntegerField(source='ausbildungsblock_id')

    class Meta:
        model = AusbildungsbloeckePfad
        fields = ('personalBlockId', 'ausbildungsBlockId')


class AusbildungserfordernissePfadSerializer(serializers.ModelSerializer):
    ausbildungsinhaltepfad_set = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = AusbildungserfordernissePfad
        fields = '__all__'


class AusbildungserfordernissePfadExportSerializer(serializers.ModelSerializer):
    personalErfordernisId = serializers.IntegerField(source='personal_erfordernis_id')
    ausbildungsErfordernisId = serializers.IntegerField(source='ausbildungserfordernis_id')
    monthsCompleted = serializers.IntegerField(source='month_completed')

    class Meta:
        model = AusbildungserfordernissePfad
        fields = ('personalErfordernisId', 'ausbildungsErfordernisId', 'monthsCompleted')


class AusbildungsinhaltePfadSerializer(serializers.ModelSerializer):
    class Meta:
        model = AusbildungsinhaltePfad
        fields = '__all__'


class AusbildungsinhaltePfadExportSerializer(serializers.ModelSerializer):
    personalInhaltId = serializers.IntegerField(source='personal_inhalt_id')
    ausbildungsInhaltId = serializers.IntegerField(source='ausbildungsinhalte_id')
    monthsCompleted = serializers.IntegerField(source='month_completed')

    class Meta:
        model = AusbildungsinhaltePfad
        fields = ('personalInhaltId', 'ausbildungsInhaltId', 'monthsCompleted')


class PlannedAusbildungsstelleByFachgebieteMonthsSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlannedAusbildungsstelleByFachgebieteMonths
        fields = '__all__'


###################################################

###################################################
class ParameterSerializer(serializers.ModelSerializer):
    consideredausbildungstypen_set = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = Parameter
        fields = '__all__'


class ParameterExportSerializer(serializers.ModelSerializer):
    startDate = serializers.DateField(source='start_date')
    endDate = serializers.DateField(source='end_date')
    maxStandstill = serializers.IntegerField(source='max_standstill')
    populationSize = serializers.IntegerField(source='population_size')
    chunkSize = serializers.IntegerField(source='chunk_size')
    fteInHours = serializers.IntegerField(source='fte_in_hours')
    weeklyHoursNeededForAccreditation = serializers.IntegerField(source='weekly_hours_needed_for_accreditation')

    class Meta:
        model = Parameter
        fields = ('startDate', 'endDate', 'maxStandstill', 'populationSize', 'chunkSize', 'fteInHours', 'weeklyHoursNeededForAccreditation')


class ParameterObjectiveWeightsExportSerializer(serializers.ModelSerializer):

    singleMonthAssignments = serializers.IntegerField(source='objectiveweights_single_month_assignments')
    monthsWithoutTraining = serializers.IntegerField(source='objectiveweights_months_without_training')
    consecutiveMonthsWithoutTraining = serializers.IntegerField(source='objectiveweights_consecutive_months_without_training')
    hospitalChanges = serializers.IntegerField(source='objectiveweights_hospital_changes')
    departmentChanges = serializers.IntegerField(source='objectiveweights_department_changes')
    monthsAtCooperationPartner = serializers.IntegerField(source='objectiveweights_months_at_cooperation_partner')
    violatedPreferences = serializers.IntegerField(source='objectiveweights_violated_preferences')
    varMonthsWithoutTraining = serializers.IntegerField(source='objectiveweights_var_months_without_training')
    varWeightedMonthsWithoutTraining = serializers.IntegerField(source='objectiveweights_var_weighted_months_without_training')
    varViolatedPreferences = serializers.IntegerField(source='objectiveweights_var_violated_preferences')
    departmentsWithoutTraining = serializers.IntegerField(source='objectiveweights_departments_without_training')

    class Meta:
        model = Parameter
        fields = ('singleMonthAssignments', 'monthsWithoutTraining', 'consecutiveMonthsWithoutTraining', 'hospitalChanges', 'departmentChanges', 'monthsAtCooperationPartner', 'violatedPreferences', 'varMonthsWithoutTraining', 'varWeightedMonthsWithoutTraining', 'varViolatedPreferences', 'departmentsWithoutTraining')


class ParameterTerminationExportSerializer(serializers.ModelSerializer):
    type = serializers.CharField(source='termination_t_type')
    value = serializers.IntegerField(source='termination_value')

    class Meta:
        model = Parameter
        fields = ('type', 'value')


class ConsideredAusbildungstypenSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConsideredAusbildungstypen
        fields = '__all__'


###################################################
class ScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Schedule
        fields = '__all__'

class ScheduleStatisticsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScheduleStatistics
        fields = '__all__'
###################################################
class ZuweisungenSerializer(serializers.ModelSerializer):
    ausbildungsstellenzuweisung_set = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    dientspostenzuweisungen_set = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = Zuweisungen
        fields = '__all__'


class ZuweisungenExportSerializer(serializers.ModelSerializer):
    personId = serializers.IntegerField(source='person_id')
    organisationsGruppenId = serializers.IntegerField(source='organisationsgruppe_id')
    ausbildungsstaettenId = serializers.IntegerField(source='ausbildungsstaette_id')
    ausbildungsInhaltId = serializers.IntegerField(source='ausbildungsinhalt_id')
    personalInhaltId = serializers.IntegerField(source='personal_inhalt_id')
    startDate = serializers.DateField(source='start_date')
    endDate = serializers.DateField(source='end_date')

    class Meta:
        model = Zuweisungen
        fields = ('personId', 'organisationsGruppenId', 'ausbildungsstaettenId', 'ausbildungsInhaltId', 'personalInhaltId', 'startDate', 'endDate', 'fixiert')


class DienstpostenZuweisungenSerializer(serializers.ModelSerializer):
    class Meta:
        model = DienstpostenZuweisungen
        fields = '__all__'


class DienstpostenZuweisungenExportSerializer(serializers.ModelSerializer):
    dienstpostenId = serializers.IntegerField(source='dienstposten_id')
    hoursPerWeek = serializers.IntegerField(source='hours_per_week')

    class Meta:
        model = DienstpostenZuweisungen
        fields = ('dienstpostenId', 'hoursPerWeek')

class AusbildungsstellenZuweisungSerializer(serializers.ModelSerializer):
    class Meta:
        model = AusbildungsstellenZuweisungen
        fields = '__all__'

class AusbildungsstellenZuweisungExportSerializer(serializers.ModelSerializer):
    ausbildungsstellenId = serializers.IntegerField(source='ausbildungsstelle_id')
    hoursPerWeek = serializers.IntegerField(source='hours_per_week')

    class Meta:
        model = AusbildungsstellenZuweisungen
        fields = ('ausbildungsstellenId', 'hoursPerWeek')
