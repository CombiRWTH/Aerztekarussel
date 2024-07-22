from datamodel.models import *

def create_person_data(person, start_date, end_date, ausbildungstyp):
    
    ausbildungstyp = ausbildungstyp.upper()

    # create Ausbildungspfade
    if AusbildungsPfade.objects.filter(person=person).count() == 0:
        ausbPfad = AusbildungsPfade(person=person, start_date=start_date)
        ausbPfad.save()

    if check_if_new_entry_is_needed(person, ausbildungstyp):
        ausbPfad = AusbildungsPfade.objects.get(person=person)

        ausBlock = Ausbildungsbloecke.objects.get(ausbildungstyp=ausbildungstyp)
        aBlockPfad = AusbildungsbloeckePfad(personal_block=create_new_personal_block_id(), ausbildungspfad=ausbPfad, ausbildungsblock=ausBlock)
        aBlockPfad.save()

        for req in ausBlock.ausbildungserfordernisse_set.all():
            areq = AusbildungserfordernissePfad(ausbildungserfordernis=req, ausbildungsblock_pfad=aBlockPfad, 
                                                personal_erfordernis=create_new_personal_block_id(), month_completed=0)
            areq.save()

            for inhalt in req.ausbildungsinhalte_set.all():
                inh = AusbildungsinhaltePfad(ausbildungsinhalte=inhalt, ausbildungserfordernis_pfad=areq,
                                             personal_inhalt=create_new_personal_block_id(), month_completed=0)
                inh.save()

        # create PlanungsParamter
        pp = PlanungsParameter(person=person, occupational_group=get_occupational_group_fixed(ausbildungstyp),
                               hours_per_week=40, start_date=start_date,
                               end_date=end_date, status_active=True)
        pp.save()

        for unit in get_allowed_org_units(ausbildungstyp):
            allOrgUnit = AllowedOrganisationUnits(organisationsgruppe=unit, planungs_parameter=pp)
            allOrgUnit.save()

def get_occupational_group_fixed(ausbildungstyp):
    for oc_group in OccupationalGroups.objects.all():
        for oc_group_diensposten in oc_group.occupationalgroupsdienstposten_set.all():
            
            organisationsgruppe = oc_group_diensposten.dienstposten.organisationsgruppe
            if organisationsgruppe != None:
                for consideredausbildungstyp in organisationsgruppe.consideredausbildungstypen_set.all():
                    if consideredausbildungstyp.ausbildungstyp == ausbildungstyp:
                        return oc_group

            ausbildundsstaette = oc_group_diensposten.dienstposten.ausbildungsstaette
            if ausbildundsstaette != None:
                for consideredausbildungstyp in ausbildundsstaette.organisationsgruppe.consideredausbildungstypen_set.all():
                    if consideredausbildungstyp.ausbildungstyp == ausbildungstyp:
                        return oc_group

def get_allowed_org_units(ausbildungstyp):
    allowed_org_units = []

     # Organisationsgruppen
    for kh in Organisationsgruppe.objects.all():
        for consideredausbildungstyp in kh.consideredausbildungstypen_set.all():
            if ausbildungstyp == consideredausbildungstyp.ausbildungstyp:
                allowed_org_units.append(kh)

    return allowed_org_units

def create_new_personal_block_id():
    personal = Personal()
    personal.save()

    return personal

def check_if_new_entry_is_needed(person, ausbildungstyp):
    ausbPfad = AusbildungsPfade.objects.get(person=person)
    
    for ausb_block_pfad in AusbildungsbloeckePfad.objects.filter(ausbildungspfad=ausbPfad):
        if ausbildungstyp == ausb_block_pfad.ausbildungsblock.ausbildungstyp:
            return False

    return True
            