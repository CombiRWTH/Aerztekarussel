from gurobipy import *
from datetime import datetime
from datamodel.models import *
import math
from itertools import combinations

def IP_solver(strict_var = ['x','z'], penalization_value = 100, 
              max_seconds_runtime = 300, sufficient_quality = 0.1, terminal_output = True,
              variable_prints = True, constraint_prints = True, consecutive_sections = [("BASISAUSBILDUNG", "SPITALSTURNUS")]):


    ########################
    ##### PREPARATIONS #####
    ########################

    # Access data from database and save it locally for the algorithm (Decreases runtime!)
    #
    persons = Personen.objects.all()
    parameters = Parameter.objects.all()
    hospitals = Organisationsgruppe.objects.all()
    allocations = Zuweisungen.objects.all()

    consideredausbildungstypen = []

    num_stud = len(persons)

    for param in parameters:
        start_date_plan = param.start_date
        end_date_plan = param.end_date

        for con_ausbildungstyp in param.consideredausbildungstypen_set.all():
            consideredausbildungstypen.append(con_ausbildungstyp.ausbildungstyp)

    if end_date_plan.day > 21:
        amount_of_months = abs((end_date_plan.year - start_date_plan.year) * 12 + end_date_plan.month - start_date_plan.month)+1
    else:
        amount_of_months = abs((end_date_plan.year - start_date_plan.year) * 12 + end_date_plan.month - start_date_plan.month)

    # Calculates the number of the month of the entered start date 
    #
    def StartDate_to_Timeslot(startDate):
        if type(startDate) != type(param.start_date):
            return -1
        SD = startDate
        if SD < start_date_plan:
            return -1
        if SD > end_date_plan:
            return amount_of_months
        if SD.day > 21:
            return abs((SD.year - start_date_plan.year) * 12 + SD.month - start_date_plan.month)+1
        return abs((SD.year - start_date_plan.year) * 12 + SD.month - start_date_plan.month)
    
    # Calculates the number of the month of the entered end date 
    #
    def EndDate_to_Timeslot(endDate):
        if type(endDate) != type(param.end_date):
            return amount_of_months
        ED = endDate
        if ED > end_date_plan:
            return amount_of_months
        if ED < start_date_plan:
            return -1
        if ED.day < 8:
            return abs((ED.year - start_date_plan.year) * 12 + ED.month - start_date_plan.month)-1
        return abs((ED.year - start_date_plan.year) * 12 + ED.month - start_date_plan.month)
    
    def one_value_out_of_list(L:list):
        if len(L) != 1:
            return 3
        for l in L:
            return l

    # t_slot   <-> time slot [monthly]
    # stud     <-> student
    # pp       <-> planning parameter of a student
    # h        <-> hospital
    # dep      <-> department of a hospital
    # d_pos    <-> duty position of a hospital or department
    # pt_block <-> plannable training block of a dep
    # t_pos    <-> training position of a pt_block
    # t_path   <-> training path of a person
    # t_block  <-> training block of t_path
    # subj     <-> subject of a t_block
    # c        <-> content of a subject

    # Access data from database and save it locally for the algorithm (Decreases runtime!)
    #
    h_dpos_list = {}
    h_dep_list = {}
    h_dpos_abb_list = {}
    h_dpos_og_list = {}
    h_dep_dpos_list = {}
    h_dep_ptblock_list = {}
    h_dep_abst_list = {}
    h_dep_dpos_abb_list = {}
    h_dep_dpos_og_list = {}
    h_dep_ptblock_tpos_list = {}
    h_dep_ptblock_gf_list = {}
    stud_pp_list = {}
    stud_uz_list = {}
    stud_tpath_list = {}
    stud_ogp_list = {}
    stud_month_completed = {}
    stud_duration = {}
    stud_ogp_of_h = {}
    stud_pp_aou_list = {}
    stud_tpath_tblock_list = {}
    stud_tpath_tblock_subj_list = {}
    stud_tpath_tblock_subj_c_list = {}
    stud_tpath_tblock_subj_c_absa_list = {}
    stud_tpath_tblock_subj_c_abit_list = {}

    for h in hospitals:
        h_dpos_list[h] = h.dienstposten_set.all()
        h_dep_list[h] = h.ausbildungsstaette_set.all()

        for d_pos in h_dpos_list[h]:
            h_dpos_abb_list[h, d_pos] = d_pos.associatedausbildungsbloecke_set.all()
            h_dpos_og_list[h, d_pos] = d_pos.occupationalgroupsdienstposten_set.all()

        for dep in h_dep_list[h]:
            h_dep_dpos_list[h, dep] = dep.dienstposten_set.all()
            h_dep_ptblock_list[h, dep] = dep.planbareausbildungsbloecke_set.all()
            h_dep_abst_list[h, dep] = dep.ausbildungsstaettentags_set.all()

            for d_pos in h_dep_dpos_list[h, dep]:
                h_dep_dpos_abb_list[h, dep, d_pos] = d_pos.associatedausbildungsbloecke_set.all()
                h_dep_dpos_og_list[h, dep, d_pos] = d_pos.occupationalgroupsdienstposten_set.all()

            for pt_block in h_dep_ptblock_list[h, dep]:
                h_dep_ptblock_tpos_list[h, dep, pt_block] = pt_block.ausbildungsstelle_set.all()
                h_dep_ptblock_gf_list[h, dep, pt_block] = pt_block.genehmigtefachgebiete_set.all()

    for stud in persons:
        stud_pp_list[stud] = stud.planungsparameter_set.all()
        stud_uz_list[stud] = [tslot for uz in stud.unterbrechungszeiten_set.all() for tslot in list(range(max(StartDate_to_Timeslot(uz.start_date), 0), min(EndDate_to_Timeslot(uz.end_date)+1, amount_of_months)))]
        stud_tpath_list[stud] = stud.ausbildungspfade_set.all()
        stud_ogp_list[stud] = stud.organisationsgruppenpriorities_set.all()
        stud_month_completed[stud] = 0
        stud_duration[stud] = 0

        for h in hospitals:
            stud_ogp_of_h[stud, h] = one_value_out_of_list([ogp.priority for ogp in stud_ogp_list[stud] if ogp.organisationsgruppe_id == h.id])

        for pp in stud_pp_list[stud]:
            stud_pp_aou_list[stud, pp] = pp.allowedorganisationunits_set.all()

        for t_path in stud_tpath_list[stud]:
            stud_tpath_tblock_list[stud, t_path] = t_path.ausbildungsbloeckepfad_set.all()
            for t_block in stud_tpath_tblock_list[stud, t_path]:
                if t_block.ausbildungsblock.ausbildungstyp in consideredausbildungstypen:
                    stud_tpath_tblock_subj_list[stud, t_path, t_block] = t_block.ausbildungserfordernissepfad_set.all()
                    for subj in stud_tpath_tblock_subj_list[stud, t_path, t_block]:
                        stud_tpath_tblock_subj_c_list[stud, t_path, t_block, subj] = subj.ausbildungsinhaltepfad_set.all()
                        stud_month_completed[stud] = stud_month_completed[stud] + min((subj.month_completed, subj.ausbildungserfordernis.duration))
                        stud_duration[stud] = stud_duration[stud] + subj.ausbildungserfordernis.duration
                        for c in stud_tpath_tblock_subj_c_list[stud, t_path, t_block, subj]:
                            stud_tpath_tblock_subj_c_absa_list[stud, t_path, t_block, subj, c] = c.ausbildungsinhalte.ausbildungsstellenanforderungen_set.all()
                            stud_tpath_tblock_subj_c_abit_list[stud, t_path, t_block, subj, c] = c.ausbildungsinhalte.ausbildungsinhaltetags_set.all()

    # Returns the objective weight when student (stud) would work in hospital (h)
    #
    def ObjectiveWeight(stud, h):
        objw = 0

        if h.is_kooperationspartner:
            for param in parameters:
                objw = objw + param.objectiveweights_months_at_cooperation_partner

        if stud_ogp_of_h[stud, h] > min([ogp.priority for ogp in stud_ogp_list[stud]]):
            for param in parameters:
                objw = objw + (stud_ogp_of_h[stud, h] - min([ogp.priority for ogp in stud_ogp_list[stud]]))*param.objectiveweights_violated_preferences

        return objw
    
    def max_list(l:list):
        if len(l) > 0:
            return [max(l)]
        return []

    # Returns True if and only if station (dep) of hospital (h) of the input fulfills one area of expertise for the content (c) of student (stud) of the input
    #
    def Areas_of_expertise_fulfilled(stud, t_path, t_block, subj, c, h, dep, pt_block):
        ausbildungsstellenanforderung_größer_null = False
        for aSA in stud_tpath_tblock_subj_c_absa_list[stud, t_path, t_block, subj, c]:
            ausbildungsstellenanforderung_größer_null = True
            if aSA.fachgebiet_id in [gF.fachgebiet.id for gF in h_dep_ptblock_gf_list[h, dep, pt_block]]:
                return True
        
        if ausbildungsstellenanforderung_größer_null:
            return False
        else:
            return True

    # Returns the id of the training block type from the input
    #
    def training_type_to_id(t_path, t_block_type):
        for t_block in stud_tpath_tblock_list[stud, t_path]:
            if t_block.ausbildungsblock.ausbildungstyp == t_block_type:
                return t_block.ausbildungsblock_id        
            
    # Returns True if and only if station (dep) of hospital (h) of the input fulfills all tags for the content (c) of student (stud) of the input
    #
    def tags_fulfilled(stud, t_path, t_block, subj, c, h, dep):
        for rt in stud_tpath_tblock_subj_c_abit_list[stud, t_path, t_block, subj, c]:
            contained = False
            for t in h_dep_abst_list[h, dep]:
                if rt.required_tag == t.tag:
                    contained = True
                    break
            if not contained:
                return False
        return True
    
    # Returns all sublists of length k from a list of length n with n >= k
    #
    def k_lists_from_n_list(n_list, k):
        if k > len(n_list):
            return []
        k_lists = []
        k_lists.extend(combinations(n_list, k))
        return k_lists
    
    # Helps to see the progress of the algorithm in the terminal
    #
    def print_progress_bar(type_for_print, type_number, counter, after_z = 1, after_x = 1, maximum_number = num_stud):
        if type_for_print == 'v' and variable_prints:
            div = max(math.floor(maximum_number/20),1)
            if 'x' not in strict_var:
                if 'z' not in strict_var:
                    print(f"Adding variable type {type_number+after_x+after_z}/15:  {round(counter*100/maximum_number)}%"+f" ({counter}/{maximum_number}) "+"|"+math.floor(counter/div)*"#"+max(math.ceil((maximum_number-counter)/div),0)*" "+"|", end='\r')
                else:
                    print(f"Adding variable type {type_number+after_x}/14:  {round(counter*100/maximum_number)}%"+f" ({counter}/{maximum_number}) "+"|"+math.floor(counter/div)*"#"+max(math.ceil((maximum_number-counter)/div),0)*" "+"|", end='\r')
            else:
                if 'z' not in strict_var:
                    print(f"Adding variable type {type_number+after_z}/14:  {round(counter*100/maximum_number)}%"+f" ({counter}/{maximum_number}) "+"|"+math.floor(counter/div)*"#"+max(math.ceil((maximum_number-counter)/div),0)*" "+"|", end='\r')
                else:    
                    print(f"Adding variable type {type_number}/13:  {round(counter*100/maximum_number)}%"+f" ({counter}/{maximum_number}) "+"|"+math.floor(counter/div)*"#"+max(math.ceil((maximum_number-counter)/div),0)*" "+"|", end='\r')
        if type_for_print == 'c' and constraint_prints:
            div = max(math.floor(maximum_number/20),1)
            print(f"Adding constraint type {type_number}/22:  {round(counter*100/maximum_number)}%"+f" ({counter}/{maximum_number}) "+"|"+math.floor(counter/div)*"#"+max(math.ceil((maximum_number-counter)/div),0)*" "+"|", end='\r')

    # Helps to see the progress of the algorithm in the terminal
    #
    def print_end_notification(type_for_print, type_number, after_progress_bar = False, after_z = 1, after_x = 1, maximum_number = num_stud):
        if type_for_print == 'v' and variable_prints:
            if after_progress_bar:
                div = max(math.floor(maximum_number/20),1)
            if 'x' not in strict_var:
                if 'z' not in strict_var:
                    if after_progress_bar:
                        print(f"Adding variable type {type_number+after_x+after_z}/15:  {100}%"+f" ({maximum_number}/{maximum_number}) "+"|"+math.ceil(maximum_number/div)*"#"+"|")
                    print(f"Variable type {type_number+after_x+after_z}/15 added!")
                else:
                    if after_progress_bar:
                        print(f"Adding variable type {type_number+after_x}/14:  {100}%"+f" ({maximum_number}/{maximum_number}) "+"|"+math.ceil(maximum_number/div)*"#"+"|")
                    print(f"Variable type {type_number+after_x}/14 added!")
            else:
                if 'z' not in strict_var:
                    if after_progress_bar:
                        print(f"Adding variable type {type_number+after_z}/14:  {100}%"+f" ({maximum_number}/{maximum_number}) "+"|"+math.ceil(maximum_number/div)*"#"+"|")
                    print(f"Variable type {type_number+after_z}/14 added!")
                else:
                    if after_progress_bar:
                        print(f"Adding variable type {type_number}/13:  {100}%"+f" ({maximum_number}/{maximum_number}) "+"|"+math.ceil(maximum_number/div)*"#"+"|")
                    print(f"Variable type {type_number}/13 added!")
            print(" ")
        if type_for_print == 'c' and constraint_prints:
            if after_progress_bar:
                div = max(math.floor(maximum_number/20),1)
                print(f"Adding constraint type {type_number}/22:  {100}%"+f" ({maximum_number}/{maximum_number}) "+"|"+math.ceil(maximum_number/div)*"#"+"|")
            print(f"Constraint type {type_number}/22 added!")
            print(" ")

    # This method allows the algorithm to terminate if the current best solution has at most a specific quality gap to the best solution
    #
    def softtime(model, where):
        if where == GRB.Callback.MIP:
            runtime = model.cbGet(GRB.Callback.RUNTIME)
            objbst = model.cbGet(GRB.Callback.MIP_OBJBST)
            objbnd = model.cbGet(GRB.Callback.MIP_OBJBND)

            if objbnd > 0.0001:
                gap = (objbst - objbnd) / objbnd
                if runtime > 10 and gap < sufficient_quality:
                    model.terminate()


    model = Model("Aerztekarussell")

    if not terminal_output:
        model.setParam("OutputFlag", 0)

    if type(max_seconds_runtime) in [float, int]:
        if max_seconds_runtime > 1:
            model.setParam('TimeLimit', max_seconds_runtime)

    print('\nPreparations completed!\n')

    #####################
    ##### VARIABLES #####
    #####################

    # x[t_slot, stud, h, dep, d_pos] = 1
    # <=> student (stud) is assigned in hospital (h) [in department (dep)] to duty position (d_pos) at month (t_slot) 
    x = {}
    counter = 0
    for stud in persons:
        counter = counter + 1
        print_progress_bar('v', 1, counter, 0, 0)
        for pp in stud_pp_list[stud]:
            for t_slot in range(max(StartDate_to_Timeslot(pp.start_date), 0), min(EndDate_to_Timeslot(pp.end_date)+1, amount_of_months)):
                if t_slot not in stud_uz_list[stud]:
                    for h in hospitals:
                        if h.id in [aou.organisationsgruppe_id for aou in stud_pp_aou_list[stud, pp]]:
                            for d_pos in [dpos for dpos in h_dpos_list[h] if pp.occupational_group.id in [og.occupational_group.id for og in h_dpos_og_list[h, dpos]]]:
                                if t_slot >= StartDate_to_Timeslot(d_pos.start_date) and t_slot <= EndDate_to_Timeslot(d_pos.end_date):
                                    x[t_slot, stud.id, h.id, str(h.id), d_pos.id] = model.addVar(vtype=GRB.BINARY, obj=ObjectiveWeight(stud, h))
                            for dep in h_dep_list[h]:
                                for d_pos in [dpos for dpos in h_dep_dpos_list[h, dep] if pp.occupational_group.id in [og.occupational_group.id for og in h_dep_dpos_og_list[h, dep, dpos]]]:
                                    if t_slot >= StartDate_to_Timeslot(d_pos.start_date) and t_slot <= EndDate_to_Timeslot(d_pos.end_date):
                                        x[t_slot, stud.id, h.id, dep.id, d_pos.id] = model.addVar(vtype=GRB.BINARY, obj=ObjectiveWeight(stud, h))
    print_end_notification('v', 1, True, 0, 0)
    if 'x' not in strict_var:
        counter = 0
        for stud in persons:
            counter = counter + 1
            print_progress_bar('v', 2, counter, 0, 0)
            for pp in stud_pp_list[stud]:
                for t_slot in range(max(StartDate_to_Timeslot(pp.start_date), 0), min(EndDate_to_Timeslot(pp.end_date)+1, amount_of_months)):
                    if t_slot not in stud_uz_list[stud]:
                        x[t_slot, stud.id, 0] = model.addVar(vtype=GRB.BINARY, obj=penalization_value)
        print_end_notification('v', 2, True, 0, 0)

    # y[t_slot, stud, h, dep, pt_block, t_pos] = 1
    # <=> student (stud) is assigned in hospital (h) in department (dep) in the plannable training block (pt_block) to training position (t_pos) at month (t_slot)
    y = {}
    counter = 0
    for stud in persons:
        counter = counter + 1
        print_progress_bar('v', 2, counter, 0)
        for pp in stud_pp_list[stud]:
            for t_slot in range(max(StartDate_to_Timeslot(pp.start_date), 0), min(EndDate_to_Timeslot(pp.end_date)+1, amount_of_months)):
                if t_slot not in stud_uz_list[stud]:
                    for param in parameters:
                        y[t_slot, stud.id, 0] = model.addVar(vtype=GRB.BINARY, obj=param.objectiveweights_months_without_training)
                        y[t_slot, stud.id, 1] = model.addVar(vtype=GRB.BINARY, obj=(-1)*param.objectiveweights_months_without_training)
                    for h in hospitals:
                        if h.id in [aou.organisationsgruppe_id for aou in stud_pp_aou_list[stud, pp]]:
                            for dep in h_dep_list[h]:
                                for pt_block in h_dep_ptblock_list[h, dep]:
                                    if t_slot >= StartDate_to_Timeslot(pt_block.start_date):
                                        for t_pos in h_dep_ptblock_tpos_list[h, dep, pt_block]:
                                            if t_slot >= StartDate_to_Timeslot(t_pos.start_date):
                                                y[t_slot, stud.id, h.id, dep.id, pt_block.ausbildungsblock_id, t_pos.id] = model.addVar(vtype=GRB.BINARY)
    print_end_notification('v', 2, True, 0)
    
    # z[t_slot, stud, t_path, t_block, subj, c] = 1
    # <=> student (stud) is assigned in training path (t_path) in training block (t_block) in subject (subj) to content (c) at month (t_slot)
    z = {}
    counter = 0
    for stud in persons:
        counter = counter + 1
        print_progress_bar('v', 3, counter, 0)
        for pp in stud_pp_list[stud]:
            for t_slot in range(max(StartDate_to_Timeslot(pp.start_date), 0), min(EndDate_to_Timeslot(pp.end_date)+1, amount_of_months)):    
                if t_slot not in stud_uz_list[stud]:
                    for t_path in stud_tpath_list[stud]:
                        if t_slot >= StartDate_to_Timeslot(t_path.start_date):
                            for t_block in stud_tpath_tblock_list[stud, t_path]:
                                if t_block.ausbildungsblock.ausbildungstyp in consideredausbildungstypen:
                                    for subj in stud_tpath_tblock_subj_list[stud, t_path, t_block]:
                                        for c in stud_tpath_tblock_subj_c_list[stud, t_path, t_block, subj]:
                                            if c.ausbildungsinhalte.max_duration - c.month_completed > 0:
                                                z[t_slot, stud.id, t_path.id, t_block.ausbildungsblock_id, subj.ausbildungserfordernis.id, c.ausbildungsinhalte.id] = model.addVar(vtype=GRB.BINARY)                                        
    print_end_notification('v', 3, True, 0)
    if 'z' not in strict_var:
        counter = 0
        for stud in persons:
            counter = counter + 1
            print_progress_bar('v', 4, counter, 0)
            for t_path in stud_tpath_list[stud]:
                for t_block in stud_tpath_tblock_list[stud, t_path]:
                    if t_block.ausbildungsblock.ausbildungstyp in consideredausbildungstypen:
                        for subj in stud_tpath_tblock_subj_list[stud, t_path, t_block]:
                            z[stud.id, t_path.id, t_block.ausbildungsblock_id, subj.ausbildungserfordernis.id] = model.addVar(vtype=GRB.INTEGER, obj=penalization_value)
                            for c in stud_tpath_tblock_subj_c_list[stud, t_path, t_block, subj]:
                                if c.ausbildungsinhalte.max_duration - c.month_completed > 0:
                                    z['-1', stud.id, t_path.id, t_block.ausbildungsblock_id, subj.ausbildungserfordernis.id, c.ausbildungsinhalte.id] = model.addVar(vtype=GRB.INTEGER, obj=penalization_value)
                                    z['+1', stud.id, t_path.id, t_block.ausbildungsblock_id, subj.ausbildungserfordernis.id, c.ausbildungsinhalte.id] = model.addVar(vtype=GRB.INTEGER, obj=penalization_value)
        print_end_notification('v', 4, True, 0)

    # zc[stud, t_path, t_block, subj, c] = 1
    # <=> the content (c) gets chosen in training path (t_path) in training block (t_block) for subject (subj) for student (stud) 
    zc = {}
    counter = 0
    for stud in persons:
        counter = counter + 1
        print_progress_bar('v', 4, counter)
        for t_path in stud_tpath_list[stud]:
            for t_block in stud_tpath_tblock_list[stud, t_path]:
                if t_block.ausbildungsblock.ausbildungstyp in consideredausbildungstypen:
                    for subj in stud_tpath_tblock_subj_list[stud, t_path, t_block]:
                        for c in stud_tpath_tblock_subj_c_list[stud, t_path, t_block, subj]:
                            zc[stud.id, t_path.id, t_block.ausbildungsblock_id, subj.ausbildungserfordernis.id, c.ausbildungsinhalte.id] = model.addVar(vtype=GRB.BINARY)
    print_end_notification('v', 4, True)

    # zsf[t_slot, stud, t_path, t_block] = 1
    # <=> the training block (t_block) of training path (t_path) of student (stud) is finished at month (t_slot)
    zsf = {}
    counter = 0
    for stud in persons:
        counter = counter + 1
        print_progress_bar('v', 5, counter)
        for t_slot in range(-1, amount_of_months):
            for t_path in stud_tpath_list[stud]:
                for t_block in stud_tpath_tblock_list[stud, t_path]:
                    if t_block.ausbildungsblock.ausbildungstyp in consideredausbildungstypen:
                        zsf[t_slot, stud.id, t_path.id, t_block.ausbildungsblock_id] = model.addVar(vtype=GRB.BINARY)
    print_end_notification('v', 5, True)

    # vvp[0] = Approximation of the variance of the violated preferences of all students
    #
    vvp = {}
    for param in parameters:
        if param.objectiveweights_var_violated_preferences > 0 and num_stud > 1:
            adtm_vp = {}  # -> Absolute distance of the violated preferences of a student (stud) to the mean 
            qdtm_vp = {}  # -> Approximation of the quadratic distance of the violated preferences of a student (stud) to the mean
            for stud in persons:
                adtm_vp[stud.id] = model.addVar(vtype=GRB.CONTINUOUS)
                for t_slot in range(amount_of_months):
                    qdtm_vp[t_slot, stud.id] = model.addVar(vtype=GRB.CONTINUOUS, ub=(2*t_slot+1))
            
            vvp[0] = model.addVar(vtype=GRB.CONTINUOUS, obj=param.objectiveweights_var_violated_preferences)
    print_end_notification('v', 6)
            
    # vmwt[0] = Approximation of the variance of the months without training of all students
    #
    vmwt = {}
    for param in parameters:
        if param.objectiveweights_var_months_without_training > 0 and num_stud > 1:
            adtm_mwt = {}  # -> Absolute distance of the months without training of a student (stud) to the mean
            qdtm_mwt = {}  # -> Approximation of the quadratic distance of the months without training of a student (stud) to the mean
            for stud in persons:
                adtm_mwt[stud.id] = model.addVar(vtype=GRB.CONTINUOUS)
                for t_slot in range(amount_of_months):
                    qdtm_mwt[t_slot, stud.id] = model.addVar(vtype=GRB.CONTINUOUS, ub=(2*t_slot+1))
            
            vmwt[0] = model.addVar(vtype=GRB.CONTINUOUS, obj=param.objectiveweights_var_months_without_training)
    print_end_notification('v', 7)
    
    # vwmwt[0] = Approximation of the variance of the weighted months without training of all students
    # -> Trying to avoid assigning months without training to students who have completed more of their training than students who have completed less of their training
    vwmwt = {}
    for param in parameters:
        if param.objectiveweights_var_weighted_months_without_training > 0 and num_stud > 1:
            adtm_wmwt = {}  # -> Absolute distance of the months without training of a student (stud) to the mean
            qdtm_wmwt = {}  # -> Approximation of the quadratic distance of the months without training of a student (stud) to the mean
            for stud in persons:
                if (stud_duration[stud] - stud_month_completed[stud]) > 0.5:
                    adtm_wmwt[stud.id] = model.addVar(vtype=GRB.CONTINUOUS)
                    for t_slot in range(amount_of_months):
                        qdtm_wmwt[t_slot, stud.id] = model.addVar(vtype=GRB.CONTINUOUS, ub=(2*t_slot+1))
            
            vwmwt[0] = model.addVar(vtype=GRB.CONTINUOUS, obj=param.objectiveweights_var_weighted_months_without_training)
    print_end_notification('v', 8)

    # cmwt[t_slot, stud] = 1
    # <=> student (stud) is not assigned to any training position at month (t_slot) and month (t_slot - 1)
    cmwt = {}
    for param in parameters:
        if param.objectiveweights_consecutive_months_without_training > 0:
            for stud in persons:
                for pp in stud_pp_list[stud]:
                    for t_slot in range(max(StartDate_to_Timeslot(pp.start_date), 0), min(EndDate_to_Timeslot(pp.end_date)+1, amount_of_months)):
                        if t_slot not in stud_uz_list[stud]:
                            if t_slot == 0:
                                if len([aa for aa in allocations if aa.person_id == stud.id]) > 0:
                                    cmwt[t_slot, stud.id] = model.addVar(vtype=GRB.BINARY, obj=param.objectiveweights_consecutive_months_without_training)
                            else:
                                if t_slot-1 in [tslot for ppp in stud_pp_list[stud] for tslot in range(max(StartDate_to_Timeslot(ppp.start_date), 0), min(EndDate_to_Timeslot(ppp.end_date)+1, amount_of_months)) if tslot not in stud_uz_list[stud]]:
                                    cmwt[t_slot, stud.id] = model.addVar(vtype=GRB.BINARY, obj=param.objectiveweights_consecutive_months_without_training)
    print_end_notification('v', 9)
                                    
    # dwt[t_slot, h, dep] = 1
    # <=> department (dep) in hospital (h) gets no student assigned to any training position of the department at month (t_slot)
    dwt = {}
    for param in parameters:
        if param.objectiveweights_departments_without_training > 0:
            for t_slot in range(amount_of_months):
                for h in hospitals:
                    for dep in h_dep_list[h]:
                        dwt[t_slot, h.id, dep.id] = model.addVar(vtype=GRB.BINARY, obj= param.objectiveweights_departments_without_training)
    print_end_notification('v', 10)
                        
    # hc[t_slot, stud] = 1
    # <=> student (stud) changes hospital at month (t_slot) [i.e. between a month (t_slot2 [<= t_slot]) and (t_slot)]
    hc = {}
    for param in parameters:
        if  param.objectiveweights_hospital_changes > 0:
            for stud in persons:
                for pp in stud_pp_list[stud]:
                    for t_slot in range(max(StartDate_to_Timeslot(pp.start_date), 0), min(EndDate_to_Timeslot(pp.end_date)+1, amount_of_months)):
                        if len(stud_pp_aou_list[stud, pp]) > 1 or t_slot == StartDate_to_Timeslot(pp.start_date) or (StartDate_to_Timeslot(pp.start_date) == -1 and t_slot == 0):
                            hc[t_slot, stud.id] = model.addVar(vtype=GRB.BINARY, obj= param.objectiveweights_hospital_changes)
    print_end_notification('v', 11)
                            
    # dc[t_slot, stud] = 1
    # <=> student (stud) changes department at month (t_slot) [i.e. between a month (t_slot2 [<= t_slot]) and (t_slot)]
    dc = {}
    for param in parameters:
        if  param.objectiveweights_department_changes > 0:
            for stud in persons:
                for pp in stud_pp_list[stud]:
                    for t_slot in range(max(StartDate_to_Timeslot(pp.start_date), 0), min(EndDate_to_Timeslot(pp.end_date)+1, amount_of_months)):
                        dc[t_slot, stud.id] = model.addVar(vtype=GRB.BINARY, obj= param.objectiveweights_department_changes)
    print_end_notification('v', 12)
                        
    # sma[t_slot, stud] = 1
    # <=> student (stud) is assigned to a department at month (t_slot) but not to the same department at month (t_slot - 1) and (t_slot + 1)
    sma = {}
    for param in parameters:
        if param.objectiveweights_single_month_assignments > 0:
            for stud in persons:
                for pp in stud_pp_list[stud]:
                    for t_slot in range(max(StartDate_to_Timeslot(pp.start_date), 0), min(EndDate_to_Timeslot(pp.end_date)+1, amount_of_months)):
                        sma[t_slot, stud.id] = model.addVar(vtype=GRB.BINARY, obj= param.objectiveweights_single_month_assignments)
    print_end_notification('v', 13)


    model.update()


    print('\nVariables added successfully!\n\n')

    #######################
    ##### CONSTRAINTS #####
    #######################

    # Every student has to work in exactly one duty position and in at most one training position at the same time slot
    #
    counter = 0
    for stud in persons:
        counter = counter + 1
        print_progress_bar('c', 1, counter)
        for pp in stud_pp_list[stud]:
            for t_slot in range(max(StartDate_to_Timeslot(pp.start_date), 0), min(EndDate_to_Timeslot(pp.end_date)+1, amount_of_months)):
                if t_slot not in stud_uz_list[stud]:
                    model.addConstr(1 == y[t_slot, stud.id, 1]
                                      +  quicksum(x[t_slot, stud.id, 0] for not_strict in [n_strict for n_strict in range(1) if 'x' not in strict_var])
                                      +  quicksum(
                                         quicksum(
                                         quicksum(x[t_slot, stud.id, h.id, dep.id, d_pos.id] for d_pos in [dpos for dpos in h_dep_dpos_list[h, dep] if  t_slot >= StartDate_to_Timeslot(dpos.start_date) 
                                                                                                                                                    and t_slot <= EndDate_to_Timeslot(dpos.end_date)
                                                                                                                                                    and pp.occupational_group.id in [og.occupational_group.id for og in h_dep_dpos_og_list[h, dep, dpos]]])
                                                                                             for dep in h_dep_list[h])
                                      +  quicksum(x[t_slot, stud.id, h.id, str(h.id), d_pos.id] for d_pos in [dpos for dpos in h_dpos_list[h] if  t_slot >= StartDate_to_Timeslot(dpos.start_date)
                                                                                                                                              and t_slot <= EndDate_to_Timeslot(dpos.end_date)
                                                                                                                                              and pp.occupational_group.id in [og.occupational_group.id for og in h_dpos_og_list[h, dpos]]])
                                                                                                for h in [h for h in hospitals if h.id in [aou.organisationsgruppe_id for aou in stud_pp_aou_list[stud, pp]]]))
                    model.addConstr(1 == y[t_slot, stud.id, 0]
                                      +  quicksum(
                                         quicksum(
                                         quicksum(
                                         quicksum(y[t_slot, stud.id, h.id, dep.id, pt_block.ausbildungsblock_id, t_pos.id] for t_pos in [tpos for tpos in h_dep_ptblock_tpos_list[h, dep, pt_block] if t_slot >= StartDate_to_Timeslot(tpos.start_date)])
                                                                                                                           for pt_block in [ptblock for ptblock in h_dep_ptblock_list[h, dep] if t_slot >= StartDate_to_Timeslot(ptblock.start_date)])
                                                                                                                           for dep in h_dep_list[h])
                                                                                                                           for h in [h for h in hospitals if h.id in [aou.organisationsgruppe_id for aou in stud_pp_aou_list[stud, pp]]]))
    print_end_notification('c', 1, True)

    # (added just to increase the effectiveness of the IP)
    #
    counter = 0
    for stud in persons:
        counter = counter + 1
        print_progress_bar('c', 2, counter)
        for pp in stud_pp_list[stud]:
            for t_slot in range(max(StartDate_to_Timeslot(pp.start_date), 0), min(EndDate_to_Timeslot(pp.end_date)+1, amount_of_months)):
                if t_slot not in stud_uz_list[stud]:
                    model.addConstr(y[t_slot, stud.id, 0] >= y[t_slot, stud.id, 1]) 
    print_end_notification('c', 2, True)

    # Every training position has only the capacity for one student at the same time slot
    #
    counter = 0
    for t_slot in range(amount_of_months):
        counter = counter + 1
        print_progress_bar('c', 3, counter, 0, 0, amount_of_months)
        for h in hospitals:
            for dep in h_dep_list[h]:
                for pt_block in h_dep_ptblock_list[h, dep]:
                    if t_slot >= StartDate_to_Timeslot(pt_block.start_date):
                        for t_pos in h_dep_ptblock_tpos_list[h, dep, pt_block]:
                            if t_slot >= StartDate_to_Timeslot(t_pos.start_date):
                                model.addConstr(1 >= quicksum(y[t_slot, stud.id, h.id, dep.id, pt_block.ausbildungsblock_id, t_pos.id] for stud in [stud for stud in persons for pp in stud_pp_list[stud] if  t_slot >= StartDate_to_Timeslot(pp.start_date)
                                                                                                                                                                                                          and t_slot <= EndDate_to_Timeslot(pp.end_date) 
                                                                                                                                                                                                          and t_slot not in stud_uz_list[stud]
                                                                                                                                                                                                          and h.id in [aou.organisationsgruppe_id for aou in stud_pp_aou_list[stud, pp]]]))   
    print_end_notification('c', 3, True, 0, 0, amount_of_months)

    # Every duty position has only the capacity for one student at the same time slot
    #
    counter = 0
    for t_slot in range(amount_of_months):
        counter = counter + 1
        print_progress_bar('c', 4, counter, 0, 0, amount_of_months)
        for h in hospitals:
            for d_pos in h_dpos_list[h]:
                if t_slot >= StartDate_to_Timeslot(d_pos.start_date) and t_slot <= EndDate_to_Timeslot(d_pos.end_date):
                    model.addConstr(1 >= quicksum(x[t_slot, stud.id, h.id, str(h.id), d_pos.id] for stud in [stud for stud in persons for pp in stud_pp_list[stud] if  t_slot >= StartDate_to_Timeslot(pp.start_date)
                                                                                                                                                                   and t_slot <= EndDate_to_Timeslot(pp.end_date) 
                                                                                                                                                                   and t_slot not in stud_uz_list[stud]
                                                                                                                                                                   and h.id in [aou.organisationsgruppe_id for aou in stud_pp_aou_list[stud, pp]]
                                                                                                                                                                   and pp.occupational_group.id in [og.occupational_group.id for og in h_dpos_og_list[h, d_pos]]]))
            for dep in h_dep_list[h]:
                for d_pos in h_dep_dpos_list[h, dep]:
                    if t_slot >= StartDate_to_Timeslot(d_pos.start_date) and t_slot <= EndDate_to_Timeslot(d_pos.end_date):
                        model.addConstr(1 >= quicksum(x[t_slot, stud.id, h.id, dep.id, d_pos.id] for stud in [stud for stud in persons for pp in stud_pp_list[stud] if  t_slot >= StartDate_to_Timeslot(pp.start_date)
                                                                                                                                                                    and t_slot <= EndDate_to_Timeslot(pp.end_date) 
                                                                                                                                                                    and t_slot not in stud_uz_list[stud]
                                                                                                                                                                    and h.id in [aou.organisationsgruppe_id for aou in stud_pp_aou_list[stud, pp]]
                                                                                                                                                                    and pp.occupational_group.id in [og.occupational_group.id for og in h_dep_dpos_og_list[h, dep, d_pos]]]))
    print_end_notification('c', 4, True, 0, 0, amount_of_months)

    # Every student has to be assigned to a duty position at the same hospital and department (and at an associated training block) for their training position at the same time slot
    #
    counter = 0
    for stud in persons:
        counter = counter + 1
        print_progress_bar('c', 5, counter)
        for pp in stud_pp_list[stud]:
            for t_slot in range(max(StartDate_to_Timeslot(pp.start_date), 0), min(EndDate_to_Timeslot(pp.end_date)+1, amount_of_months)):
                if t_slot not in stud_uz_list[stud]:
                    for h in [h for h in hospitals if h.id in [aou.organisationsgruppe_id for aou in stud_pp_aou_list[stud, pp]]]:
                        for dep in h_dep_list[h]:
                            for pt_block in [ptblock for ptblock in h_dep_ptblock_list[h, dep] if t_slot >= StartDate_to_Timeslot(ptblock.start_date)]:
                                for t_pos in [tpos for tpos in h_dep_ptblock_tpos_list[h, dep, pt_block] if t_slot >= StartDate_to_Timeslot(tpos.start_date)]:
                                    model.addConstr(y[t_slot, stud.id, h.id, dep.id, pt_block.ausbildungsblock_id, t_pos.id]
                                                    <= quicksum(x[t_slot, stud.id, 0] for not_strict in [n_strict for n_strict in range(1) if 'x' not in strict_var])
                                                    +  quicksum(x[t_slot, stud.id, h.id, dep.id, d_pos.id] for d_pos in [dpos for dpos in h_dep_dpos_list[h, dep] if  t_slot >= StartDate_to_Timeslot(dpos.start_date) 
                                                                                                                                                                  and t_slot <= EndDate_to_Timeslot(dpos.end_date)
                                                                                                                                                                  and pt_block.ausbildungsblock_id in [abb.ausbildungsblock_id for abb in h_dep_dpos_abb_list[h, dep, dpos]]
                                                                                                                                                                  and pp.occupational_group.id in [og.occupational_group.id for og in h_dep_dpos_og_list[h, dep, dpos]]])
                                                    +  quicksum(x[t_slot, stud.id, h.id, str(h.id), d_pos.id] for d_pos in [dpos for dpos in h_dpos_list[h] if  t_slot >= StartDate_to_Timeslot(dpos.start_date) 
                                                                                                                                                            and t_slot <= EndDate_to_Timeslot(dpos.end_date)
                                                                                                                                                            and pt_block.ausbildungsblock_id in [abb.ausbildungsblock_id for abb in h_dpos_abb_list[h, dpos]]
                                                                                                                                                            and pp.occupational_group.id in [og.occupational_group.id for og in h_dpos_og_list[h, dpos]]]))
    print_end_notification('c', 5, True)

    # Every student gets one month of training in one subject if and only if this student gets a valid training position for this subject in one month
    #
    counter = 0
    for stud in persons:
        counter = counter + 1
        print_progress_bar('c', 6, counter)
        for pp in stud_pp_list[stud]:
            for t_slot in range(max(StartDate_to_Timeslot(pp.start_date), 0), min(EndDate_to_Timeslot(pp.end_date)+1, amount_of_months)):    
                if t_slot not in stud_uz_list[stud]:
                    for h in hospitals:
                        if h.id in [aou.organisationsgruppe_id for aou in stud_pp_aou_list[stud, pp]]:
                            for dep in h_dep_list[h]:
                                for pt_block in h_dep_ptblock_list[h, dep]:
                                    if t_slot >= StartDate_to_Timeslot(pt_block.start_date):
                                        model.addConstr(quicksum(y[t_slot, stud.id, h.id, dep.id, pt_block.ausbildungsblock_id, t_pos.id] for t_pos in [tpos for tpos in h_dep_ptblock_tpos_list[h, dep, pt_block] if t_slot >= StartDate_to_Timeslot(tpos.start_date)])
                                                        <= quicksum(
                                                           quicksum(
                                                           quicksum(
                                                           quicksum(z[t_slot, stud.id, t_path.id, t_block.ausbildungsblock_id, subj.ausbildungserfordernis.id, c.ausbildungsinhalte.id] for c in [c2 for c2 in stud_tpath_tblock_subj_c_list[stud, t_path, t_block, subj] if c2.ausbildungsinhalte.max_duration - c2.month_completed > 0 and tags_fulfilled(stud, t_path, t_block, subj, c2, h, dep) and Areas_of_expertise_fulfilled(stud, t_path, t_block, subj, c2, h, dep, pt_block)])
                                                                                                                                              for subj in stud_tpath_tblock_subj_list[stud, t_path, t_block])
                                                                                                                                              for t_block in [tblock for tblock in stud_tpath_tblock_list[stud, t_path] if tblock.ausbildungsblock.ausbildungstyp in consideredausbildungstypen])
                                                                                                                                              for t_path in [tpath for tpath in stud_tpath_list[stud] if t_slot >= StartDate_to_Timeslot(tpath.start_date)]))
    print_end_notification('c', 6, True)
    counter = 0
    for stud in persons:
        counter = counter + 1
        print_progress_bar('c', 7, counter)
        for pp in stud_pp_list[stud]:
            for t_slot in range(max(StartDate_to_Timeslot(pp.start_date), 0), min(EndDate_to_Timeslot(pp.end_date)+1, amount_of_months)):    
                if t_slot not in stud_uz_list[stud]:
                    model.addConstr(quicksum(
                                    quicksum(
                                    quicksum(
                                    quicksum(z[t_slot, stud.id, t_path.id, t_block.ausbildungsblock_id, subj.ausbildungserfordernis.id, c.ausbildungsinhalte.id] for c in [c2 for c2 in stud_tpath_tblock_subj_c_list[stud, t_path, t_block, subj] if c2.ausbildungsinhalte.max_duration - c2.month_completed > 0])
                                                                                                                       for subj in stud_tpath_tblock_subj_list[stud, t_path, t_block])
                                                                                                                       for t_block in [tblock for tblock in stud_tpath_tblock_list[stud, t_path] if tblock.ausbildungsblock.ausbildungstyp in consideredausbildungstypen])
                                                                                                                       for t_path in [tpath for tpath in stud_tpath_list[stud] if t_slot >= StartDate_to_Timeslot(tpath.start_date)])
                                    <= quicksum(
                                       quicksum(
                                       quicksum(
                                       quicksum(y[t_slot, stud.id, h.id, dep.id, pt_block.ausbildungsblock_id, t_pos.id] for t_pos in [tpos for tpos in h_dep_ptblock_tpos_list[h, dep, pt_block] if t_slot >= StartDate_to_Timeslot(tpos.start_date)])
                                                                                                                         for pt_block in [ptblock for ptblock in h_dep_ptblock_list[h, dep] if t_slot >= StartDate_to_Timeslot(ptblock.start_date)])
                                                                                                                         for dep in h_dep_list[h])
                                                                                                                         for h in [hh for hh in hospitals if hh.id in [aou.organisationsgruppe_id for aou in stud_pp_aou_list[stud, pp]]]))
    print_end_notification('c', 7, True)

    # Every student needs to attend to contents of every subject a certain amount of months
    #
    counter = 0
    for stud in persons:
        counter = counter + 1
        print_progress_bar('c', 8, counter)
        for t_path in stud_tpath_list[stud]:
            for t_block in stud_tpath_tblock_list[stud, t_path]:
                if t_block.ausbildungsblock.ausbildungstyp in consideredausbildungstypen:
                    for subj in stud_tpath_tblock_subj_list[stud, t_path, t_block]:
                        subj_fulfilled = False
                        for max_c_lists in k_lists_from_n_list([cc for cc in stud_tpath_tblock_subj_c_list[stud, t_path, t_block, subj] if cc.month_completed >= cc.ausbildungsinhalte.min_duration], subj.ausbildungserfordernis.max_number_of_picks):
                            if subj.ausbildungserfordernis.duration <= sum(min(c.month_completed, c.ausbildungsinhalte.max_duration) for c in [max_c_lists[i] for i in range(subj.ausbildungserfordernis.max_number_of_picks)]):
                                subj_fulfilled = True
                        if not subj_fulfilled:    
                            model.addConstr(subj.ausbildungserfordernis.duration - quicksum(min(c.month_completed, c.ausbildungsinhalte.max_duration)*zc[stud.id, t_path.id, t_block.ausbildungsblock_id, subj.ausbildungserfordernis.id, c.ausbildungsinhalte.id] for c in stud_tpath_tblock_subj_c_list[stud, t_path, t_block, subj])
                                            == quicksum(z[stud.id, t_path.id, t_block.ausbildungsblock_id, subj.ausbildungserfordernis.id] for not_strict in [n_strict for n_strict in range(1) if 'z' not in strict_var])
                                            +  quicksum(
                                               quicksum(z[t_slot, stud.id, t_path.id, t_block.ausbildungsblock_id, subj.ausbildungserfordernis.id, c.ausbildungsinhalte.id] for c in [c2 for c2 in stud_tpath_tblock_subj_c_list[stud, t_path, t_block, subj] if c2.ausbildungsinhalte.max_duration - c2.month_completed > 0])
                                                                                                                                                                            for t_slot in [tslot for pp in stud_pp_list[stud] for tslot in range(max(StartDate_to_Timeslot(pp.start_date), 0), min(EndDate_to_Timeslot(pp.end_date)+1, amount_of_months))
                                                                                                                                                                                                 if  tslot not in stud_uz_list[stud]
                                                                                                                                                                                                 and tslot >= StartDate_to_Timeslot(t_path.start_date)]))
                        else:
                            model.addConstr(subj.ausbildungserfordernis.duration <= quicksum(min(c.month_completed, c.ausbildungsinhalte.max_duration)*zc[stud.id, t_path.id, t_block.ausbildungsblock_id, subj.ausbildungserfordernis.id, c.ausbildungsinhalte.id] for c in stud_tpath_tblock_subj_c_list[stud, t_path, t_block, subj]))
                            model.addConstr(0 == quicksum(
                                                 quicksum(z[t_slot, stud.id, t_path.id, t_block.ausbildungsblock_id, subj.ausbildungserfordernis.id, c.ausbildungsinhalte.id] for c in [c2 for c2 in stud_tpath_tblock_subj_c_list[stud, t_path, t_block, subj] if c2.ausbildungsinhalte.max_duration - c2.month_completed > 0])
                                                                                                                                                                              for t_slot in [tslot for pp in stud_pp_list[stud] for tslot in range(max(StartDate_to_Timeslot(pp.start_date), 0), min(EndDate_to_Timeslot(pp.end_date)+1, amount_of_months))
                                                                                                                                                                                                   if  tslot not in stud_uz_list[stud]
                                                                                                                                                                                                   and tslot >= StartDate_to_Timeslot(t_path.start_date)]))
    print_end_notification('c', 8, True)

    # Every student has to pass a minimal amount and a maximal amount of different contents for every subject
    #
    counter = 0
    for stud in persons:
        counter = counter + 1
        print_progress_bar('c', 9, counter)
        for t_path in stud_tpath_list[stud]:
            for t_block in stud_tpath_tblock_list[stud, t_path]:
                if t_block.ausbildungsblock.ausbildungstyp in consideredausbildungstypen:
                    for subj in stud_tpath_tblock_subj_list[stud, t_path, t_block]:
                        model.addConstr(subj.ausbildungserfordernis.min_number_of_picks <= quicksum(zc[stud.id, t_path.id, t_block.ausbildungsblock_id, subj.ausbildungserfordernis.id, c.ausbildungsinhalte.id] for c in stud_tpath_tblock_subj_c_list[stud, t_path, t_block, subj]))
                        model.addConstr(subj.ausbildungserfordernis.max_number_of_picks >= quicksum(zc[stud.id, t_path.id, t_block.ausbildungsblock_id, subj.ausbildungserfordernis.id, c.ausbildungsinhalte.id] for c in stud_tpath_tblock_subj_c_list[stud, t_path, t_block, subj]))
    print_end_notification('c', 9, True)

    # Every student needs to pass a minimal amount and maximal amount of months of every chosen content for every subject
    #
    counter = 0
    for stud in persons:
        counter = counter + 1
        print_progress_bar('c', 10, counter)
        for t_path in stud_tpath_list[stud]:
            for t_block in stud_tpath_tblock_list[stud, t_path]:
                if t_block.ausbildungsblock.ausbildungstyp in consideredausbildungstypen:
                    for subj in stud_tpath_tblock_subj_list[stud, t_path, t_block]:
                        for c in stud_tpath_tblock_subj_c_list[stud, t_path, t_block, subj]:
                            if c.ausbildungsinhalte.max_duration - c.month_completed > 0:
                                if c.ausbildungsinhalte.min_duration - c.month_completed > 0:
                                    model.addConstr((c.ausbildungsinhalte.min_duration - c.month_completed) * zc[stud.id, t_path.id, t_block.ausbildungsblock_id, subj.ausbildungserfordernis.id, c.ausbildungsinhalte.id]
                                                    <= quicksum(z[t_slot, stud.id, t_path.id, t_block.ausbildungsblock_id, subj.ausbildungserfordernis.id, c.ausbildungsinhalte.id] for t_slot in [tslot for pp in stud_pp_list[stud] for tslot in range(max(StartDate_to_Timeslot(pp.start_date), 0), min(EndDate_to_Timeslot(pp.end_date)+1, amount_of_months)) if tslot not in stud_uz_list[stud] and tslot >= StartDate_to_Timeslot(t_path.start_date)])
                                                    +  quicksum(z['-1', stud.id, t_path.id, t_block.ausbildungsblock_id, subj.ausbildungserfordernis.id, c.ausbildungsinhalte.id] for not_strict in [n_strict for n_strict in range(1) if 'z' not in strict_var]))
                                model.addConstr((c.ausbildungsinhalte.max_duration - c.month_completed) * zc[stud.id, t_path.id, t_block.ausbildungsblock_id, subj.ausbildungserfordernis.id, c.ausbildungsinhalte.id]
                                                >= quicksum(z[t_slot, stud.id, t_path.id, t_block.ausbildungsblock_id, subj.ausbildungserfordernis.id, c.ausbildungsinhalte.id] for t_slot in [tslot for pp in stud_pp_list[stud] for tslot in range(max(StartDate_to_Timeslot(pp.start_date), 0), min(EndDate_to_Timeslot(pp.end_date)+1, amount_of_months)) if tslot not in stud_uz_list[stud] and tslot >= StartDate_to_Timeslot(t_path.start_date)])
                                                -  quicksum(z['+1', stud.id, t_path.id, t_block.ausbildungsblock_id, subj.ausbildungserfordernis.id, c.ausbildungsinhalte.id] for not_strict in [n_strict for n_strict in range(1) if 'z' not in strict_var]))
    print_end_notification('c', 10, True)

    # Every subject has to be finished in the planning horizon
    #
    counter = 0
    for stud in persons:
        counter = counter + 1
        print_progress_bar('c', 11, counter)
        for t_path in stud_tpath_list[stud]:
            for t_block in stud_tpath_tblock_list[stud, t_path]:
                if t_block.ausbildungsblock.ausbildungstyp in consideredausbildungstypen:
                    model.addConstr(1 == quicksum(zsf[t_slot, stud.id, t_path.id, t_block.ausbildungsblock_id] for t_slot in range(-1, amount_of_months)))
    print_end_notification('c', 11, True)

    # Every student does not have to be assigned to an training position after finishing all subjects
    #
    counter = 0
    for stud in persons:
        counter = counter + 1
        print_progress_bar('c', 12, counter)
        for pp in stud_pp_list[stud]:
            for t_slot in range(max(StartDate_to_Timeslot(pp.start_date), 0), min(EndDate_to_Timeslot(pp.end_date)+1, amount_of_months)):
                if t_slot not in stud_uz_list[stud]:
                    for t_path in stud_tpath_list[stud]:
                        for t_block in stud_tpath_tblock_list[stud, t_path]:
                            if t_block.ausbildungsblock.ausbildungstyp in consideredausbildungstypen:
                                model.addConstr(y[t_slot, stud.id, 1] <= quicksum(zsf[tslot, stud.id, t_path.id, t_block.ausbildungsblock_id] for tslot in range(-1, t_slot)))
    print_end_notification('c', 12, True)

    # A subject is finished in a month if and only if the last content of the subject is done in this month
    #
    counter = 0
    for stud in persons:
        counter = counter + 1
        print_progress_bar('c', 13, counter)
        for pp in stud_pp_list[stud]:
            for t_slot in range(max(StartDate_to_Timeslot(pp.start_date), 1), min(EndDate_to_Timeslot(pp.end_date)+1, amount_of_months)):    
                if t_slot not in stud_uz_list[stud]:
                    for t_path in stud_tpath_list[stud]:
                        if t_slot >= StartDate_to_Timeslot(t_path.start_date):
                            for t_block in stud_tpath_tblock_list[stud, t_path]:
                                if t_block.ausbildungsblock.ausbildungstyp in consideredausbildungstypen:
                                    for subj in stud_tpath_tblock_subj_list[stud, t_path, t_block]:
                                        for c in stud_tpath_tblock_subj_c_list[stud, t_path, t_block, subj]:
                                            if c.ausbildungsinhalte.max_duration - c.month_completed > 0:
                                                model.addConstr(z[t_slot, stud.id, t_path.id, t_block.ausbildungsblock_id, subj.ausbildungserfordernis.id, c.ausbildungsinhalte.id]
                                                                <= 1 - quicksum(zsf[tslot, stud.id, t_path.id, t_block.ausbildungsblock_id] for tslot in range(-1, t_slot)))
    print_end_notification('c', 13, True)

    # The sections have to be finished in the respective order
    #
    counter = 0
    for stud in persons:
        counter = counter + 1
        print_progress_bar('c', 14, counter)
        for pp in stud_pp_list[stud]:
            for t_slot in range(max(StartDate_to_Timeslot(pp.start_date), 0), min(EndDate_to_Timeslot(pp.end_date)+1, amount_of_months)):    
                if t_slot not in stud_uz_list[stud]:
                    for t_path in stud_tpath_list[stud]:
                        if t_slot >= StartDate_to_Timeslot(t_path.start_date):
                            for t_block in stud_tpath_tblock_list[stud, t_path]:
                                if t_block.ausbildungsblock.ausbildungstyp in consideredausbildungstypen:
                                    for cs in consecutive_sections:
                                        if t_block.ausbildungsblock.ausbildungstyp == cs[1] and len([subject for tblock in stud_tpath_tblock_list[stud, t_path] for subject in stud_tpath_tblock_subj_list[stud, t_path, tblock] if tblock.ausbildungsblock.ausbildungstyp == cs[0]]) > 0:
                                            for subj in stud_tpath_tblock_subj_list[stud, t_path, t_block]:
                                                for c in stud_tpath_tblock_subj_c_list[stud, t_path, t_block, subj]:
                                                    if c.ausbildungsinhalte.max_duration - c.month_completed > 0:
                                                        model.addConstr(z[t_slot, stud.id, t_path.id, t_block.ausbildungsblock_id, subj.ausbildungserfordernis.id, c.ausbildungsinhalte.id]
                                                                        <= quicksum(zsf[tslot, stud.id, t_path.id, training_type_to_id(t_path, cs[0])] for tslot in range(-1, t_slot)))
    print_end_notification('c', 14, True)

    # Constraints for the approximation of the variance of the violated preferences of all students
    #
    if vvp != {}:
        counter = 0
        for stud in persons:
            counter = counter + 1
            print_progress_bar('c', 15, counter)
            model.addConstr(adtm_vp[stud.id] >= quicksum(
                                                quicksum(
                                                quicksum(
                                                quicksum((stud_ogp_of_h[stud, h] - min([ogp.priority for ogp in stud_ogp_list[stud]]))*x[t_slot, stud.id, h.id, str(h.id), d_pos.id] for d_pos in [dpos for dpos in h_dpos_list[h] if  pps.occupational_group.id in [og.occupational_group.id for og in h_dpos_og_list[h, dpos]]
                                                                                                                                                                                                                                   and t_slot >= StartDate_to_Timeslot(dpos.start_date)
                                                                                                                                                                                                                                   and t_slot <= EndDate_to_Timeslot(dpos.end_date)])
                                                                                                                                                                                     for h in [h2 for h2 in hospitals if  h2.id in [aou.organisationsgruppe_id for aou in stud_pp_aou_list[stud, pps]]
                                                                                                                                                                                                                      and (stud_ogp_of_h[stud, h2] - min([ogp.priority for ogp in stud_ogp_list[stud]])) > 0]) 
                                                                                                                                                                                     for t_slot in [tslot for tslot in range(max(StartDate_to_Timeslot(pps.start_date), 0), min(EndDate_to_Timeslot(pps.end_date)+1, amount_of_months)) if tslot not in stud_uz_list[stud]])
                                                                                                                                                                                     for pps in stud_pp_list[stud])
                                             +  quicksum(
                                                quicksum(
                                                quicksum(
                                                quicksum(
                                                quicksum((stud_ogp_of_h[stud, h] - min([ogp.priority for ogp in stud_ogp_list[stud]]))*x[t_slot, stud.id, h.id, dep.id, d_pos.id] for d_pos in [dpos for dpos in h_dep_dpos_list[h, dep] if  pps.occupational_group.id in [og.occupational_group.id for og in h_dep_dpos_og_list[h, dep, dpos]]
                                                                                                                                                                                                                                         and t_slot >= StartDate_to_Timeslot(dpos.start_date)
                                                                                                                                                                                                                                         and t_slot <= EndDate_to_Timeslot(dpos.end_date)])
                                                                                                                                                                                  for dep in h_dep_list[h])
                                                                                                                                                                                  for h in [h2 for h2 in hospitals if  h2.id in [aou.organisationsgruppe_id for aou in stud_pp_aou_list[stud, pps]] 
                                                                                                                                                                                                                   and (stud_ogp_of_h[stud, h2] - min([ogp.priority for ogp in stud_ogp_list[stud]])) > 0]) 
                                                                                                                                                                                  for t_slot in [tslot for tslot in range(max(StartDate_to_Timeslot(pps.start_date), 0), min(EndDate_to_Timeslot(pps.end_date)+1, amount_of_months)) if tslot not in stud_uz_list[stud]])
                                                                                                                                                                                  for pps in stud_pp_list[stud])
                                             -  (1/num_stud)*quicksum(
                                                             quicksum(
                                                             quicksum(
                                                             quicksum(
                                                             quicksum((stud_ogp_of_h[stud2, h] - min([ogp.priority for ogp in stud_ogp_list[stud2]]))*x[t_slot, stud2.id, h.id, str(h.id), d_pos.id] for d_pos in [dpos for dpos in h_dpos_list[h] if  pps.occupational_group.id in [og.occupational_group.id for og in h_dpos_og_list[h, dpos]]
                                                                                                                                                                                                                                                   and t_slot >= StartDate_to_Timeslot(dpos.start_date)
                                                                                                                                                                                                                                                   and t_slot <= EndDate_to_Timeslot(dpos.end_date)])
                                                                                                                                                                                                     for h in [h2 for h2 in hospitals if  h2.id in [aou.organisationsgruppe_id for aou in stud_pp_aou_list[stud2, pps]] 
                                                                                                                                                                                                                                      and (stud_ogp_of_h[stud2, h2] - min([ogp.priority for ogp in stud_ogp_list[stud2]])) > 0]) 
                                                                                                                                                                                                     for t_slot in [tslot for tslot in range(max(StartDate_to_Timeslot(pps.start_date), 0), min(EndDate_to_Timeslot(pps.end_date)+1, amount_of_months)) if tslot not in stud_uz_list[stud2]])
                                                                                                                                                                                                     for pps in stud_pp_list[stud2])
                                                                                                                                                                                                     for stud2 in persons)
                                             -  (1/num_stud)*quicksum(
                                                             quicksum(
                                                             quicksum(
                                                             quicksum(
                                                             quicksum(
                                                             quicksum((stud_ogp_of_h[stud2, h] - min([ogp.priority for ogp in stud_ogp_list[stud2]]))*x[t_slot, stud2.id, h.id, dep.id, d_pos.id] for d_pos in [dpos for dpos in h_dep_dpos_list[h, dep] if  pps.occupational_group.id in [og.occupational_group.id for og in h_dep_dpos_og_list[h, dep, dpos]]
                                                                                                                                                                                                                                                         and t_slot >= StartDate_to_Timeslot(dpos.start_date)
                                                                                                                                                                                                                                                         and t_slot <= EndDate_to_Timeslot(dpos.end_date)])
                                                                                                                                                                                                  for dep in h_dep_list[h])
                                                                                                                                                                                                  for h in [h2 for h2 in hospitals if  h2.id in [aou.organisationsgruppe_id for aou in stud_pp_aou_list[stud2, pps]] 
                                                                                                                                                                                                                                   and (stud_ogp_of_h[stud2, h2] - min([ogp.priority for ogp in stud_ogp_list[stud2]])) > 0]) 
                                                                                                                                                                                                  for t_slot in [tslot for tslot in range(max(StartDate_to_Timeslot(pps.start_date), 0), min(EndDate_to_Timeslot(pps.end_date)+1, amount_of_months)) if tslot not in stud_uz_list[stud2]])
                                                                                                                                                                                                  for pps in stud_pp_list[stud2])
                                                                                                                                                                                                  for stud2 in persons))
            model.addConstr(adtm_vp[stud.id] >= (1/num_stud)*quicksum(
                                                             quicksum(
                                                             quicksum(
                                                             quicksum(
                                                             quicksum((stud_ogp_of_h[stud2, h] - min([ogp.priority for ogp in stud_ogp_list[stud2]]))*x[t_slot, stud2.id, h.id, str(h.id), d_pos.id] for d_pos in [dpos for dpos in h_dpos_list[h] if  pps.occupational_group.id in [og.occupational_group.id for og in h_dpos_og_list[h, dpos]]
                                                                                                                                                                                                                                                   and t_slot >= StartDate_to_Timeslot(dpos.start_date)
                                                                                                                                                                                                                                                   and t_slot <= EndDate_to_Timeslot(dpos.end_date)])
                                                                                                                                                                                                     for h in [h2 for h2 in hospitals if  h2.id in [aou.organisationsgruppe_id for aou in stud_pp_aou_list[stud2, pps]] 
                                                                                                                                                                                                                                      and (stud_ogp_of_h[stud2, h2] - min([ogp.priority for ogp in stud_ogp_list[stud2]])) > 0]) 
                                                                                                                                                                                                     for t_slot in [tslot for tslot in range(max(StartDate_to_Timeslot(pps.start_date), 0), min(EndDate_to_Timeslot(pps.end_date)+1, amount_of_months)) if tslot not in stud_uz_list[stud2]])
                                                                                                                                                                                                     for pps in stud_pp_list[stud2])
                                                                                                                                                                                                     for stud2 in persons)
                                             +  (1/num_stud)*quicksum(
                                                             quicksum(
                                                             quicksum(
                                                             quicksum(
                                                             quicksum(
                                                             quicksum((stud_ogp_of_h[stud2, h] - min([ogp.priority for ogp in stud_ogp_list[stud2]]))*x[t_slot, stud2.id, h.id, dep.id, d_pos.id] for d_pos in [dpos for dpos in h_dep_dpos_list[h, dep] if  pps.occupational_group.id in [og.occupational_group.id for og in h_dep_dpos_og_list[h, dep, dpos]]
                                                                                                                                                                                                                                                         and t_slot >= StartDate_to_Timeslot(dpos.start_date)
                                                                                                                                                                                                                                                         and t_slot <= EndDate_to_Timeslot(dpos.end_date)])
                                                                                                                                                                                                  for dep in h_dep_list[h])
                                                                                                                                                                                                  for h in [h2 for h2 in hospitals if  h2.id in [aou.organisationsgruppe_id for aou in stud_pp_aou_list[stud2, pps]] 
                                                                                                                                                                                                                                   and (stud_ogp_of_h[stud2, h2] - min([ogp.priority for ogp in stud_ogp_list[stud2]])) > 0]) 
                                                                                                                                                                                                  for t_slot in [tslot for tslot in range(max(StartDate_to_Timeslot(pps.start_date), 0), min(EndDate_to_Timeslot(pps.end_date)+1, amount_of_months)) if tslot not in stud_uz_list[stud2]])
                                                                                                                                                                                                  for pps in stud_pp_list[stud2])
                                                                                                                                                                                                  for stud2 in persons)
                                             -  quicksum(
                                                quicksum(
                                                quicksum(
                                                quicksum((stud_ogp_of_h[stud, h] - min([ogp.priority for ogp in stud_ogp_list[stud]]))*x[t_slot, stud.id, h.id, str(h.id), d_pos.id] for d_pos in [dpos for dpos in h_dpos_list[h] if  pps.occupational_group.id in [og.occupational_group.id for og in h_dpos_og_list[h, dpos]]
                                                                                                                                                                                                                                   and t_slot >= StartDate_to_Timeslot(dpos.start_date)
                                                                                                                                                                                                                                   and t_slot <= EndDate_to_Timeslot(dpos.end_date)])
                                                                                                                                                                                     for h in [h2 for h2 in hospitals if  h2.id in [aou.organisationsgruppe_id for aou in stud_pp_aou_list[stud, pps]] 
                                                                                                                                                                                                                      and (stud_ogp_of_h[stud, h2] - min([ogp.priority for ogp in stud_ogp_list[stud]])) > 0]) 
                                                                                                                                                                                     for t_slot in [tslot for tslot in range(max(StartDate_to_Timeslot(pps.start_date), 0), min(EndDate_to_Timeslot(pps.end_date)+1, amount_of_months)) if tslot not in stud_uz_list[stud]])
                                                                                                                                                                                     for pps in stud_pp_list[stud])
                                             -  quicksum(
                                                quicksum(
                                                quicksum(
                                                quicksum(
                                                quicksum((stud_ogp_of_h[stud, h] - min([ogp.priority for ogp in stud_ogp_list[stud]]))*x[t_slot, stud.id, h.id, dep.id, d_pos.id] for d_pos in [dpos for dpos in h_dep_dpos_list[h, dep] if  pps.occupational_group.id in [og.occupational_group.id for og in h_dep_dpos_og_list[h, dep, dpos]]
                                                                                                                                                                                                                                         and t_slot >= StartDate_to_Timeslot(dpos.start_date)
                                                                                                                                                                                                                                         and t_slot <= EndDate_to_Timeslot(dpos.end_date)]) 
                                                                                                                                                                                  for dep in h_dep_list[h])
                                                                                                                                                                                  for h in [h2 for h2 in hospitals if  h2.id in [aou.organisationsgruppe_id for aou in stud_pp_aou_list[stud, pps]] 
                                                                                                                                                                                                                   and (stud_ogp_of_h[stud, h2] - min([ogp.priority for ogp in stud_ogp_list[stud]])) > 0]) 
                                                                                                                                                                                  for t_slot in [tslot for tslot in range(max(StartDate_to_Timeslot(pps.start_date), 0), min(EndDate_to_Timeslot(pps.end_date)+1, amount_of_months)) if tslot not in stud_uz_list[stud]])
                                                                                                                                                                                  for pps in stud_pp_list[stud]))
            model.addConstr(quicksum((1/(2*t_slot+1))*qdtm_vp[t_slot, stud.id] for t_slot in range(amount_of_months)) >= adtm_vp[stud.id])
        model.addConstr(vvp[0] >= (12/(num_stud*amount_of_months))*quicksum(
                                                                   quicksum(qdtm_vp[t_slot, stud.id] for t_slot in range(amount_of_months))
                                                                                                     for stud in persons))
    print_end_notification('c', 15, vvp != {})

    # Constraints for the approximation of the variance of the months without training of all students
    #
    if vmwt != {}:
        counter = 0
        for stud in persons:
            counter = counter + 1
            print_progress_bar('c', 16, counter)
            model.addConstr(adtm_mwt[stud.id] >= quicksum((y[t_slot, stud.id,0] - y[t_slot, stud.id,1]) for t_slot in [tslot for pps in stud_pp_list[stud] for tslot in range(max(StartDate_to_Timeslot(pps.start_date), 0), min(EndDate_to_Timeslot(pps.end_date)+1, amount_of_months)) if tslot not in stud_uz_list[stud]])
                                              -  (1/num_stud)*quicksum(
                                                              quicksum((y[t_slot2, stud2.id,0] - y[t_slot2, stud2.id,1]) for t_slot2 in [tslot for pps in stud_pp_list[stud2] for tslot in range(max(StartDate_to_Timeslot(pps.start_date), 0), min(EndDate_to_Timeslot(pps.end_date)+1, amount_of_months)) if tslot not in stud_uz_list[stud2]]) 
                                                                                                                         for stud2 in persons))            
            model.addConstr(adtm_mwt[stud.id] >= (1/num_stud)*quicksum(
                                                              quicksum((y[t_slot2, stud2.id,0] - y[t_slot2, stud2.id,1]) for t_slot2 in [tslot for pps in stud_pp_list[stud2] for tslot in range(max(StartDate_to_Timeslot(pps.start_date), 0), min(EndDate_to_Timeslot(pps.end_date)+1, amount_of_months)) if tslot not in stud_uz_list[stud2]]) 
                                                                                                                         for stud2 in persons)
                                              -  quicksum((y[t_slot, stud.id,0] - y[t_slot, stud.id,1]) for t_slot in [tslot for pps in stud_pp_list[stud] for tslot in range(max(StartDate_to_Timeslot(pps.start_date), 0), min(EndDate_to_Timeslot(pps.end_date)+1, amount_of_months)) if tslot not in stud_uz_list[stud]]))
            model.addConstr(quicksum((1/(2*t_slot+1))*qdtm_mwt[t_slot, stud.id] for t_slot in range(amount_of_months)) >= adtm_mwt[stud.id])        
        model.addConstr(vmwt[0] >= (12/(num_stud*amount_of_months))*quicksum(
                                                                    quicksum(qdtm_mwt[t_slot, stud.id] for t_slot in range(amount_of_months))
                                                                                                       for stud in persons))
    print_end_notification('c', 16, vmwt != {})

    # Constraints for the approximation of the variance of the weighted months without training of all students
    #
    if vwmwt != {}:
        counter = 0
        for stud in [stud for stud in persons if (stud_duration[stud] - stud_month_completed[stud]) > 0.5]:
            counter = counter + 1
            print_progress_bar('c', 17, counter)
            model.addConstr(adtm_wmwt[stud.id] >= quicksum((y[t_slot, stud.id,0] - y[t_slot, stud.id,1]) for t_slot in [tslot for pps in stud_pp_list[stud] for tslot in range(max(StartDate_to_Timeslot(pps.start_date), 0), min(EndDate_to_Timeslot(pps.end_date)+1, amount_of_months)) if tslot not in stud_uz_list[stud]])
                                               -  (1/num_stud)*quicksum(
                                                               quicksum((y[t_slot2, stud2.id,0] - y[t_slot2, stud2.id,1]) for t_slot2 in [tslot for pps in stud_pp_list[stud2] for tslot in range(max(StartDate_to_Timeslot(pps.start_date), 0), min(EndDate_to_Timeslot(pps.end_date)+1, amount_of_months)) if tslot not in stud_uz_list[stud2]]) 
                                                                                                                          for stud2 in [stud3 for stud3 in persons if (stud_duration[stud3] - stud_month_completed[stud3]) > 0.5]))            
            model.addConstr(adtm_wmwt[stud.id] >= (1/num_stud)*quicksum(
                                                               quicksum((y[t_slot2, stud2.id,0] - y[t_slot2, stud2.id,1]) for t_slot2 in [tslot for pps in stud_pp_list[stud2] for tslot in range(max(StartDate_to_Timeslot(pps.start_date), 0), min(EndDate_to_Timeslot(pps.end_date)+1, amount_of_months)) if tslot not in stud_uz_list[stud2]]) 
                                                                                                                          for stud2 in [stud3 for stud3 in persons if (stud_duration[stud3] - stud_month_completed[stud3]) > 0.5])
                                               -  quicksum((y[t_slot, stud.id,0] - y[t_slot, stud.id,1]) for t_slot in [tslot for pps in stud_pp_list[stud] for tslot in range(max(StartDate_to_Timeslot(pps.start_date), 0), min(EndDate_to_Timeslot(pps.end_date)+1, amount_of_months)) if tslot not in stud_uz_list[stud]]))
            model.addConstr(quicksum((1/(2*t_slot+1))*qdtm_wmwt[t_slot, stud.id] for t_slot in range(amount_of_months)) >= adtm_wmwt[stud.id])        
        model.addConstr(vwmwt[0] >= (1/num_stud)*quicksum(
                                                 quicksum((1/(stud_duration[stud] - stud_month_completed[stud]))*qdtm_wmwt[t_slot, stud.id] for t_slot in range(amount_of_months))
                                                                                                                                            for stud in [stud for stud in persons if (stud_duration[stud] - stud_month_completed[stud]) > 0.5]))
    print_end_notification('c', 17, vwmwt != {})

    # Every consecutive month without training has to get tracked to minimize the amount of such occurrences
    #
    if cmwt != {}:
        counter = 0
        for stud in persons:
            counter = counter + 1
            print_progress_bar('c', 18, counter)
            for pp in stud_pp_list[stud]:
                for t_slot in range(max(StartDate_to_Timeslot(pp.start_date), 0), min(EndDate_to_Timeslot(pp.end_date)+1, amount_of_months)):
                    if t_slot not in stud_uz_list[stud]:
                        if t_slot == 0:
                            if len([aa for aa in allocations if aa.person_id == stud.id]) > 0:
                                model.addConstr(cmwt[t_slot, stud.id] >= y[t_slot, stud.id, 0] - y[t_slot, stud.id, 1])
                        else:
                            if t_slot-1 in [tslot for ppp in stud_pp_list[stud] for tslot in range(max(StartDate_to_Timeslot(ppp.start_date), 0), min(EndDate_to_Timeslot(ppp.end_date)+1, amount_of_months)) if tslot not in stud_uz_list[stud]]:
                                model.addConstr(1 + cmwt[t_slot, stud.id] >= y[t_slot-1, stud.id, 0] - y[t_slot-1, stud.id, 1] + y[t_slot, stud.id, 0] - y[t_slot, stud.id, 1])
    print_end_notification('c', 18, cmwt != {})

    # Every department without any training in a month has to get tracked to minimize the amount of such occurrences
    #
    if dwt != {}:
        counter = 0
        for t_slot in range(amount_of_months):
            counter = counter + 1
            print_progress_bar('c', 19, counter, 0, 0, amount_of_months)
            for h in hospitals:
                for dep in h_dep_list[h]:
                    model.addConstr(1 - dwt[t_slot, h.id, dep.id] <= quicksum(
                                                                     quicksum(
                                                                     quicksum(y[t_slot, stud.id, h.id, dep.id, pt_block.ausbildungsblock_id, t_pos.id] for t_pos in [tpos for tpos in h_dep_ptblock_tpos_list[h, dep, pt_block] if t_slot >= StartDate_to_Timeslot(tpos.start_date)])
                                                                                                                                                       for pt_block in [ptblock for ptblock in h_dep_ptblock_list[h, dep] if t_slot >= StartDate_to_Timeslot(ptblock.start_date)])
                                                                                                                                                       for stud in [stud for stud in persons for pp in stud_pp_list[stud] if  t_slot >= StartDate_to_Timeslot(pp.start_date)
                                                                                                                                                                                                                          and t_slot <= EndDate_to_Timeslot(pp.end_date)
                                                                                                                                                                                                                          and t_slot not in stud_uz_list[stud]
                                                                                                                                                                                                                          and h.id in [aou.organisationsgruppe_id for aou in stud_pp_aou_list[stud, pp]]]))
    print_end_notification('c', 19, dwt != {}, 0, 0, amount_of_months)

    # Every hospital change has to get tracked to minimize the amount of hospital changes
    #
    if hc != {}:
        counter = 0
        for stud in persons:
            counter = counter + 1
            print_progress_bar('c', 20, counter)
            for pp in stud_pp_list[stud]:
                for t_slot in range(max(StartDate_to_Timeslot(pp.start_date), 0), min(EndDate_to_Timeslot(pp.end_date)+1, amount_of_months)):
                    if t_slot not in stud_uz_list[stud]:
                        if t_slot == 0:
                            for a in allocations:
                                if a.person_id == stud.id:
                                    for h in hospitals:
                                        if h.id in [aou.organisationsgruppe_id for aou in stud_pp_aou_list[stud, pp]] and h.id != a.organisationsgruppe_id:
                                            model.addConstr(hc[t_slot, stud.id] >= quicksum(x[t_slot, stud.id, h.id, str(h.id), d_pos.id] for d_pos in [dpos for dpos in h_dpos_list[h] if  t_slot >= StartDate_to_Timeslot(dpos.start_date)
                                                                                                                                                                                        and t_slot <= EndDate_to_Timeslot(dpos.end_date)
                                                                                                                                                                                        and pp.occupational_group.id in [og.occupational_group.id for og in h_dpos_og_list[h, dpos]]])
                                                                                +  quicksum(
                                                                                   quicksum(x[t_slot, stud.id, h.id, dep.id, d_pos.id] for d_pos in [dpos for dpos in h_dep_dpos_list[h, dep] if  t_slot >= StartDate_to_Timeslot(dpos.start_date)
                                                                                                                                                                                              and t_slot <= EndDate_to_Timeslot(dpos.end_date)
                                                                                                                                                                                              and pp.occupational_group.id in [og.occupational_group.id for og in h_dep_dpos_og_list[h, dep, dpos]]])
                                                                                                                                       for dep in h_dep_list[h]))
                        else:
                            if t_slot == StartDate_to_Timeslot(pp.start_date):
                                for pp2 in stud_pp_list[stud]:
                                    for t_slot2 in max_list([tslot2 for tslot2 in range(t_slot) if tslot2 >= StartDate_to_Timeslot(pp2.start_date) and tslot2 <= EndDate_to_Timeslot(pp2.end_date) and tslot2 not in stud_uz_list[stud]]):
                                        for h in hospitals:
                                            if h.id in [aou.organisationsgruppe_id for aou in stud_pp_aou_list[stud, pp2]]:
                                                model.addConstr(1 + hc[t_slot, stud.id] >= quicksum(x[t_slot2, stud.id, h.id, str(h.id), d_pos.id] for d_pos in [dpos for dpos in h_dpos_list[h] if  t_slot2 >= StartDate_to_Timeslot(dpos.start_date) 
                                                                                                                                                                                                 and t_slot2 <= EndDate_to_Timeslot(dpos.end_date)
                                                                                                                                                                                                 and pp2.occupational_group.id in [og.occupational_group.id for og in h_dpos_og_list[h, dpos]]])
                                                                                           +  quicksum(
                                                                                              quicksum(x[t_slot2, stud.id, h.id, dep.id, d_pos.id] for d_pos in [dpos for dpos in h_dep_dpos_list[h, dep] if  t_slot2 >= StartDate_to_Timeslot(dpos.start_date)
                                                                                                                                                                                                          and t_slot2 <= EndDate_to_Timeslot(dpos.end_date)
                                                                                                                                                                                                          and pp2.occupational_group.id in [og.occupational_group.id for og in h_dep_dpos_og_list[h, dep, dpos]]])
                                                                                                                                                   for dep in h_dep_list[h])
                                                                                           +  quicksum(
                                                                                              quicksum(x[t_slot, stud.id, hh.id, str(hh.id), d_pos.id] for d_pos in [dpos for dpos in h_dpos_list[hh] if  t_slot >= StartDate_to_Timeslot(dpos.start_date)
                                                                                                                                                                                                      and t_slot <= EndDate_to_Timeslot(dpos.end_date)
                                                                                                                                                                                                      and pp.occupational_group.id in [og.occupational_group.id for og in h_dpos_og_list[hh, dpos]]])
                                                                                           +  quicksum(
                                                                                              quicksum(x[t_slot, stud.id, hh.id, dep.id, d_pos.id] for d_pos in [dpos for dpos in h_dep_dpos_list[hh, dep] if  t_slot >= StartDate_to_Timeslot(dpos.start_date)
                                                                                                                                                                                                           and t_slot <= EndDate_to_Timeslot(dpos.end_date)
                                                                                                                                                                                                           and pp.occupational_group.id in [og.occupational_group.id for og in h_dep_dpos_og_list[hh, dep, dpos]]])
                                                                                                                                                   for dep in h_dep_list[hh])
                                                                                                                                                   for hh in [hos for hos in hospitals if  hos.id in [aou.organisationsgruppe_id for aou in stud_pp_aou_list[stud, pp]]
                                                                                                                                                                                       and hos.id != h.id]))    
                            else:    
                                if len(stud_pp_aou_list[stud, pp]) > 1:
                                    for t_slot2 in max_list([tslot2 for tslot2 in range(t_slot) for pp2 in stud_pp_list[stud] if tslot2 >= StartDate_to_Timeslot(pp2.start_date) and tslot2 <= EndDate_to_Timeslot(pp2.end_date) and tslot2 not in stud_uz_list[stud]]):
                                        for h in hospitals:
                                            if h.id in [aou.organisationsgruppe_id for aou in stud_pp_aou_list[stud, pp]]:
                                                model.addConstr(1 + hc[t_slot, stud.id] >= quicksum(x[t_slot2, stud.id, h.id, str(h.id), d_pos.id] for d_pos in [dpos for dpos in h_dpos_list[h] if  t_slot2 >= StartDate_to_Timeslot(dpos.start_date)
                                                                                                                                                                                                 and t_slot2 <= EndDate_to_Timeslot(dpos.end_date)
                                                                                                                                                                                                 and pp.occupational_group.id in [og.occupational_group.id for og in h_dpos_og_list[h, dpos]]])
                                                                                        +  quicksum(
                                                                                           quicksum(x[t_slot2, stud.id, h.id, dep.id, d_pos.id] for d_pos in [dpos for dpos in h_dep_dpos_list[h, dep] if  t_slot2 >= StartDate_to_Timeslot(dpos.start_date)
                                                                                                                                                                                                       and t_slot2 <= EndDate_to_Timeslot(dpos.end_date)
                                                                                                                                                                                                       and pp.occupational_group.id in [og.occupational_group.id for og in h_dep_dpos_og_list[h, dep, dpos]]])
                                                                                                                                                for dep in h_dep_list[h])
                                                                                        +  quicksum(
                                                                                           quicksum(x[t_slot, stud.id, hh.id, str(hh.id), d_pos.id] for d_pos in [dpos for dpos in h_dpos_list[hh] if  t_slot >= StartDate_to_Timeslot(dpos.start_date)
                                                                                                                                                                                                   and t_slot <= EndDate_to_Timeslot(dpos.end_date)
                                                                                                                                                                                                   and pp.occupational_group.id in [og.occupational_group.id for og in h_dpos_og_list[hh, dpos]]])
                                                                                        +  quicksum(
                                                                                           quicksum(x[t_slot, stud.id, hh.id, dep.id, d_pos.id] for d_pos in [dpos for dpos in h_dep_dpos_list[hh, dep] if  t_slot >= StartDate_to_Timeslot(dpos.start_date)
                                                                                                                                                                                                        and t_slot <= EndDate_to_Timeslot(dpos.end_date)
                                                                                                                                                                                                        and pp.occupational_group.id in [og.occupational_group.id for og in h_dep_dpos_og_list[hh, dep, dpos]]])
                                                                                                                                                for dep in h_dep_list[hh])
                                                                                                                                                for hh in [hos for hos in hospitals if  hos.id in [aou.organisationsgruppe_id for aou in stud_pp_aou_list[stud, pp]]
                                                                                                                                                                                    and hos.id != h.id]))
    print_end_notification('c', 20, hc != {})

    # Every department change has to get tracked to minimize the amount of department changes
    #
    if dc != {}:
        counter = 0
        for stud in persons:
            counter = counter + 1
            print_progress_bar('c', 21, counter)
            for pp in stud_pp_list[stud]:
                for t_slot in range(max(StartDate_to_Timeslot(pp.start_date), 0), min(EndDate_to_Timeslot(pp.end_date)+1, amount_of_months)):
                    if t_slot not in stud_uz_list[stud]:
                        if t_slot == 0:
                            for h in [h2 for h2 in hospitals if h2.id in [aou.organisationsgruppe_id for aou in stud_pp_aou_list[stud, pp]]]:
                                for a in allocations:
                                    if a.person_id == stud.id:
                                        for dep in h_dep_list[h]:
                                            if h.id != a.organisationsgruppe_id or dep.id != a.ausbildungsstaette_id:
                                                for d_pos in h_dep_dpos_list[h, dep]:
                                                    if t_slot >= StartDate_to_Timeslot(d_pos.start_date) and t_slot <= EndDate_to_Timeslot(d_pos.end_date):
                                                        model.addConstr(dc[t_slot, stud.id] >= x[t_slot, stud.id, h.id, dep.id, d_pos.id])
                                                for pt_block in [ptblock for ptblock in h_dep_ptblock_list[h, dep] if t_slot >= StartDate_to_Timeslot(ptblock.start_date)]:
                                                    for t_pos in [tpos for tpos in h_dep_ptblock_tpos_list[h, dep, pt_block] if t_slot >= StartDate_to_Timeslot(tpos.start_date)]:
                                                        model.addConstr(dc[t_slot, stud.id] >= y[t_slot, stud.id, h.id, dep.id, pt_block.ausbildungsblock_id, t_pos.id])
                        else:
                            for pp2 in stud_pp_list[stud]:
                                for t_slot2 in max_list([tslot2 for tslot2 in range(t_slot) if tslot2 >= StartDate_to_Timeslot(pp2.start_date) and tslot2 <= EndDate_to_Timeslot(pp2.end_date) and tslot2 not in stud_uz_list[stud]]):
                                    for h in [h2 for h2 in hospitals if h2.id in [aou.organisationsgruppe_id for aou in stud_pp_aou_list[stud, pp2]]]:
                                        for dep in h_dep_list[h]:
                                            model.addConstr(1 + dc[t_slot, stud.id] >= quicksum(x[t_slot2, stud.id, h.id, dep.id, d_pos.id] for d_pos in [dpos for dpos in h_dep_dpos_list[h, dep] if  t_slot2 >= StartDate_to_Timeslot(dpos.start_date)
                                                                                                                                                                                                   and t_slot2 <= EndDate_to_Timeslot(dpos.end_date)
                                                                                                                                                                                                   and pp2.occupational_group.id in [og.occupational_group.id for og in h_dep_dpos_og_list[h, dep, dpos]]])
                                                                                    +  quicksum(
                                                                                       quicksum(x[t_slot, stud.id, h.id, depp.id, d_pos.id] for d_pos in [dpos for dpos in h_dep_dpos_list[h, depp] if  t_slot >= StartDate_to_Timeslot(dpos.start_date)
                                                                                                                                                                                                    and t_slot <= EndDate_to_Timeslot(dpos.end_date)
                                                                                                                                                                                                    and pp.occupational_group.id in [og.occupational_group.id for og in h_dep_dpos_og_list[h, depp, dpos]]]) 
                                                                                                                                            for depp in [dep2 for dep2 in h_dep_list[h] if  dep2.id != dep.id
                                                                                                                                                                                        and h.id in [aou.organisationsgruppe_id for aou in stud_pp_aou_list[stud, pp]]])
                                                                                    +  quicksum(
                                                                                       quicksum(x[t_slot, stud.id, hh.id, str(hh.id), d_pos.id] for d_pos in [dpos for dpos in h_dpos_list[hh] if  t_slot >= StartDate_to_Timeslot(dpos.start_date)
                                                                                                                                                                                               and t_slot <= EndDate_to_Timeslot(dpos.end_date)
                                                                                                                                                                                               and pp.occupational_group.id in [og.occupational_group.id for og in h_dpos_og_list[hh, dpos]]])
                                                                                                                                                for hh in [hos for hos in hospitals if  hos.id in [aou.organisationsgruppe_id for aou in stud_pp_aou_list[stud, pp]]
                                                                                                                                                                                    and hos.id != h.id])
                                                                                    +  quicksum(
                                                                                       quicksum(
                                                                                       quicksum(x[t_slot, stud.id, hh.id, depp.id, d_pos.id] for d_pos in [dpos for dpos in h_dep_dpos_list[hh, depp] if  t_slot >= StartDate_to_Timeslot(dpos.start_date)
                                                                                                                                                                                                      and t_slot <= EndDate_to_Timeslot(dpos.end_date)
                                                                                                                                                                                                      and pp.occupational_group.id in [og.occupational_group.id for og in h_dep_dpos_og_list[hh, depp, dpos]]])
                                                                                                                                             for depp in h_dep_list[hh]) 
                                                                                                                                             for hh in [hos for hos in hospitals if  hos.id in [aou.organisationsgruppe_id for aou in stud_pp_aou_list[stud, pp]]
                                                                                                                                                                                 and hos.id != h.id]))
                                            model.addConstr(1 + dc[t_slot, stud.id] >= quicksum(
                                                                                       quicksum(y[t_slot2, stud.id, h.id, dep.id, pt_block.ausbildungsblock_id, t_pos.id] for t_pos in [tpos for tpos in h_dep_ptblock_tpos_list[h, dep, pt_block] if t_slot2 >= StartDate_to_Timeslot(tpos.start_date)])
                                                                                                                                                                          for pt_block in [ptblock for ptblock in h_dep_ptblock_list[h, dep] if t_slot2 >= StartDate_to_Timeslot(ptblock.start_date)])
                                                                                    +  quicksum(
                                                                                       quicksum(
                                                                                       quicksum(y[t_slot, stud.id, h.id, depp.id, pt_block.ausbildungsblock_id, t_pos.id] for t_pos in [tpos for tpos in h_dep_ptblock_tpos_list[h, depp, pt_block] if t_slot >= StartDate_to_Timeslot(tpos.start_date)])
                                                                                                                                                                          for pt_block in [ptblock for ptblock in h_dep_ptblock_list[h, depp] if t_slot >= StartDate_to_Timeslot(ptblock.start_date)])
                                                                                                                                                                          for depp in [dep2 for dep2 in h_dep_list[h] if  dep2.id != dep.id
                                                                                                                                                                                                                      and h.id in [aou.organisationsgruppe_id for aou in stud_pp_aou_list[stud, pp]]])
                                                                                    +  quicksum(
                                                                                       quicksum(
                                                                                       quicksum(
                                                                                       quicksum(y[t_slot, stud.id, hh.id, depp.id, pt_block.ausbildungsblock_id, t_pos.id] for t_pos in [tpos for tpos in h_dep_ptblock_tpos_list[hh, depp, pt_block] if t_slot >= StartDate_to_Timeslot(tpos.start_date)])
                                                                                                                                                                           for pt_block in [ptblock for ptblock in h_dep_ptblock_list[hh, depp] if t_slot >= StartDate_to_Timeslot(ptblock.start_date)])
                                                                                                                                                                           for depp in h_dep_list[hh])
                                                                                                                                                                           for hh in [hos for hos in hospitals if  hos.id in [aou.organisationsgruppe_id for aou in stud_pp_aou_list[stud, pp]]
                                                                                                                                                                                                               and hos.id != h.id]))
    print_end_notification('c', 21, dc != {})

    # Every single month assignment has to get tracked to minimize the amount of such occurrences
    #
    if sma != {}:
        counter = 0
        for stud in persons:
            counter = counter + 1
            print_progress_bar('c', 22, counter)
            for pp in stud_pp_list[stud]:
                for t_slot in range(max(StartDate_to_Timeslot(pp.start_date), 0), min(EndDate_to_Timeslot(pp.end_date)+1, amount_of_months)):
                    if t_slot not in stud_uz_list[stud]:
                        if t_slot == 0:
                            if len([aa for aa in allocations if aa.person_id == stud.id]) > 0:
                                for a in [aa for aa in allocations if aa.person_id == stud.id]:
                                    for h in [h2 for h2 in hospitals if h2.id in [aou.organisationsgruppe_id for aou in stud_pp_aou_list[stud, pp]]]:
                                        for dep in [depp for depp in h_dep_list[h] if depp.id != a.ausbildungsstaette_id or h.id != a.organisationsgruppe_id]:
                                            for d_pos in h_dep_dpos_list[h, dep]:
                                                if t_slot >= StartDate_to_Timeslot(d_pos.start_date) and t_slot <= EndDate_to_Timeslot(d_pos.end_date) and pp.occupational_group.id in [og.occupational_group.id for og in h_dep_dpos_og_list[h, dep, d_pos]]:
                                                    model.addConstr(sma[t_slot, stud.id] >= x[t_slot, stud.id, h.id, dep.id, d_pos.id]
                                                                                         -  quicksum(x[t_slot+1, stud.id, h.id, dep.id, d_posi.id] for d_posi in [dpos for dpos in h_dep_dpos_list[h, dep] for ppp in stud_pp_list[stud] if  t_slot+1 >= max(StartDate_to_Timeslot(ppp.start_date), StartDate_to_Timeslot(dpos.start_date))
                                                                                                                                                                                                                                         and t_slot+1 <= min(EndDate_to_Timeslot(ppp.end_date), EndDate_to_Timeslot(dpos.end_date))
                                                                                                                                                                                                                                         and t_slot+1 not in stud_uz_list[stud]
                                                                                                                                                                                                                                         and ppp.occupational_group.id in [og.occupational_group.id for og in h_dep_dpos_og_list[h, dep, dpos]]
                                                                                                                                                                                                                                         and h.id in [aou.organisationsgruppe_id for aou in stud_pp_aou_list[stud, ppp]]])
                                                                                         -  quicksum(x[t_slot+1, stud.id, h.id, str(h.id), d_posi.id] for d_posi in [dpos for dpos in h_dpos_list[h] for ppp in stud_pp_list[stud] if  t_slot+1 >= max(StartDate_to_Timeslot(ppp.start_date), StartDate_to_Timeslot(dpos.start_date))
                                                                                                                                                                                                                                   and t_slot+1 <= min(EndDate_to_Timeslot(ppp.end_date), EndDate_to_Timeslot(dpos.end_date))
                                                                                                                                                                                                                                   and t_slot+1 not in stud_uz_list[stud]
                                                                                                                                                                                                                                   and ppp.occupational_group.id in [og.occupational_group.id for og in h_dpos_og_list[h, dpos]]
                                                                                                                                                                                                                                   and h.id in [aou.organisationsgruppe_id for aou in stud_pp_aou_list[stud, ppp]]]))
                                            for pt_block in h_dep_ptblock_list[h, dep]:
                                                if t_slot >= StartDate_to_Timeslot(pt_block.start_date):
                                                    for t_pos in h_dep_ptblock_tpos_list[h, dep, pt_block]:
                                                        if t_slot >= StartDate_to_Timeslot(t_pos.start_date):
                                                            model.addConstr(sma[t_slot, stud.id] >= y[t_slot, stud.id, h.id, dep.id, pt_block.ausbildungsblock_id, t_pos.id]
                                                                                                 -  quicksum(
                                                                                                    quicksum(y[t_slot+1, stud.id, h.id, dep.id, pt_block2.ausbildungsblock_id, t_posi.id] for t_posi in [tpos for tpos in h_dep_ptblock_tpos_list[h, dep, pt_block2] for ppp in stud_pp_list[stud] if  t_slot+1 >= max(StartDate_to_Timeslot(ppp.start_date), StartDate_to_Timeslot(pt_block2.start_date), StartDate_to_Timeslot(tpos.start_date))
                                                                                                                                                                                                                                                                                                   and t_slot+1 <= EndDate_to_Timeslot(ppp.end_date)
                                                                                                                                                                                                                                                                                                   and t_slot+1 not in stud_uz_list[stud]
                                                                                                                                                                                                                                                                                                   and h.id in [aou.organisationsgruppe_id for aou in stud_pp_aou_list[stud, ppp]]])
                                                                                                                                                                                          for pt_block2 in h_dep_ptblock_list[h, dep]))
                            else:
                                for h in [h2 for h2 in hospitals if h2.id in [aou.organisationsgruppe_id for aou in stud_pp_aou_list[stud, pp]]]:
                                    for dep in h_dep_list[h]:
                                        for d_pos in h_dep_dpos_list[h, dep]:
                                            if t_slot >= StartDate_to_Timeslot(d_pos.start_date) and t_slot <= EndDate_to_Timeslot(d_pos.end_date) and pp.occupational_group.id in [og.occupational_group.id for og in h_dep_dpos_og_list[h, dep, d_pos]]:
                                                model.addConstr(sma[t_slot, stud.id] >= x[t_slot, stud.id, h.id, dep.id, d_pos.id]
                                                                                     -  quicksum(x[t_slot+1, stud.id, h.id, dep.id, d_posi.id] for d_posi in [dpos for dpos in h_dep_dpos_list[h, dep] for ppp in stud_pp_list[stud] if  t_slot+1 >= max(StartDate_to_Timeslot(ppp.start_date), StartDate_to_Timeslot(dpos.start_date))
                                                                                                                                                                                                                                     and t_slot+1 <= min(EndDate_to_Timeslot(ppp.end_date), EndDate_to_Timeslot(dpos.end_date))
                                                                                                                                                                                                                                     and t_slot+1 not in stud_uz_list[stud]
                                                                                                                                                                                                                                     and ppp.occupational_group.id in [og.occupational_group.id for og in h_dep_dpos_og_list[h, dep, dpos]]
                                                                                                                                                                                                                                     and h.id in [aou.organisationsgruppe_id for aou in stud_pp_aou_list[stud, ppp]]])
                                                                                     -  quicksum(x[t_slot+1, stud.id, h.id, str(h.id), d_posi.id] for d_posi in [dpos for dpos in h_dpos_list[h] for ppp in stud_pp_list[stud] if  t_slot+1 >= max(StartDate_to_Timeslot(ppp.start_date), StartDate_to_Timeslot(dpos.start_date))
                                                                                                                                                                                                                               and t_slot+1 <= min(EndDate_to_Timeslot(ppp.end_date), EndDate_to_Timeslot(dpos.end_date))
                                                                                                                                                                                                                               and t_slot+1 not in stud_uz_list[stud]
                                                                                                                                                                                                                               and ppp.occupational_group.id in [og.occupational_group.id for og in h_dpos_og_list[h, dpos]]
                                                                                                                                                                                                                               and h.id in [aou.organisationsgruppe_id for aou in stud_pp_aou_list[stud, ppp]]]))
                                        for pt_block in h_dep_ptblock_list[h, dep]:
                                            if t_slot >= StartDate_to_Timeslot(pt_block.start_date):
                                                for t_pos in h_dep_ptblock_tpos_list[h, dep, pt_block]:
                                                    if t_slot >= StartDate_to_Timeslot(t_pos.start_date):
                                                        model.addConstr(sma[t_slot, stud.id] >= y[t_slot, stud.id, h.id, dep.id, pt_block.ausbildungsblock_id, t_pos.id]
                                                                                             -  quicksum(
                                                                                                quicksum(y[t_slot+1, stud.id, h.id, dep.id, pt_block2.ausbildungsblock_id, t_posi.id] for t_posi in [tpos for tpos in h_dep_ptblock_tpos_list[h, dep, pt_block2] for ppp in stud_pp_list[stud] if  t_slot+1 >= max(StartDate_to_Timeslot(ppp.start_date), StartDate_to_Timeslot(pt_block2.start_date), StartDate_to_Timeslot(tpos.start_date))
                                                                                                                                                                                                                                                                                               and t_slot+1 <= EndDate_to_Timeslot(ppp.end_date)
                                                                                                                                                                                                                                                                                               and t_slot+1 not in stud_uz_list[stud]
                                                                                                                                                                                                                                                                                               and h.id in [aou.organisationsgruppe_id for aou in stud_pp_aou_list[stud, ppp]]])
                                                                                                                                                                                      for pt_block2 in h_dep_ptblock_list[h, dep]))
                        else:
                            if t_slot == amount_of_months-1:
                                for h in [h2 for h2 in hospitals if h2.id in [aou.organisationsgruppe_id for aou in stud_pp_aou_list[stud, pp]]]:
                                    for dep in h_dep_list[h]:
                                        for d_pos in h_dep_dpos_list[h, dep]:
                                            if t_slot >= StartDate_to_Timeslot(d_pos.start_date) and t_slot <= EndDate_to_Timeslot(d_pos.end_date) and pp.occupational_group.id in [og.occupational_group.id for og in h_dep_dpos_og_list[h, dep, d_pos]]:
                                                model.addConstr(sma[t_slot, stud.id] >= x[t_slot, stud.id, h.id, dep.id, d_pos.id]
                                                                                     -  quicksum(x[t_slot-1, stud.id, h.id, dep.id, d_posi.id] for d_posi in [dpos for dpos in h_dep_dpos_list[h, dep] for ppm in stud_pp_list[stud] if  t_slot-1 >= max(StartDate_to_Timeslot(ppm.start_date), StartDate_to_Timeslot(dpos.start_date))
                                                                                                                                                                                                                                     and t_slot-1 <= min(EndDate_to_Timeslot(ppm.end_date), EndDate_to_Timeslot(dpos.end_date))
                                                                                                                                                                                                                                     and t_slot-1 not in stud_uz_list[stud]
                                                                                                                                                                                                                                     and ppm.occupational_group.id in [og.occupational_group.id for og in h_dep_dpos_og_list[h, dep, dpos]]
                                                                                                                                                                                                                                     and h.id in [aou.organisationsgruppe_id for aou in stud_pp_aou_list[stud, ppm]]])
                                                                                     -  quicksum(x[t_slot-1, stud.id, h.id, str(h.id), d_posi.id] for d_posi in [dpos for dpos in h_dpos_list[h] for ppm in stud_pp_list[stud] if  t_slot-1 >= max(StartDate_to_Timeslot(ppm.start_date), StartDate_to_Timeslot(dpos.start_date))
                                                                                                                                                                                                                               and t_slot-1 <= min(EndDate_to_Timeslot(ppm.end_date), EndDate_to_Timeslot(dpos.end_date))
                                                                                                                                                                                                                               and t_slot-1 not in stud_uz_list[stud]
                                                                                                                                                                                                                               and ppm.occupational_group.id in [og.occupational_group.id for og in h_dpos_og_list[h, dpos]]
                                                                                                                                                                                                                               and h.id in [aou.organisationsgruppe_id for aou in stud_pp_aou_list[stud, ppm]]]))
                                        for pt_block in h_dep_ptblock_list[h, dep]:
                                            if t_slot >= StartDate_to_Timeslot(pt_block.start_date):
                                                for t_pos in h_dep_ptblock_tpos_list[h, dep, pt_block]:
                                                    if t_slot >= StartDate_to_Timeslot(t_pos.start_date):
                                                        model.addConstr(sma[t_slot, stud.id] >= y[t_slot, stud.id, h.id, dep.id, pt_block.ausbildungsblock_id, t_pos.id]
                                                                                             -  quicksum(
                                                                                                quicksum(y[t_slot-1, stud.id, h.id, dep.id, pt_block2.ausbildungsblock_id, t_posi.id] for t_posi in [tpos for tpos in h_dep_ptblock_tpos_list[h, dep, pt_block2] for ppm in stud_pp_list[stud] if  t_slot-1 >= max(StartDate_to_Timeslot(ppm.start_date), StartDate_to_Timeslot(pt_block2.start_date), StartDate_to_Timeslot(tpos.start_date))
                                                                                                                                                                                                                                                                                               and t_slot-1 <= EndDate_to_Timeslot(ppm.end_date)
                                                                                                                                                                                                                                                                                               and t_slot-1 not in stud_uz_list[stud]
                                                                                                                                                                                                                                                                                               and h.id in [aou.organisationsgruppe_id for aou in stud_pp_aou_list[stud, ppm]]]) 
                                                                                                                                                                                      for pt_block2 in h_dep_ptblock_list[h, dep]))
                            else:
                                for h in [h2 for h2 in hospitals if h2.id in [aou.organisationsgruppe_id for aou in stud_pp_aou_list[stud, pp]]]:
                                    for dep in h_dep_list[h]:
                                        for d_pos in h_dep_dpos_list[h, dep]:
                                            if t_slot >= StartDate_to_Timeslot(d_pos.start_date) and t_slot <= EndDate_to_Timeslot(d_pos.end_date) and pp.occupational_group.id in [og.occupational_group.id for og in h_dep_dpos_og_list[h, dep, d_pos]]:
                                                model.addConstr(sma[t_slot, stud.id] >= x[t_slot, stud.id, h.id, dep.id, d_pos.id]
                                                                                     -  quicksum(x[t_slot-1, stud.id, h.id, dep.id, d_posi.id] for d_posi in [dpos for dpos in h_dep_dpos_list[h, dep] for ppm in stud_pp_list[stud] if  t_slot-1 >= max(StartDate_to_Timeslot(ppm.start_date), StartDate_to_Timeslot(dpos.start_date))
                                                                                                                                                                                                                                     and t_slot-1 <= min(EndDate_to_Timeslot(ppm.end_date), EndDate_to_Timeslot(dpos.end_date))
                                                                                                                                                                                                                                     and t_slot-1 not in stud_uz_list[stud]
                                                                                                                                                                                                                                     and ppm.occupational_group.id in [og.occupational_group.id for og in h_dep_dpos_og_list[h, dep, dpos]]
                                                                                                                                                                                                                                     and h.id in [aou.organisationsgruppe_id for aou in stud_pp_aou_list[stud, ppm]]])
                                                                                     -  quicksum(x[t_slot-1, stud.id, h.id, str(h.id), d_posi.id] for d_posi in [dpos for dpos in h_dpos_list[h] for ppm in stud_pp_list[stud] if  t_slot-1 >= max(StartDate_to_Timeslot(ppm.start_date), StartDate_to_Timeslot(dpos.start_date))
                                                                                                                                                                                                                               and t_slot-1 <= min(EndDate_to_Timeslot(ppm.end_date), EndDate_to_Timeslot(dpos.end_date))
                                                                                                                                                                                                                               and t_slot-1 not in stud_uz_list[stud]
                                                                                                                                                                                                                               and ppm.occupational_group.id in [og.occupational_group.id for og in h_dpos_og_list[h, dpos]]
                                                                                                                                                                                                                               and h.id in [aou.organisationsgruppe_id for aou in stud_pp_aou_list[stud, ppm]]])
                                                                                     -  quicksum(x[t_slot+1, stud.id, h.id, dep.id, d_posi.id] for d_posi in [dpos for dpos in h_dep_dpos_list[h, dep] for ppp in stud_pp_list[stud] if  t_slot+1 >= max(StartDate_to_Timeslot(ppp.start_date), StartDate_to_Timeslot(dpos.start_date))
                                                                                                                                                                                                                                     and t_slot+1 <= min(EndDate_to_Timeslot(ppp.end_date), EndDate_to_Timeslot(dpos.end_date))
                                                                                                                                                                                                                                     and t_slot+1 not in stud_uz_list[stud]
                                                                                                                                                                                                                                     and ppp.occupational_group.id in [og.occupational_group.id for og in h_dep_dpos_og_list[h, dep, dpos]]
                                                                                                                                                                                                                                     and h.id in [aou.organisationsgruppe_id for aou in stud_pp_aou_list[stud, ppp]]])
                                                                                     -  quicksum(x[t_slot+1, stud.id, h.id, str(h.id), d_posi.id] for d_posi in [dpos for dpos in h_dpos_list[h] for ppp in stud_pp_list[stud] if  t_slot+1 >= max(StartDate_to_Timeslot(ppp.start_date), StartDate_to_Timeslot(dpos.start_date))
                                                                                                                                                                                                                               and t_slot+1 <= min(EndDate_to_Timeslot(ppp.end_date), EndDate_to_Timeslot(dpos.end_date))
                                                                                                                                                                                                                               and t_slot+1 not in stud_uz_list[stud]
                                                                                                                                                                                                                               and ppp.occupational_group.id in [og.occupational_group.id for og in h_dpos_og_list[h, dpos]]
                                                                                                                                                                                                                               and h.id in [aou.organisationsgruppe_id for aou in stud_pp_aou_list[stud, ppp]]]))
                                        for pt_block in h_dep_ptblock_list[h, dep]:
                                            if t_slot >= StartDate_to_Timeslot(pt_block.start_date):
                                                for t_pos in h_dep_ptblock_tpos_list[h, dep, pt_block]:
                                                    if t_slot >= StartDate_to_Timeslot(t_pos.start_date):
                                                        model.addConstr(sma[t_slot, stud.id] >= y[t_slot, stud.id, h.id, dep.id, pt_block.ausbildungsblock_id, t_pos.id]
                                                                                             -  quicksum(
                                                                                                quicksum(y[t_slot-1, stud.id, h.id, dep.id, pt_block2.ausbildungsblock_id, t_posi.id] for t_posi in [tpos for tpos in h_dep_ptblock_tpos_list[h, dep, pt_block2] for ppm in stud_pp_list[stud] if  t_slot-1 >= max(StartDate_to_Timeslot(ppm.start_date), StartDate_to_Timeslot(pt_block2.start_date), StartDate_to_Timeslot(tpos.start_date))
                                                                                                                                                                                                                                                                                               and t_slot-1 <= EndDate_to_Timeslot(ppm.end_date)
                                                                                                                                                                                                                                                                                               and t_slot-1 not in stud_uz_list[stud]
                                                                                                                                                                                                                                                                                               and h.id in [aou.organisationsgruppe_id for aou in stud_pp_aou_list[stud, ppm]]]) 
                                                                                                                                                                                      for pt_block2 in h_dep_ptblock_list[h, dep])
                                                                                             -  quicksum(
                                                                                                quicksum(y[t_slot+1, stud.id, h.id, dep.id, pt_block2.ausbildungsblock_id, t_posi.id] for t_posi in [tpos for tpos in h_dep_ptblock_tpos_list[h, dep, pt_block2] for ppp in stud_pp_list[stud] if  t_slot+1 >= max(StartDate_to_Timeslot(ppp.start_date), StartDate_to_Timeslot(pt_block2.start_date), StartDate_to_Timeslot(tpos.start_date))
                                                                                                                                                                                                                                                                                               and t_slot+1 <= EndDate_to_Timeslot(ppp.end_date)
                                                                                                                                                                                                                                                                                               and t_slot+1 not in stud_uz_list[stud]
                                                                                                                                                                                                                                                                                               and h.id in [aou.organisationsgruppe_id for aou in stud_pp_aou_list[stud, ppp]]]) 
                                                                                                                                                                                      for pt_block2 in h_dep_ptblock_list[h, dep]))
    print_end_notification('c', 22, sma != {})


    model.update()
    
    print('\nConstraints added successfully!\n\n')

    ########################
    ##### OPTIMIZATION #####
    ########################

    if type(sufficient_quality) == float:
        if sufficient_quality > 0.0001:
            model.optimize(softtime)
            print('\nOptimization (softtime) completed!')
        else:
            model.optimize()
            print('\nOptimization completed!')
    else:
        model.optimize()
        print('\nOptimization completed!')


    return model, x, y, z, vvp, vmwt, vwmwt, cmwt, dwt, hc, dc, sma
