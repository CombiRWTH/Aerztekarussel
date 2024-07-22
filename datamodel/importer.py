from datamodel.models import *
from datetime import datetime
import json
import os


def load_file(datamodelstatus, db):
    path = datamodelstatus.import_file.path

    # deleting all previous data
    Fachgebiete.objects.using(db).all().delete()
    Ausbildungsbloecke.objects.using(db).all().delete()
    Ausbildungserfordernisse.objects.using(db).all().delete()
    Ausbildungsinhalte.objects.using(db).all().delete()
    AusbildungsinhalteTags.objects.using(db).all().delete()
    AusbildungsStellenAnforderungen.objects.using(db).all().delete()
    OccupationalGroups.objects.using(db).all().delete()
    Personal.objects.using(db).all().delete()

    Organisationsgruppe.objects.using(db).all().delete()
    Ausbildungsstaette.objects.using(db).all().delete()
    AusbildungsstaettenTags.objects.using(db).all().delete()
    Dienstposten.objects.using(db).all().delete()
    OccupationalGroupsDienstposten.objects.using(db).all().delete()
    AssociatedAusbildungsbloecke.objects.using(db).all().delete()
    PlanbareAusbildungsbloecke.objects.using(db).all().delete()
    Ausbildungsstelle.objects.using(db).all().delete()
    GenehmigteFachgebiete.objects.using(db).all().delete()

    Personen.objects.using(db).all().delete()
    PlanungsParameter.objects.using(db).all().delete()
    AllowedOrganisationUnits.objects.using(db).all().delete()
    AusbildungsPfade.objects.using(db).all().delete()
    OrganisationsGruppenPriorities.objects.using(db).all().delete()
    Unterbrechungszeiten.objects.using(db).all().delete()
    AusbildungsbloeckePfad.objects.using(db).all().delete()
    AusbildungserfordernissePfad.objects.using(db).all().delete()
    AusbildungsinhaltePfad.objects.using(db).all().delete()
    PlannedAusbildungsstelleByFachgebieteMonths.objects.using(db).all().delete()

    Zuweisungen.objects.using(db).all().delete()
    DienstpostenZuweisungen.objects.using(db).all().delete()
    AusbildungsstellenZuweisungen.objects.using(db).all().delete()

    Parameter.objects.using(db).all().delete()
    ConsideredAusbildungstypen.objects.using(db).all().delete()

    # Opening JSON file
    f = open(path, encoding='utf-8')
    data = json.load(f)

    # First Save all Relations that are used as Foreign-Keys

    # Fachgebiete and OccupationalGroups
    for kh in data['algorithmData']['organisationsGruppen']:
        import_occupational_groups(kh, db)

        for staette in kh['ausbildungsstaetten']:

            import_occupational_groups(staette, db)

            for block in staette['planbareAusbildungsbloecke']:
                for gebiet in block['genehmigteFachgebiete']:
                    if Fachgebiete.objects.using(db).filter(id_ext=gebiet['fachgebietId']).count() == 0:
                        fg = Fachgebiete(id_ext=gebiet['fachgebietId'])
                        fg.save(using=db)

    ausbildungstypen_allowed_organisationgruppe = {'BASISAUSBILDUNG': [], 'SPITALSTURNUS': []}
    current_org_units = []

    # Ausbildungsblock, Ausbildungserfordernisse, Ausbildungsinahlte including Tags and Anforderungen
    for person in data['algorithmData']['persons']:

        current_org_units.clear()
        for param in person['planungsParameter']:
            current_sub_org_units = []
            for unit in param['allowedOrgUnits']:
                current_sub_org_units.append(unit)

            current_org_units.append(current_sub_org_units)

        for pfad in person['ausbildungsPfade']:
            for block in pfad['ausbildungsBloecke']:
                if Ausbildungsbloecke.objects.using(db).filter(id_ext=block['ausbildungsBlockId']).count() == 0:
                    aBlock = Ausbildungsbloecke(id_ext=block['ausbildungsBlockId'], name=block['name'],
                                                ausbildungstyp=block['ausbildungsTyp'])
                    aBlock.save(using=db)

                    if block['ausbildungsTyp'] in ['BASISAUSBILDUNG', 'SPITALSTURNUS']:
                        ausbildungstypen_allowed_organisationgruppe[block['ausbildungsTyp']].extend(
                            current_org_units[0])
                    if len(current_org_units) > 0:
                        del current_org_units[0]

                import_personal(block, 'personalBlockId', db)

                for req in block['erfordernisse']:
                    if Ausbildungserfordernisse.objects.using(db).filter(
                            id_ext=req['ausbildungsErfordernisId']).count() == 0:
                        areq = Ausbildungserfordernisse(id_ext=req['ausbildungsErfordernisId'], ausbildungsblock=aBlock,
                                                        name=req['name'], duration=req['duration'],
                                                        min_number_of_picks=req['minimalNumberOfPicks'],
                                                        max_number_of_picks=req['maximumNumberOfPicks'])
                        areq.save(using=db)

                    import_personal(req, 'personalErfordernisId', db)

                    for inhalt in req['inhalte']:
                        if Ausbildungsinhalte.objects.using(db).filter(
                                id_ext=inhalt['ausbildungsInhaltId']).count() == 0:
                            inh = Ausbildungsinhalte(id_ext=inhalt['ausbildungsInhaltId'], ausbildungserfordernis=areq,
                                                     name=inhalt['name'], min_duration=inhalt['minDuration'],
                                                     max_duration=inhalt['maxDuration'],
                                                     preferred=inhalt['preferred'] == "true")
                            inh.save(using=db)

                            for tag in inhalt['requiredTags']:
                                sTag = AusbildungsinhalteTags(required_tag=tag, ausbildungsinhalt=inh)
                                sTag.save(using=db)

                            for anf in inhalt['ausbildungsStellenAnforderungen']:
                                for anrechenbaresFachgebiet in anf['anrechenbareFachgebiete']:
                                    fachgebiet = Fachgebiete.objects.using(db).get(id_ext=anrechenbaresFachgebiet)
                                    an = AusbildungsStellenAnforderungen(ausbildungsinhalt=inh, fachgebiet=fachgebiet,
                                                                         anrechendbare_duration_in_month=anf[
                                                                             'anrechenbareDauerInMonths'])
                                    an.save(using=db)

                        import_personal(inhalt, 'personalInhaltId', db)

    # now continue importing the rest in tree style fashion of json file

    # Organisations Gruppen
    for kh in data['algorithmData']['organisationsGruppen']:
        og = Organisationsgruppe(id_ext=kh['id'], is_kooperationspartner=kh['isKooperationspartner'], name=kh['name'])
        og.save(using=db)

        # save considered ausbildungstypen to organisationsgruppe
        if kh['id'] in ausbildungstypen_allowed_organisationgruppe['BASISAUSBILDUNG']:
            consideredAusbildungstyp = ConsideredAusbildungstypen(organisationsgruppe=og,
                                                                  ausbildungstyp='BASISAUSBILDUNG')
            consideredAusbildungstyp.save(using=db)

        if kh['id'] in ausbildungstypen_allowed_organisationgruppe['SPITALSTURNUS']:
            consideredAusbildungstyp = ConsideredAusbildungstypen(organisationsgruppe=og,
                                                                  ausbildungstyp='SPITALSTURNUS')
            consideredAusbildungstyp.save(using=db)
            # Ausbildungsstaetten
        for staette in kh['ausbildungsstaetten']:
            ausbSt = Ausbildungsstaette(id_ext=staette['id'], name=staette['name'], organisationsgruppe=og)
            ausbSt.save(using=db)

            import_dienstposten(staette, ausbSt, None, db)
            # Ausbildungsstaettentags
            for staetteTag in staette['tags']:
                tag = AusbildungsstaettenTags(tag=staetteTag, ausbildungsstaette=ausbSt)
                tag.save(using=db)
            # Planbare Ausbildungsblöcke
            for block in staette['planbareAusbildungsbloecke']:
                fix_missing_ausbildungsblock_data(block['ausbildungsBlockId'], db)
                ausBlock = Ausbildungsbloecke.objects.using(db).get(id_ext=block['ausbildungsBlockId'])
                pA = PlanbareAusbildungsbloecke(ausbildungsblock=ausBlock, start_date=block['startDate'],
                                                ausbildungsstaette=ausbSt)
                pA.save(using=db)
                # Ausbildungsstellen
                for stelle in block['ausbildungsStellen']:
                    ausbS = Ausbildungsstelle(id_ext=stelle['id'], start_date=stelle['startDate'],
                                              duration_in_month=stelle['durationInMonths'],
                                              planbarer_ausbildungsblock=pA)
                    ausbS.save(using=db)
                # Genehmigte Fachgebiete
                for gebiet in block['genehmigteFachgebiete']:
                    genFachgebiet = Fachgebiete.objects.using(db).get(id_ext=gebiet['fachgebietId'])
                    fg = GenehmigteFachgebiete(fachgebiet=genFachgebiet, duration_in_month=gebiet['durationInMonths'],
                                               planbarer_ausbildungsblock=pA)
                    fg.save(using=db)

        import_dienstposten(kh, None, og, db)

    # Personen
    for pers in data['algorithmData']['persons']:
        person = Personen(id_ext=pers['id'], name=pers['name'])
        person.save(using=db)
        # Planungsparameter
        for param in pers['planungsParameter']:
            occGroup = OccupationalGroups.objects.using(db).get(id_ext=param['occupationalGroupId'])
            pp = PlanungsParameter(person=person, occupational_group=occGroup,
                                   hours_per_week=param['hoursPerWeek'], start_date=param['startDate'],
                                   end_date=param['endDate'], status_active=param['status'] == 'ACTIVE')
            pp.save(using=db)
            # Allowed organisation units
            for unit in param['allowedOrgUnits']:
                orgUnit = Organisationsgruppe.objects.using(db).get(id_ext=unit)
                allOrgUnit = AllowedOrganisationUnits(organisationsgruppe=orgUnit, planungs_parameter=pp)
                allOrgUnit.save(using=db)
        # Unterbrechungszeiten
        for pause in pers['unterbrechungszeiten']:
            uz = Unterbrechungszeiten(person=person, start_date=pause['startDate'], end_date=pause['endDate'])
            uz.save(using=db)
        # Ausbildungspfad
        for pfad in pers['ausbildungsPfade']:
            ausbPfad = AusbildungsPfade(id_ext=pfad['id'], start_date=pfad['startDate'], person=person)
            ausbPfad.save(using=db)
            # Ausbildungsblöcke
            for block in pfad['ausbildungsBloecke']:
                fix_missing_ausbildungsblock_data(block['ausbildungsBlockId'], db)
                ausBlock = Ausbildungsbloecke.objects.using(db).get(id_ext=block['ausbildungsBlockId'])
                personal_block = Personal.objects.using(db).get(id_ext=block['personalBlockId'])
                aBlockPfad = AusbildungsbloeckePfad(personal_block=personal_block, ausbildungspfad=ausbPfad,
                                                    ausbildungsblock=ausBlock)
                aBlockPfad.save(using=db)
                # Ausbildungserfordernisse
                for req in block['erfordernisse']:
                    ausErfor = Ausbildungserfordernisse.objects.using(db).get(id_ext=req['ausbildungsErfordernisId'])
                    personal_erfordernis = Personal.objects.using(db).get(id_ext=req['personalErfordernisId'])
                    areq = AusbildungserfordernissePfad(ausbildungserfordernis=ausErfor,
                                                        ausbildungsblock_pfad=aBlockPfad,
                                                        personal_erfordernis=personal_erfordernis,
                                                        month_completed=req['monthsCompleted'])
                    areq.save(using=db)
                    # Ausbildungsinhalte
                    for inhalt in req['inhalte']:
                        ausInhalte = Ausbildungsinhalte.objects.using(db).get(id_ext=inhalt['ausbildungsInhaltId'])
                        personal_inhalt = Personal.objects.using(db).get(id_ext=inhalt['personalInhaltId'])
                        inh = AusbildungsinhaltePfad(ausbildungsinhalte=ausInhalte, ausbildungserfordernis_pfad=areq,
                                                     personal_inhalt=personal_inhalt,
                                                     month_completed=inhalt['monthsCompleted'])
                        inh.save(using=db)
        # Organisationsgruppen priorities
        for prio in pers['organisationsGruppenPriorities']:
            orgUnit = Organisationsgruppe.objects.using(db).get(id_ext=prio)
            pr = OrganisationsGruppenPriorities(person=person, organisationsgruppe=orgUnit,
                                                priority=pers['organisationsGruppenPriorities'][prio])
            pr.save(using=db)
        # Planned Ausbildungsstelle by Fachgebiete months
        for plans in pers['plannedAusbildungsstelleByFachgebieteMonths']:
            for plan in pers['plannedAusbildungsstelleByFachgebieteMonths'][plans]:
                ausStelle = Ausbildungsstelle.objects.using(db).get(id_ext=plans)
                planFachgebiet = Fachgebiete.objects.using(db).get(id_ext=plan)
                pr = PlannedAusbildungsstelleByFachgebieteMonths(ausbildungsstelle=ausStelle, person=person,
                                                                 fachgebiet=planFachgebiet, month=
                                                                 pers['plannedAusbildungsstelleByFachgebieteMonths'][
                                                                     plans][plan])
                pr.save(using=db)

    # Zuweisungen
    for zuwei in data['algorithmData']['zuweisungen']:
        fix_missing_person_data(zuwei['personId'], db)
        person = Personen.objects.using(db).get(id_ext=zuwei['personId'])
        orgUnit = Organisationsgruppe.objects.using(db).get(id_ext=zuwei['organisationsGruppenId'])
        ausSt = Ausbildungsstaette.objects.using(db).get(id_ext=zuwei['ausbildungsstaettenId'])

        try:
            ausInhalte = Ausbildungsinhalte.objects.using(db).get(id_ext=zuwei['ausbildungsInhaltId'])
        except Ausbildungsinhalte.DoesNotExist:
            ausInhalte = None

        try:
            personalInhalt = Personal.objects.using(db).get(id_ext=zuwei['personalInhaltId'])
        except Personal.DoesNotExist:
            personalInhalt = None

        zuweisung = Zuweisungen(person=person, organisationsgruppe=orgUnit, ausbildungsstaette=ausSt,
                                ausbildungsinhalt=ausInhalte,
                                personal_inhalt=personalInhalt, start_date=zuwei['startDate'],
                                end_date=zuwei['endDate'], fixiert=zuwei['fixiert'])
        zuweisung.save(using=db)
        # Dienstpostenzuweisungen
        for dienstpostenZuwei in zuwei['dienstpostenZuweisungen']:
            dienstposten = Dienstposten.objects.using(db).get(id_ext=dienstpostenZuwei['dienstpostenId'])
            dienstpostenZuweisung = DienstpostenZuweisungen(zuweisung=zuweisung, dienstposten=dienstposten,
                                                            hours_per_week=dienstpostenZuwei['hoursPerWeek'])
            dienstpostenZuweisung.save(using=db)
        # Ausbildungsstellenzuweisungen
        for ausbildungsStellenZuwei in zuwei['ausbildungsstellenZuweisungen']:
            ausStelle = Ausbildungsstelle.objects.using(db).get(id_ext=ausbildungsStellenZuwei['ausbildungsstellenId'])
            ausbildungsStellenZuweisung = AusbildungsstellenZuweisungen(zuweisung=zuweisung,
                                                                        ausbildungsstelle=ausStelle,
                                                                        hours_per_week=ausbildungsStellenZuwei[
                                                                            'hoursPerWeek'])
            ausbildungsStellenZuweisung.save(using=db)

    # Parameter: the imported paramter is always written to id=0
    parameter, created = Parameter.objects.using(db).get_or_create(
        id=0, start_date=data['parameters']['startDate'], end_date=data['parameters']['endDate'],
        max_standstill=data['parameters']['maxStandstill'], population_size=data['parameters']['populationSize'],
        chunk_size=data['parameters']['chunkSize'], fte_in_hours=data['parameters']['fteInHours'],
        weekly_hours_needed_for_accreditation=data['parameters']['weeklyHoursNeededForAccreditation'],
        objectiveweights_single_month_assignments=data['parameters']['objectiveWeights']['singleMonthAssignments'],
        objectiveweights_months_without_training=data['parameters']['objectiveWeights']['monthsWithoutTraining'],
        objectiveweights_consecutive_months_without_training=data['parameters']['objectiveWeights'][
            'consecutiveMonthsWithoutTraining'],
        objectiveweights_hospital_changes=data['parameters']['objectiveWeights']['hospitalChanges'],
        objectiveweights_department_changes=data['parameters']['objectiveWeights']['departmentChanges'],
        objectiveweights_months_at_cooperation_partner=data['parameters']['objectiveWeights'][
            'monthsAtCooperationPartner'],
        objectiveweights_violated_preferences=data['parameters']['objectiveWeights']['violatedPreferences'],
        objectiveweights_var_months_without_training=data['parameters']['objectiveWeights']['varMonthsWithoutTraining'],
        objectiveweights_var_violated_preferences=data['parameters']['objectiveWeights']['varViolatedPreferences'],
        objectiveweights_departments_without_training=data['parameters']['objectiveWeights'][
            'departmentsWithoutTraining'],
        termination_t_type=data['parameters']['termination']['type'],
        termination_value=data['parameters']['termination']['value']
    )
    # considered Ausbildungstypen
    for conAusTyp in data['parameters']['consideredAusbildungstypen']:
        consideredAusbildungstyp = ConsideredAusbildungstypen(parameter=parameter, ausbildungstyp=conAusTyp)
        consideredAusbildungstyp.save(using=db)

    # Closing file
    f.close()
    print("Finished importing json file")

    imported_rows = Fachgebiete.objects.using(db).all().count()
    imported_rows += Ausbildungsbloecke.objects.using(db).all().count()
    imported_rows += Ausbildungserfordernisse.objects.using(db).all().count()
    imported_rows += Ausbildungsinhalte.objects.using(db).all().count()
    imported_rows += AusbildungsinhalteTags.objects.using(db).all().count()
    imported_rows += AusbildungsStellenAnforderungen.objects.using(db).all().count()
    imported_rows += OccupationalGroups.objects.using(db).all().count()
    imported_rows += Personal.objects.using(db).all().count()
    imported_rows += Organisationsgruppe.objects.using(db).all().count()
    imported_rows += Ausbildungsstaette.objects.using(db).all().count()
    imported_rows += AusbildungsstaettenTags.objects.using(db).all().count()
    imported_rows += Dienstposten.objects.using(db).all().count()
    imported_rows += OccupationalGroupsDienstposten.objects.using(db).all().count()
    imported_rows += AssociatedAusbildungsbloecke.objects.using(db).all().count()
    imported_rows += PlanbareAusbildungsbloecke.objects.using(db).all().count()
    imported_rows += Ausbildungsstelle.objects.using(db).all().count()
    imported_rows += GenehmigteFachgebiete.objects.using(db).all().count()
    imported_rows += Personen.objects.using(db).all().count()
    imported_rows += PlanungsParameter.objects.using(db).all().count()
    imported_rows += AllowedOrganisationUnits.objects.using(db).all().count()
    imported_rows += AusbildungsPfade.objects.using(db).all().count()
    imported_rows += OrganisationsGruppenPriorities.objects.using(db).all().count()
    imported_rows += Unterbrechungszeiten.objects.using(db).all().count()
    imported_rows += AusbildungsbloeckePfad.objects.using(db).all().count()
    imported_rows += AusbildungserfordernissePfad.objects.using(db).all().count()
    imported_rows += AusbildungsinhaltePfad.objects.using(db).all().count()
    imported_rows += PlannedAusbildungsstelleByFachgebieteMonths.objects.using(db).all().count()
    imported_rows += Zuweisungen.objects.using(db).all().count()
    imported_rows += DienstpostenZuweisungen.objects.using(db).all().count()
    imported_rows += AusbildungsstellenZuweisungen.objects.using(db).all().count()
    imported_rows += Parameter.objects.using(db).all().count()
    imported_rows += ConsideredAusbildungstypen.objects.using(db).all().count()

    datamodelstatus.import_date = datetime.now()
    datamodelstatus.import_file_name = os.path.basename(datamodelstatus.import_file.name)
    datamodelstatus.import_row_count = imported_rows
    datamodelstatus.save(using=db)


def import_occupational_groups(jsonPath, db):
    """ Import all occupational groups from specified json to specified database."""
    for dienst in jsonPath['dienstposten']:
        for occupationalGroup in dienst['occupationalGroups']:
            if OccupationalGroups.objects.using(db).filter(id_ext=occupationalGroup).count() == 0:
                ocGroup = OccupationalGroups(id_ext=occupationalGroup)
                ocGroup.save(using=db)


def import_personal(jsonPath, tag, db):
    """ Import all personal entries from specified json to specified database."""
    if Personal.objects.using(db).filter(id_ext=jsonPath[tag]).count() == 0:
        personal = Personal(id_ext=jsonPath[tag])
        personal.save(using=db)


def import_dienstposten(staette, ausbSt, orgGruppe, db):
    """ Import all dienstposten from specified json to specified database."""
    for dienst in staette['dienstposten']:
        dp = Dienstposten(id_ext=dienst['id'], start_date=dienst['startDate'], end_date=dienst['endDate'],
                          hours=dienst['hours'], organisationsgruppe=orgGruppe, ausbildungsstaette=ausbSt)
        dp.save(using=db)

        for occupationalGroup in dienst['occupationalGroups']:
            occGroup = OccupationalGroups.objects.using(db).get(id_ext=occupationalGroup)
            ocGroup = OccupationalGroupsDienstposten(occupational_group=occGroup, dienstposten=dp)
            ocGroup.save(using=db)

        for associatedAusbildungsbloeck in dienst['associatedAusbildungsBloecke']:
            fix_missing_ausbildungsblock_data(associatedAusbildungsbloeck, db)
            ausBlock = Ausbildungsbloecke.objects.using(db).get(id_ext=associatedAusbildungsbloeck)
            asBlock = AssociatedAusbildungsbloecke(ausbildungsblock=ausBlock, dienstposten=dp)
            asBlock.save(using=db)


def fix_missing_ausbildungsblock_data(id, db):
    """ Fix when ausbildungsbloecke are not specified, shouldn't occur on real data."""
    if Ausbildungsbloecke.objects.using(db).filter(id_ext=id).count() == 0:
        aBlock = Ausbildungsbloecke(id_ext=id, name='Missing data - inserted by importer',
                                    ausbildungstyp='Missing data - inserted by importer')
        aBlock.save(using=db)


def fix_missing_person_data(id, db):
    """ Fix when ausbildungsbloecke are not specified, shouldn't occur on real data."""
    if Personen.objects.using(db).filter(id_ext=id).count() == 0:
        person = Personen(id_ext=id, name='Missing data - inserted by importer')
        person.save(using=db)
