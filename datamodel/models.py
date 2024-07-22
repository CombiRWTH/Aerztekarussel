from django.db import models
from colorfield.fields import ColorField

###################################################
class DatamodelStatus(models.Model):
    id = models.IntegerField(primary_key=True)
    is_admin_primary = models.BooleanField()
    is_user_primary = models.BooleanField()
    import_date = models.DateField(null=True)
    import_file_name = models.TextField(null=True)
    import_row_count = models.IntegerField(null=True)
    import_file = models.FileField(null=True, upload_to="json_files/")

    def __str__(self):
        return str(self.id)

###################################################
# Baseclasses
class Fachgebiete(models.Model):
    id = models.AutoField(primary_key=True)
    id_ext = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return str(self.id)

class Ausbildungsbloecke(models.Model):
    id = models.AutoField(primary_key=True)
    id_ext = models.IntegerField(null=True, blank=True)
    name = models.TextField()
    ausbildungstyp = models.TextField()

    def __str__(self):
        if self.name == None:
            return str(self.id)
        return self.name

class Ausbildungserfordernisse(models.Model):
    id = models.AutoField(primary_key=True)
    id_ext = models.IntegerField(null=True, blank=True)
    ausbildungsblock = models.ForeignKey(Ausbildungsbloecke, on_delete=models.CASCADE)
    name = models.TextField(null=True)
    duration = models.IntegerField()
    min_number_of_picks = models.IntegerField()
    max_number_of_picks = models.IntegerField()

    def __str__(self):
        if self.name == None:
            return str(self.id)
        return self.name

class Ausbildungsinhalte(models.Model):
    id = models.AutoField(primary_key=True)
    id_ext = models.IntegerField(null=True, blank=True)
    ausbildungserfordernis = models.ForeignKey(Ausbildungserfordernisse, on_delete=models.CASCADE)
    name = models.TextField()
    min_duration = models.IntegerField()
    max_duration = models.IntegerField()
    preferred = models.BooleanField()

    def __str__(self):
        if self.name == None:
            return str(self.id)
        return self.name

class AusbildungsinhalteTags(models.Model):
    id = models.AutoField(primary_key=True)
    ausbildungsinhalt = models.ForeignKey(Ausbildungsinhalte, on_delete=models.CASCADE)
    required_tag = models.IntegerField()

    def __str__(self):
        return str(self.required_tag)

class AusbildungsStellenAnforderungen(models.Model):
    id = models.AutoField(primary_key=True)
    ausbildungsinhalt = models.ForeignKey(Ausbildungsinhalte, on_delete=models.CASCADE)
    fachgebiet = models.ForeignKey(Fachgebiete, on_delete=models.CASCADE)
    anrechendbare_duration_in_month = models.IntegerField()

    def __str__(self):
        return str(self.id)

class OccupationalGroups(models.Model):
    id = models.AutoField(primary_key=True)
    id_ext = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return str(self.id)

class Personal(models.Model):
    id = models.AutoField(primary_key=True)
    id_ext = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return str(self.id)
###################################################

###################################################
# Organisatiosgruppen
class Organisationsgruppe(models.Model):
    COLOR_PALETTE = [
        ("#000000", "Black", ),
        ("#FF0000", "Red", ),
        ("#00FF00", "Lime", ),
        ("#0000FF", "Blue", ),
        ("#FFFF00", "Yellow", ),
        ("#FF00FF", "Magenta", ),
        ("#00FFFF", "Cyan", ),
        ("#800000", "Maroon", ),
        ("#808000", "Olive", ),
        ("#008000", "Green", ),
        ("#800080", "Purple", ),
        ("#008080", "Teal", ),
        ("#000080", "Navy", ),
        ("#FFA500", "Orange", ),
        ("#A52A2A", "Brown", ),
        ("#8A2BE2", "BlueViolet", ),
        ("#5F9EA0", "CadetBlue", ),
        ("#D2691E", "Chocolate", ),
        ("#FF4500", "OrangeRed", ),
        ("#2E8B57", "SeaGreen", ),
        ("#DA70D6", "Orchid", ),
        ("#B22222", "FireBrick", ),
        ("#FF1493", "DeepPink", ),
        ("#7FFF00", "Chartreuse", ),
    ]

    id = models.AutoField(primary_key=True)
    id_ext = models.IntegerField(null=True, blank=True)
    is_kooperationspartner = models.BooleanField()
    name = models.TextField()
    color = ColorField(samples=COLOR_PALETTE, default='#FF0000')

    def __str__(self):
        if self.name == None:
            return str(self.id)
        return self.name

class Ausbildungsstaette(models.Model):
    id = models.AutoField(primary_key=True)
    id_ext = models.IntegerField(null=True, blank=True)
    organisationsgruppe = models.ForeignKey(Organisationsgruppe, on_delete=models.CASCADE)
    name = models.TextField()

    def __str__(self):
        if self.name == None:
            return str(self.id)
        return self.name

class AusbildungsstaettenTags(models.Model):
    id = models.AutoField(primary_key=True)
    ausbildungsstaette = models.ForeignKey(Ausbildungsstaette, on_delete=models.CASCADE)
    tag = models.IntegerField(blank=True)

    def __str__(self):
        return str(self.tag)

class Dienstposten(models.Model):
    id = models.AutoField(primary_key=True)
    id_ext = models.IntegerField(null=True, blank=True)
    organisationsgruppe = models.ForeignKey(Organisationsgruppe, on_delete=models.CASCADE, null=True)
    ausbildungsstaette = models.ForeignKey(Ausbildungsstaette, on_delete=models.CASCADE, null=True)
    start_date = models.DateField(null=True)
    end_date = models.DateField(null=True)
    hours = models.IntegerField()

    def __str__(self):
        return str(self.id)

class OccupationalGroupsDienstposten(models.Model):
    id = models.AutoField(primary_key=True)
    dienstposten = models.ForeignKey(Dienstposten, on_delete=models.CASCADE)
    occupational_group = models.ForeignKey(OccupationalGroups, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.occupational_group)

class AssociatedAusbildungsbloecke(models.Model):
    id = models.AutoField(primary_key=True)
    ausbildungsblock = models.ForeignKey(Ausbildungsbloecke, on_delete=models.CASCADE)
    dienstposten = models.ForeignKey(Dienstposten, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.id)

class PlanbareAusbildungsbloecke(models.Model):
    id = models.AutoField(primary_key=True)
    ausbildungsblock = models.ForeignKey(Ausbildungsbloecke, on_delete=models.CASCADE)
    ausbildungsstaette = models.ForeignKey(Ausbildungsstaette, on_delete=models.CASCADE)
    start_date = models.DateField()

    def __str__(self):
        return str(self.id)

class Ausbildungsstelle(models.Model):
    id = models.AutoField(primary_key=True)
    id_ext = models.IntegerField(null=True, blank=True)
    planbarer_ausbildungsblock = models.ForeignKey(PlanbareAusbildungsbloecke, on_delete=models.CASCADE)
    start_date = models.DateField()
    duration_in_month = models.IntegerField(null=True)

    def __str__(self):
        return str(self.id)

class GenehmigteFachgebiete(models.Model):
    id = models.AutoField(primary_key=True)
    planbarer_ausbildungsblock = models.ForeignKey(PlanbareAusbildungsbloecke, on_delete=models.CASCADE)
    fachgebiet = models.ForeignKey(Fachgebiete, on_delete=models.CASCADE)
    duration_in_month = models.IntegerField()

    def __str__(self):
        return str(self.id)
###################################################

###################################################
# Personen
class Personen(models.Model):
    id = models.AutoField(primary_key=True)
    id_ext = models.IntegerField(null=True, blank=True)
    name = models.TextField(null=True)

    def __str__(self):
        if self.name == None:
            return str(self.id)
        return self.name

class PlanungsParameter(models.Model):
    id = models.AutoField(primary_key=True)
    person = models.ForeignKey(Personen, on_delete=models.CASCADE)
    occupational_group = models.ForeignKey(OccupationalGroups, on_delete=models.CASCADE)
    hours_per_week = models.IntegerField()
    start_date = models.DateField()
    end_date = models.DateField(null=True)
    status_active = models.BooleanField()

    def __str__(self):
        return str(self.id)

class AllowedOrganisationUnits(models.Model):
    id = models.AutoField(primary_key=True)
    organisationsgruppe = models.ForeignKey(Organisationsgruppe, on_delete=models.CASCADE)
    planungs_parameter = models.ForeignKey(PlanungsParameter, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.id)

class AusbildungsPfade(models.Model):
    id = models.AutoField(primary_key=True)
    id_ext = models.IntegerField(null=True, blank=True)
    person = models.ForeignKey(Personen, on_delete=models.CASCADE)
    start_date = models.DateField()

    def __str__(self):
        return str(self.id)

class OrganisationsGruppenPriorities(models.Model):
    id = models.AutoField(primary_key=True)
    person = models.ForeignKey(Personen, on_delete=models.CASCADE)
    organisationsgruppe = models.ForeignKey(Organisationsgruppe, on_delete=models.CASCADE)
    priority = models.IntegerField()

    def __str__(self):
        return str(self.priority)

class Unterbrechungszeiten(models.Model):
    id = models.AutoField(primary_key=True)
    person = models.ForeignKey(Personen, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()

    def __str__(self):
        return str(self.id)

class AusbildungsbloeckePfad(models.Model):
    id = models.AutoField(primary_key=True)
    ausbildungspfad = models.ForeignKey(AusbildungsPfade, on_delete=models.CASCADE)
    ausbildungsblock = models.ForeignKey(Ausbildungsbloecke, on_delete=models.CASCADE)
    personal_block = models.ForeignKey(Personal, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.id)

class AusbildungserfordernissePfad(models.Model):
    id = models.AutoField(primary_key=True)
    ausbildungsblock_pfad = models.ForeignKey(AusbildungsbloeckePfad, on_delete=models.CASCADE)
    ausbildungserfordernis = models.ForeignKey(Ausbildungserfordernisse, on_delete=models.CASCADE)
    personal_erfordernis = models.ForeignKey(Personal, on_delete=models.CASCADE)
    month_completed = models.IntegerField()

    def __str__(self):
        return str(self.id)
        
class AusbildungsinhaltePfad(models.Model):
    id = models.AutoField(primary_key=True)
    ausbildungserfordernis_pfad = models.ForeignKey(AusbildungserfordernissePfad, on_delete=models.CASCADE)
    ausbildungsinhalte = models.ForeignKey(Ausbildungsinhalte, on_delete=models.CASCADE)
    personal_inhalt = models.ForeignKey(Personal, on_delete=models.CASCADE)
    month_completed = models.IntegerField()

    def __str__(self):
        return str(self.id)
        
class PlannedAusbildungsstelleByFachgebieteMonths(models.Model):
    id = models.AutoField(primary_key=True)
    ausbildungsstelle = models.ForeignKey(Ausbildungsstelle, on_delete=models.CASCADE)
    person = models.ForeignKey(Personen, on_delete=models.CASCADE)
    fachgebiet = models.ForeignKey(Fachgebiete, on_delete=models.CASCADE)
    month = models.IntegerField()

    def __str__(self):
        return str(self.id)
###################################################

##########################################
# Zuweisungen
class Zuweisungen(models.Model):
    id = models.AutoField(primary_key=True)
    person = models.ForeignKey(Personen, on_delete=models.CASCADE)
    organisationsgruppe = models.ForeignKey(Organisationsgruppe, on_delete=models.CASCADE)
    ausbildungsstaette = models.ForeignKey(Ausbildungsstaette, on_delete=models.CASCADE)
    ausbildungsinhalt = models.ForeignKey(Ausbildungsinhalte, on_delete=models.CASCADE, null=True)
    personal_inhalt = models.ForeignKey(Personal, on_delete=models.CASCADE, null=True)
    start_date = models.DateField()
    end_date = models.DateField()
    fixiert = models.BooleanField()

    def __str__(self):
        return str(self.id)

class DienstpostenZuweisungen(models.Model):
    id = models.AutoField(primary_key=True)
    zuweisung = models.ForeignKey(Zuweisungen, on_delete=models.CASCADE)
    dienstposten = models.ForeignKey(Dienstposten, on_delete=models.CASCADE)
    hours_per_week = models.IntegerField()

    def __str__(self):
        return str(self.id)

class AusbildungsstellenZuweisungen(models.Model):
    id = models.AutoField(primary_key=True)
    zuweisung = models.ForeignKey(Zuweisungen, on_delete=models.CASCADE)
    ausbildungsstelle = models.ForeignKey(Ausbildungsstelle, on_delete=models.CASCADE)
    hours_per_week = models.IntegerField()

    def __str__(self):
        return str(self.id)
###################################################

###################################################
# Parameter
class Parameter(models.Model):
    id = models.AutoField(primary_key=True)
    start_date = models.DateField()
    end_date = models.DateField()
    max_standstill = models.IntegerField(null=True)
    population_size = models.IntegerField(null=True)
    chunk_size = models.IntegerField(null=True)
    fte_in_hours = models.IntegerField(null=True)
    weekly_hours_needed_for_accreditation = models.IntegerField()
    objectiveweights_single_month_assignments = models.IntegerField()
    objectiveweights_months_without_training = models.IntegerField()
    objectiveweights_consecutive_months_without_training = models.IntegerField()
    objectiveweights_hospital_changes = models.IntegerField()
    objectiveweights_department_changes = models.IntegerField()
    objectiveweights_months_at_cooperation_partner = models.IntegerField()
    objectiveweights_violated_preferences = models.IntegerField()
    objectiveweights_var_months_without_training = models.IntegerField()
    objectiveweights_var_violated_preferences = models.IntegerField()
    objectiveweights_departments_without_training = models.IntegerField()
    objectiveweights_var_weighted_months_without_training = models.IntegerField(null=True, default=0)
    termination_t_type = models.TextField(null=True)
    termination_value = models.IntegerField(null=True)
    algorithm_strict_var = models.BooleanField(null=True, default=True)
    algorithm_penalization_value = models.IntegerField(null=True, default=100)
    algorithm_max_seconds_runtime = models.IntegerField(null=True, default=300)
    algorithm_sufficient_quality = models.FloatField(null=True, default=0.1)
    
    def __str__(self):
        return str(self.id)

class ConsideredAusbildungstypen(models.Model):
    id = models.AutoField(primary_key=True)
    organisationsgruppe = models.ForeignKey(Organisationsgruppe, on_delete=models.CASCADE, null=True)
    parameter = models.ForeignKey(Parameter, on_delete=models.CASCADE, null=True)
    ausbildungstyp = models.TextField(null=True)

    def __str__(self):
        return str(self.parameter)
###################################################

###################################################
# Schedule
class Schedule(models.Model):
    id = models.AutoField(primary_key=True)
    month = models.IntegerField()
    start_date = models.DateField()
    end_date = models.DateField()
    person = models.ForeignKey(Personen, on_delete=models.CASCADE, null=True)
    organisationsgruppe = models.ForeignKey(Organisationsgruppe, on_delete=models.CASCADE, null=True)
    ausbildungsstaette = models.ForeignKey(Ausbildungsstaette, on_delete=models.CASCADE, null=True)
    dienstposten = models.ForeignKey(Dienstposten, on_delete=models.CASCADE, null=True)
    ausbildungsblock = models.ForeignKey(Ausbildungsbloecke, on_delete=models.CASCADE, null=True)
    ausbildungsstelle = models.ForeignKey(Ausbildungsstelle, on_delete=models.CASCADE, null=True)
    ausbildungspfad = models.ForeignKey(AusbildungsPfade, on_delete=models.CASCADE, null=True)
    ausbildungserfordernis = models.ForeignKey(Ausbildungserfordernisse, on_delete=models.CASCADE, null=True)
    ausbildungsinhalt = models.ForeignKey(Ausbildungsinhalte, on_delete=models.CASCADE, null=True)

    def __str__(self):
        return str(self.id)

# Schedule statistics
class ScheduleStatistics(models.Model):
    id = models.AutoField(primary_key=True)
    date = models.DateTimeField()
    
    variance_violated_preferences = models.FloatField(null=True)
    variance_months_without_training = models.FloatField(null=True)
    variance_weighted_months_without_training = models.FloatField(null=True)
    
    consecutive_months_without_training = models.IntegerField(null=True)
    consecutive_months_without_training_median = models.IntegerField(null=True)
    consecutive_months_without_training_mean  = models.FloatField(null=True)
    consecutive_months_without_training_max = models.IntegerField(null=True)

    departments_without_training = models.IntegerField(null=True)
    departments_without_training_median = models.IntegerField(null=True)
    departments_without_training_mean = models.FloatField(null=True)
    departments_without_training_max = models.IntegerField(null=True)
    
    hospital_changes = models.IntegerField(null=True)
    hospital_changes_median = models.IntegerField(null=True)
    hospital_changes_mean = models.FloatField(null=True)
    hospital_changes_max = models.IntegerField(null=True)
    
    department_changes = models.IntegerField(null=True)
    department_changes_median = models.IntegerField(null=True)
    department_changes_mean = models.FloatField(null=True)
    department_changes_max = models.IntegerField(null=True)
    
    single_month_assignments = models.IntegerField(null=True)
    single_month_assignments_median = models.IntegerField(null=True)
    single_month_assignments_mean = models.FloatField(null=True)
    single_month_assignments_max = models.IntegerField(null=True)
    
    months_without_training = models.IntegerField(null=True)
    months_without_training_median = models.IntegerField(null=True)
    months_without_training_mean = models.FloatField(null=True)
    months_without_training_max = models.IntegerField(null=True)
    
    months_at_cooperation_partner = models.IntegerField(null=True)
    months_at_cooperation_partner_median = models.IntegerField(null=True)
    months_at_cooperation_partner_mean = models.FloatField(null=True)
    months_at_cooperation_partner_max = models.IntegerField(null=True)

    violated_preferences_occurrences = models.IntegerField(null=True)
    violated_preferences_occurrences_median = models.IntegerField(null=True)
    violated_preferences_occurrences_mean = models.FloatField(null=True)
    violated_preferences_occurrences_max = models.IntegerField(null=True)

    violated_preferences_weight = models.IntegerField(null=True)
    violated_preferences_weight_median = models.IntegerField(null=True)
    violated_preferences_weight_mean = models.FloatField(null=True)
    violated_preferences_weight_max = models.IntegerField(null=True)

    months_without_work = models.IntegerField(null=True)
    months_without_work_median = models.IntegerField(null=True)
    months_without_work_mean = models.FloatField(null=True)
    months_without_work_max = models.IntegerField(null=True)

    missing_progress_in_subject_occurrences = models.IntegerField(null=True)
    missing_progress_in_subject_occurrences_median = models.IntegerField(null=True)
    missing_progress_in_subject_occurrences_mean = models.FloatField(null=True)
    missing_progress_in_subject_occurrences_max = models.IntegerField(null=True)

    missing_progress_in_subject_amount = models.IntegerField(null=True)
    missing_progress_in_subject_amount_median = models.IntegerField(null=True)
    missing_progress_in_subject_amount_mean = models.FloatField(null=True)
    missing_progress_in_subject_amount_max = models.IntegerField(null=True)
    
    missing_progress_in_content_occurrences = models.IntegerField(null=True)
    missing_progress_in_content_occurrences_median = models.IntegerField(null=True)
    missing_progress_in_content_occurrences_mean = models.FloatField(null=True)
    missing_progress_in_content_occurrences_max = models.IntegerField(null=True)

    missing_progress_in_content_amount = models.IntegerField(null=True)
    missing_progress_in_content_amount_median = models.IntegerField(null=True)
    missing_progress_in_content_amount_mean = models.FloatField(null=True)
    missing_progress_in_content_amount_max = models.IntegerField(null=True)

    excess_progress_in_content_occurrences = models.IntegerField(null=True)
    excess_progress_in_content_occurrences_median = models.IntegerField(null=True)
    excess_progress_in_content_occurrences_mean = models.FloatField(null=True)
    excess_progress_in_content_occurrences_max = models.IntegerField(null=True)

    excess_progress_in_content_amount = models.IntegerField(null=True)
    excess_progress_in_content_amount_median = models.IntegerField(null=True)
    excess_progress_in_content_amount_mean = models.FloatField(null=True)
    excess_progress_in_content_amount_max = models.IntegerField(null=True)

    def __str__(self):
        return str(self.id)
###################################################