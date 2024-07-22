from datamodel.models import *
import json


def read_db(printToConsole):
    
    # Organisationsgruppen
    for kh in Organisationsgruppe.objects.all():
        printTestValues(printToConsole, f"Krankenhaus-Id:{kh.id}, Id-Extern:{kh.id_ext}, Name:{kh.name}, Ist-Kooperationsparter:{kh.is_kooperationspartner}")
        
        # Ausbildungsstätte
        for staette in kh.ausbildungsstaette_set.all():
            printTestValues(printToConsole, f"Ausbildungsstätte-Id:{staette.id}, Id-Extern:{staette.id_ext}, Name:{staette.name}, Id-Organsiationsgruppe:{staette.organisationsgruppe_id}")

            # AusbildungsstaettenTags
            for tag in staette.ausbildungsstaettentags_set.all():
                printTestValues(printToConsole, f"AusbildungsstaettenTags-Id:{tag.id}, Id-Extern:{tag.tag}, Id-Ausbildungsstätte:{tag.ausbildungsstaette_id}")

            # Dienstposten
            for dienstposten in staette.dienstposten_set.all():
                printTestValues(printToConsole, f"Dienstposten-Id:{dienstposten.id}, Id-Extern:{dienstposten.id_ext}, Start-Datum:{dienstposten.start_date}, Ende-Datum:{dienstposten.end_date}, Stunden:{dienstposten.hours}, Id-Ausbildungsstätte:{dienstposten.ausbildungsstaette_id}")

                # OccupationalGroup
                for occupationalGroup in dienstposten.occupationalgroupsdienstposten_set.all():
                    printTestValues(printToConsole, f"OccupationalGroup-Id:{occupationalGroup.id}, Gruppe:{occupationalGroup.occupational_group.id_ext}, Id-Dienstposten:{occupationalGroup.dienstposten_id}")
                    
                # AssociatedAusbildungsbloeck
                for associatedAusbildungsbloeck in dienstposten.associatedausbildungsbloecke_set.all():
                    printTestValues(printToConsole, f"AssociatedAusbildungsbloeck-Id:{associatedAusbildungsbloeck.id}, Id-Ausbildungsblock:{associatedAusbildungsbloeck.ausbildungsblock_id}, Id-Dienstposten:{associatedAusbildungsbloeck.dienstposten_id}")
                
            # Planbarer-Ausbildungsblock
            for planbarerAusbildungsblock in staette.planbareausbildungsbloecke_set.all():
                printTestValues(printToConsole, f"Planbarer-Ausbildungsblock-Id:{planbarerAusbildungsblock.id}, Id-Ausbildungsblock:{planbarerAusbildungsblock.ausbildungsblock_id}, Start-Datum:{planbarerAusbildungsblock.start_date}, Id-Ausbildungsstätte:{planbarerAusbildungsblock.ausbildungsstaette_id}")

                # Ausbildungsstelle
                for ausbildungsStelle in planbarerAusbildungsblock.ausbildungsstelle_set.all():
                    printTestValues(printToConsole, f"Ausbildungsstelle-Id:{ausbildungsStelle.id}, Id-Extern:{ausbildungsStelle.id_ext}, Start-Datum:{ausbildungsStelle.start_date}, Dauer:{ausbildungsStelle.duration_in_month}, Id-Planbare-Ausbildungsblöcke:{ausbildungsStelle.planbarer_ausbildungsblock_id}")

                # Genehmigtes Fachgebiet
                for genehmigtesFachgebiet in planbarerAusbildungsblock.genehmigtefachgebiete_set.all():
                    printTestValues(printToConsole, f"GenehmigtesFachgebiet-Id:{genehmigtesFachgebiet.id}, Id-Extern:{genehmigtesFachgebiet.fachgebiet.id_ext}, Dauer:{genehmigtesFachgebiet.duration_in_month}, Id-Planbare-Ausbildungsblöcke:{genehmigtesFachgebiet.planbarer_ausbildungsblock_id}")

        # Dienstposten
        for dienstposten in kh.dienstposten_set.all():
            printTestValues(printToConsole, f"Dienstposten-Id:{dienstposten.id}, Id-Extern:{dienstposten.id_ext}, Start-Datum:{dienstposten.start_date}, Ende-Datum:{dienstposten.end_date}, Stunden:{dienstposten.hours}, Id-Organsiationsgruppe:{dienstposten.organisationsgruppe_id}")

            # OccupationalGroup
            for occupationalGroup in dienstposten.occupationalgroupsdienstposten_set.all():
                printTestValues(printToConsole, f"OccupationalGroup-Id:{occupationalGroup.id}, Gruppe:{occupationalGroup.occupational_group.id_ext}, Id-Dienstposten:{occupationalGroup.dienstposten_id}")
                
            # AssociatedAusbildungsbloeck
            for associatedAusbildungsbloeck in dienstposten.associatedausbildungsbloecke_set.all():
                printTestValues(printToConsole, f"AssociatedAusbildungsbloeck-Id:{associatedAusbildungsbloeck.id}, Id-Ausbildungsblock:{associatedAusbildungsbloeck.ausbildungsblock_id}, Id-Dienstposten:{associatedAusbildungsbloeck.dienstposten_id}")

    # Personen
    for person in Personen.objects.all():
        printTestValues(printToConsole, f"Person-Id:{person.id}, Id-Extern:{person.id_ext}, Name:{person.name}")
        
        # Planungsparameter
        for param in person.planungsparameter_set.all():
            printTestValues(printToConsole, f"Planungsparameter-Id:{param.id}, Id-Person:{param.person_id}, Id-Occupational-Group:{param.occupational_group.id_ext}, Stunden:{param.hours_per_week}, Start-Datum:{param.start_date}, End-Datum:{param.end_date}, Status-Aktiv:{param.status_active}")
            
            # Allowed-Org-Unit
            for unit in param.allowedorganisationunits_set.all():
                printTestValues(printToConsole, f"Allowed-Org-Unit-Id:{unit.id}, Id-Organisationsgruppe:{unit.organisationsgruppe_id}, Id-Planungsparameter:{unit.planungs_parameter_id}")

        # Unterbrechungszeiten
        for pause in person.unterbrechungszeiten_set.all():
            printTestValues(printToConsole, f"Unterbrechungszeiten-Id:{pause.id}, Id-Person:{pause.person_id}, Start-Datum:{pause.start_date}, End-Datum:{pause.end_date}")
            
        # Ausbildungspfad
        for pfad in person.ausbildungspfade_set.all():
            printTestValues(printToConsole, f"Ausbildungspfad-Id:{pfad.id}, Id-Extern:{pfad.id_ext}, Id-Person:{pfad.person_id}, Start-Datum:{pfad.start_date}")

            # Ausbildungsbloecke
            for block in pfad.ausbildungsbloeckepfad_set.all():
                printTestValues(printToConsole, f"Ausbildungsblock-Id:{block.id}, Id-Extern:{block.ausbildungsblock.id_ext}, Name:{block.ausbildungsblock.name}, Ausbildungstyp:{block.ausbildungsblock.ausbildungstyp}, Personal-Block-Id:{block.personal_block.id_ext}, Id-Ausbildungspfad:{block.ausbildungspfad_id}")

                # Ausbildungserfordernisse
                for erfordernisse in block.ausbildungserfordernissepfad_set.all():
                    printTestValues(printToConsole, f"Ausbildungserfordernis-Id:{erfordernisse.id}, Id-Extern:{erfordernisse.ausbildungserfordernis.id_ext}, Id-Ausbildungsblock:{erfordernisse.ausbildungsblock_pfad_id}, Personal-Erfordernis-Id:{erfordernisse.personal_erfordernis.id_ext}, Name:{erfordernisse.ausbildungserfordernis.name}, Dauer:{erfordernisse.ausbildungserfordernis.duration}, Monate-absolviert:{erfordernisse.month_completed}, Minimale-Anzahl-Wahl:{erfordernisse.ausbildungserfordernis.min_number_of_picks}, Maximale-Anzahl-Wahl:{erfordernisse.ausbildungserfordernis.max_number_of_picks}")

                    # Ausbildungsinhalte
                    for inhalt in erfordernisse.ausbildungsinhaltepfad_set.all():
                        printTestValues(printToConsole, f"Ausbildungsinhalt-Id:{inhalt.id}, Id-Extern:{inhalt.ausbildungsinhalte.id_ext}, Id-Ausbildungserfordernis:{inhalt.ausbildungserfordernis_pfad_id}, Personal-Inhalt-Id:{inhalt.personal_inhalt.id_ext}, Name:{inhalt.ausbildungsinhalte.name}, Minimale-Dauer:{inhalt.ausbildungsinhalte.min_duration}, Maximale-Dauer:{inhalt.ausbildungsinhalte.max_duration}, Monate-absolviert:{inhalt.month_completed}, bevorzugt:{inhalt.ausbildungsinhalte.preferred}")

                        # AusbildungsinhalteTags
                        for tag in inhalt.ausbildungsinhalte.ausbildungsinhaltetags_set.all():
                            printTestValues(printToConsole, f"AusbildungsinhalteTags-Id:{tag.id}, Required-Tag:{tag.required_tag}, Id-Ausbildungsinhalte:{tag.ausbildungsinhalt_id}")
                        
                        # AusbildungsStellenAnforderungen
                        for ausbildungsStellenAnforderung in inhalt.ausbildungsinhalte.ausbildungsstellenanforderungen_set.all():
                            printTestValues(printToConsole, f"AusbildungsStellenAnforderung-Id:{ausbildungsStellenAnforderung.id}, Id-Ausbildungsinhalt:{ausbildungsStellenAnforderung.ausbildungsinhalt_id}, Id-Fachgebiet:{ausbildungsStellenAnforderung.fachgebiet_id} Anrechenbare-Dauer-in-Monaten:{ausbildungsStellenAnforderung.anrechendbare_duration_in_month}")

        # OrganisationsGruppenPriorities
        for prio in person.organisationsgruppenpriorities_set.all():
            printTestValues(printToConsole, f"OrganisationsGruppenPriorities-Id:{prio.id}, Id-Person:{prio.person_id}, Id-Organisationsgruppe:{prio.organisationsgruppe_id}, Priority:{prio.priority}")

        # PlannedAusbildungsstelleByFachgebieteMonths
        for plan in person.plannedausbildungsstellebyfachgebietemonths_set.all():
            printTestValues(printToConsole, f"PlannedAusbildungsstelleByFachgebieteMonths-Id:{plan.id}, Id-Person:{plan.person_id}, Id-Fachgebiet:{plan.fachgebiet_id}, Monate:{plan.month}")

    # Zuweisungen
    for zuwei in Zuweisungen.objects.all():
        printTestValues(printToConsole, f"Zuweisung-Id:{zuwei.id}, Person-Id:{zuwei.person_id}, Organisationsgruppe-Id:{zuwei.organisationsgruppe_id}, Ausbildungsstaette-Id:{zuwei.ausbildungsstaette_id}, Ausbildungsinhalt-Id:{zuwei.ausbildungsinhalt_id}, Personal-Inhalt-Id:{zuwei.personal_inhalt_id}, Start-Datum:{zuwei.start_date}, End-Datum:{zuwei.end_date}, fixiert:{zuwei.fixiert}")

        for dienstpostenZuweisung in zuwei.dienstpostenzuweisungen_set.all():
            printTestValues(printToConsole, f"Dienstposten-Zuweisung-Id:{dienstpostenZuweisung.id}, Id-Zuweisung:{dienstpostenZuweisung.zuweisung_id}, Id-Dienstposten:{dienstpostenZuweisung.dienstposten_id}, Stunden-pro-Woche:{dienstpostenZuweisung.hours_per_week}")

        for ausbildungsstellenZuweisung in zuwei.ausbildungsstellenzuweisungen_set.all():
            printTestValues(printToConsole, f"Ausbildungsstellen-Zuweisung-Id:{ausbildungsstellenZuweisung.id}, Id-Zuweisung:{ausbildungsstellenZuweisung.zuweisung_id}, Id-Ausbildungsstelle:{ausbildungsstellenZuweisung.ausbildungsstelle_id}, Stunden-pro-Woche:{ausbildungsstellenZuweisung.hours_per_week}")

    # Parameter
    for param in Parameter.objects.all():
        printTestValues(printToConsole, f"Parameter-Id:{param.id}, Start-Datum:{param.start_date}, End-Datum:{param.end_date}, Max-Standstill:{param.max_standstill}," +
                                        f"Population-Size:{param.population_size}, Chunk-Size:{param.chunk_size}, Fte-in-Hours:{param.fte_in_hours}," +
                                        f"Weekly-Hours-needed-for-Accreditation:{param.weekly_hours_needed_for_accreditation}, single_month_assignments:{param.objectiveweights_single_month_assignments}," +
                                        f"months_without_training:{param.objectiveweights_months_without_training}, consecutive_months_without_training:{param.objectiveweights_consecutive_months_without_training}," +
                                        f"hospital_changes:{param.objectiveweights_hospital_changes}, department_changes:{param.objectiveweights_department_changes}, months_at_cooperation_partner:{param.objectiveweights_months_at_cooperation_partner}," +
                                        f"violated_preferences:{param.objectiveweights_violated_preferences}, var_months_without_training:{param.objectiveweights_var_months_without_training}," +
                                        f"var_violated_preferences:{param.objectiveweights_var_violated_preferences}, departments_without_training:{param.objectiveweights_departments_without_training}," +
                                        f"type:{param.termination_t_type}, value:{param.termination_value}")

        for consideredausbildungstyp in param.consideredausbildungstypen_set.all():
            printTestValues(printToConsole, f"ausbildungstyp:{consideredausbildungstyp.ausbildungstyp}")

def printTestValues(printToConsole, value):
    if printToConsole:
        print(value)