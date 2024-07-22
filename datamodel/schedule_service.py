import datetime
from datetime import timedelta
from dateutil.relativedelta import relativedelta
from datamodel.models import *

def update_schedule(X, Y, Z):
    for param in Parameter.objects.all():
        start_date_plan = param.start_date
        end_date_plan = param.end_date

    amount_of_months = abs((end_date_plan.year - start_date_plan.year) * 12 + end_date_plan.month - start_date_plan.month)+1

    Schedule.objects.all().delete()

    for t_slot in range(amount_of_months):
        for stud in Personen.objects.all():
            # Check if student (stud) got assigned to a duty position at month (t_slot) 
            if (t_slot, stud.id) in X.keys():
                # Check if student (stud) got assigned to a training position at month (t_slot) 
                if (t_slot, stud.id) in Y.keys():
                    # Check if student (stud) got progress in one content of any subject at month (t_slot) 
                    if (t_slot, stud.id) in Z.keys():
                        save_schedule(start_date_plan, t_slot, stud.id,
                                      X[(t_slot, stud.id)][0], Y[(t_slot, stud.id)][1], X[(t_slot, stud.id)][2], Z[(t_slot, stud.id)][1],
                                      Y[(t_slot, stud.id)][3], Z[(t_slot, stud.id)][0], Z[(t_slot, stud.id)][2], Z[(t_slot, stud.id)][3])
                    else:
                        save_schedule(start_date_plan, t_slot, stud.id,
                                      X[(t_slot, stud.id)][0], Y[(t_slot, stud.id)][1], X[(t_slot, stud.id)][2], Y[(t_slot, stud.id)][2],
                                      Y[(t_slot, stud.id)][3], -1, -1, -1)
                # type(X[(t_slot, stud.id)][1]) == str  
                # <=> 
                # student (Stud) was assigned to a position in the month (t_slot) that does not belong to a single department.
                elif type(X[(t_slot, stud.id)][1]) == str:
                    save_schedule(start_date_plan, t_slot, stud.id,
                                  X[(t_slot, stud.id)][0], -1, X[(t_slot, stud.id)][2], -1,
                                  -1, -1, -1, -1)
                else:
                    save_schedule(start_date_plan, t_slot, stud.id,
                                  X[(t_slot, stud.id)][0], X[(t_slot, stud.id)][1], X[(t_slot, stud.id)][2], -1,
                                  -1, -1, -1, -1)
            else:
                if (t_slot, stud.id) in Y.keys():
                    if (t_slot, stud.id) in Z.keys():
                        save_schedule(start_date_plan, t_slot, stud.id,
                                      Y[(t_slot, stud.id)][0], Y[(t_slot, stud.id)][1], -1, Z[(t_slot, stud.id)][1],
                                      Y[(t_slot, stud.id)][3], Z[(t_slot, stud.id)][0], Z[(t_slot, stud.id)][2], Z[(t_slot, stud.id)][3])
                    else:
                        save_schedule(start_date_plan, t_slot, stud.id,
                                      Y[(t_slot, stud.id)][0], Y[(t_slot, stud.id)][1], -1, Y[(t_slot, stud.id)][2],
                                      Y[(t_slot, stud.id)][3], -1, -1, -1)
                else:
                    if (t_slot, stud.id) in Z.keys():
                        save_schedule(start_date_plan, t_slot, stud.id,
                                      -1, -1, -1, Z[(t_slot, stud.id)][1],
                                      -1, Z[(t_slot, stud.id)][0], Z[(t_slot, stud.id)][2], Z[(t_slot, stud.id)][3])
                    else:
                        save_schedule(start_date_plan, t_slot, stud.id,
                                  -1, -1, -1, -1,
                                  -1, -1, -1, -1)
     # -> Different cases get checked to create the right values for the schedule and the right visualization of the schedule


def save_schedule(start_date_plan, month, student, 
                  organisationsgruppe, ausbildungsstaette, dienstposten, ausbildungsblock, 
                  ausbildungsstelle, ausbildungspfad, ausbildungserfordernis, ausbildungsinhalt):
    
    person = Personen.objects.get(id=student)

    orgUnit = safe_get(Organisationsgruppe, organisationsgruppe)
    ausSt = safe_get(Ausbildungsstaette, ausbildungsstaette)
    dienstPost = safe_get(Dienstposten, dienstposten)
    ausBlock = safe_get(Ausbildungsbloecke, ausbildungsblock)
    ausStelle = safe_get(Ausbildungsstelle, ausbildungsstelle)
    ausPfad = safe_get(AusbildungsPfade, ausbildungspfad)
    ausErf = safe_get(Ausbildungserfordernisse, ausbildungserfordernis)
    ausInhalt = safe_get(Ausbildungsinhalte, ausbildungsinhalt)

    start_date = datetime.date(start_date_plan.year, start_date_plan.month, 1) + relativedelta(months=month)
    end_date = start_date + relativedelta(months=1) - timedelta(days=1)
    
    currentSchedule = Schedule(start_date=start_date, end_date=end_date, month=month, person=person, 
                               organisationsgruppe=orgUnit, ausbildungsstaette=ausSt, dienstposten=dienstPost, ausbildungsblock=ausBlock, 
                               ausbildungsstelle=ausStelle, ausbildungspfad=ausPfad, ausbildungserfordernis=ausErf, ausbildungsinhalt=ausInhalt)
    currentSchedule.save()

def safe_get(table, id):
    try:
        return table.objects.get(id=id)
    except table.DoesNotExist:
        return None
    