from datamodel.models import *
import json
from datamodel.serializers import *

def export_db(db, name):
    printToConsole = True
    with open(name, 'w') as f:
        json_text = {}
        algorithmData = {}

########Organisationsgruppen################################################
        krankenhaeuser = []
        for kh in Organisationsgruppe.objects.using(db).all():
            serializer = OrganisationsgruppeExportSerializer(kh)
            khdata = serializer.data

            #Ausbildungsstaetten
            staetten = []
            for staette in kh.ausbildungsstaette_set.using(db).all():
                serializerStaette = AusbildungsstaetteExportSerializer(staette)
                staetteData = serializerStaette.data

                #AusbildungsstaettenTags
                tags = []
                for tag in staette.ausbildungsstaettentags_set.using(db).all():
                    tags.append(tag.tag)

                # Dienstposten
                posten = []
                for dienstposten in staette.dienstposten_set.using(db).all():
                    serializerStPosten = DienstpostenExportSerializer(dienstposten)
                    postenData = serializerStPosten.data

                    # OccupationalGroup
                    occGroups = []
                    for occupationalGroup in dienstposten.occupationalgroupsdienstposten_set.using(db).all():
                        occGroups.append(occupationalGroup.occupational_group_id)

                    # AssociatedAusbildungsbloecke
                    assocBlocks = []
                    for associatedAusbildungsbloeck in dienstposten.associatedausbildungsbloecke_set.using(db).all():
                        assocBlocks.append(associatedAusbildungsbloeck.ausbildungsblock_id)

                    postenData['occupationalGroups'] = occGroups
                    postenData['associatedAusbildungsBloecke'] = assocBlocks
                    posten.append(postenData)

                # Planbarer-Ausbildungsblock
                plBlocks = []
                for planbarerAusbildungsblock in staette.planbareausbildungsbloecke_set.using(db).all():
                    plBlockSer = PlanbareAusbildungsbloeckeExportSerializer(planbarerAusbildungsblock)
                    plBlockData = plBlockSer.data

                    # Ausbildungsstelle
                    ausbStellen = []
                    for ausbildungsStelle in planbarerAusbildungsblock.ausbildungsstelle_set.using(db).all():
                        stellenSer = AusbildungsstelleExportSerializer(ausbildungsStelle)
                        stellenData = stellenSer.data
                        ausbStellen.append(stellenData)

                    # Genehmigtes Fachgebiet
                    gebiete = []
                    for genehmigtesFachgebiet in planbarerAusbildungsblock.genehmigtefachgebiete_set.using(db).all():
                        gebietSer = GenehmigteFachgebieteExportSerializer(genehmigtesFachgebiet)
                        gebietData = gebietSer.data
                        gebiete.append(gebietData)

                    plBlockData['ausbildungsStellen'] = ausbStellen
                    plBlockData['genehmigteFachgebiete'] = gebiete
                    plBlocks.append(plBlockData)

                staetteData['tags'] = tags
                staetteData['dienstposten'] = posten
                staetteData['planbareAusbildungsbloecke'] = plBlocks
                staetten.append(staetteData)

            # Dienstposten
            posten = []
            for dienstposten in kh.dienstposten_set.using(db).all():

                serializerStPosten = DienstpostenExportSerializer(dienstposten)
                postenData = serializerStPosten.data

                # OccupationalGroup
                occGroups = []
                for occupationalGroup in dienstposten.occupationalgroupsdienstposten_set.using(db).all():
                    occGroups.append(occupationalGroup.occupational_group_id)

                # AssociatedAusbildungsbloecke
                assocBlocks = []
                for associatedAusbildungsbloeck in dienstposten.associatedausbildungsbloecke_set.using(db).all():
                    assocBlocks.append(associatedAusbildungsbloeck.ausbildungsblock_id)

                postenData['occupationalGroups'] = occGroups
                postenData['associatedAusbildungsBloecke'] = assocBlocks

                posten.append(postenData)

            khdata['ausbildungsstaetten'] = staetten
            khdata['dienstposten'] = posten
            krankenhaeuser.append(khdata)
        algorithmData['organisationsGruppen'] = krankenhaeuser

########Personen##################################################################
        personen = []
        for person in Personen.objects.using(db).all():
            serializer = PersonenExportSerializer(person)
            personData = serializer.data

            # Planungsparameter
            params = []
            for param in person.planungsparameter_set.using(db).all():
                paramSer = PlanungsParameterExportSerializer(param)
                paramData = paramSer.data

                # Allowed-Org-Unit
                units = []
                for unit in param.allowedorganisationunits_set.using(db).all():
                    units.append(unit.organisationsgruppe_id)

                paramData['allowedOrgUnits'] = units
                if paramData['status']:
                    paramData['status'] = 'ACTIVE'
                else:
                    paramData['status'] = 'INACTIVE'
                params.append(paramData)

            # Unterbrechungszeiten
            pausen = []
            for pause in person.unterbrechungszeiten_set.using(db).all():
                pauseSer = UnterbrechungszeitenExportSerializer(pause)
                pauseData = pauseSer.data
                pausen.append(pauseData)

            # Ausbildungspfad
            pfade = []
            for pfad in person.ausbildungspfade_set.using(db).all():
                pfadSer = AusbildungsPfadeExportSerializer(pfad)
                pfadData = pfadSer.data

                # Ausbildungsbloecke
                blocks = []
                for block in pfad.ausbildungsbloeckepfad_set.using(db).all():
                    blockSer = AusbildungsbloeckePfadExportSerializer(block)
                    blockData = blockSer.data
                    block2 = Ausbildungsbloecke.objects.using(db).get(id=block.ausbildungsblock_id)
                    blockData['name'] = block2.name
                    blockData['ausbildungsTyp'] = block2.ausbildungstyp

                    # Ausbildungserfordernisse
                    erfords = []
                    for erfordernisse in block.ausbildungserfordernissepfad_set.using(db).all():
                        erfordsSer = AusbildungserfordernissePfadExportSerializer(erfordernisse)
                        erfordData = erfordsSer.data
                        erfordernisData = AusbildungserfordernisseExportSerializer(Ausbildungserfordernisse.objects.using(db).get(id=erfordernisse.ausbildungserfordernis_id)).data
                        erfordernisData.update(erfordData)

                        # Ausbildungsinhalte
                        pfadInhalte = []
                        for inhalt in erfordernisse.ausbildungsinhaltepfad_set.using(db).all():
                            pfInSer = AusbildungsinhaltePfadExportSerializer(inhalt)
                            pfInData = pfInSer.data
                            inhaltData = AusbildungsinhalteExportSerializer(Ausbildungsinhalte.objects.using(db).get(id=inhalt.ausbildungsinhalte_id)).data
                            inhaltData.update(pfInData)

                            # AusbildungsinhalteTags
                            inTags = []
                            ausbTags = Ausbildungsinhalte.objects.using(db).get(id=inhalt.ausbildungsinhalte_id)
                            for tag in ausbTags.ausbildungsinhaltetags_set.using(db).all():
                                inTags.append(tag.required_tag)

                            # AusbildungsStellenAnforderungen
                            anforderungen = []
                            for ausbildungsStellenAnforderung in ausbTags.ausbildungsstellenanforderungen_set.using(db).all():
                                anfSer = AusbildungsStellenAnforderungenExportSerializer(ausbildungsStellenAnforderung)
                                anfData = anfSer.data
                                anfData['anrechenbareFachgebiete'] = [anfData['anrechenbareFachgebiete']]
                                anforderungen.append(anfData)

                            inhaltData['requiredTags'] = inTags
                            inhaltData['ausbildungsStellenAnforderungen'] = anforderungen
                            pfadInhalte.append(inhaltData)
                        erfordernisData['inhalte'] = pfadInhalte
                        erfords.append(erfordernisData)
                    blockData['erfordernisse'] = erfords
                    blocks.append(blockData)
                pfadData['ausbildungsBloecke'] = blocks
                pfade.append(pfadData)

            # OrganisationsGruppenPriorities
            prios = {}
            for prio in person.organisationsgruppenpriorities_set.using(db).all():
                prios[prio.organisationsgruppe_id] = prio.priority

            # PlannedAusbildungsstelleByFachgebieteMonths
            planned = {}
            for plans in person.plannedausbildungsstellebyfachgebietemonths_set.using(db).all():
                plan = {}
                plan[plans.fachgebiet_id] = plans.month
                planned[plans.ausbildungsstelle_id] = plan
            personData['planungsParameter'] = params
            personData['unterbrechungszeiten'] = pausen
            personData['ausbildungsPfade'] = pfade
            personData['organisationsGruppenPriorities'] = prios
            personData['plannedAusbildungsstelleByFachgebieteMonths'] = planned
            personen.append(personData)
        algorithmData['persons'] = personen

########Zuweisungen###############################################################
        zuweisungen = []
        for zuwei in Zuweisungen.objects.using(db).all():
            serializer = ZuweisungenExportSerializer(zuwei)
            zuweiData = serializer.data

            # Dienstpostenzuweisungen
            dpZuweisungen = []
            for dienstpostenZuweisung in zuwei.dienstpostenzuweisungen_set.using(db).all():
                dpZuwSer = DienstpostenZuweisungenExportSerializer(dienstpostenZuweisung)
                dpZuweisungen.append(dpZuwSer.data)

            # Ausbildungstellenzuweisungen
            ausbZuweisungen = []
            for ausbildungsstellenZuweisung in zuwei.ausbildungsstellenzuweisungen_set.using(db).all():
                ausbZuwSer = AusbildungsstellenZuweisungExportSerializer(ausbildungsstellenZuweisung)
                ausbZuweisungen.append(ausbZuwSer.data)

            zuweiData['dienstpostenZuweisungen'] = dpZuweisungen
            zuweiData['ausbildungsstellenZuweisungen'] = ausbZuweisungen
            zuweisungen.append(zuweiData)
        algorithmData['zuweisungen'] = zuweisungen

########Parameter#################################################################

        param = Parameter.objects.using(db).all().first()
        paramSerializer = ParameterExportSerializer(param)
        paramData = paramSerializer.data
        objWeightsSer = ParameterObjectiveWeightsExportSerializer(param)
        paramData['objectiveWeights'] = objWeightsSer.data
        terminationSer = ParameterTerminationExportSerializer(param)
        paramData['termination'] = terminationSer.data
        # Considered Ausbildungstypen
        typen = []
        for consideredausbildungstyp in param.consideredausbildungstypen_set.using(db).all():
            typen.append(consideredausbildungstyp.ausbildungstyp)
        paramData['consideredAusbildungstypen'] = typen
        json_text['algorithmData'] = algorithmData
        json_text['parameters'] = paramData
        json.dump(json_text, f, indent=5)
