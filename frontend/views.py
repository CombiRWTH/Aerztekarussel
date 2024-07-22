from django.shortcuts import render, redirect, get_object_or_404
from .forms import StudentRegistrationForm, HospitalPreferenceForm, UnterbrechungszeitenForm, UploadForm
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse, HttpResponse, HttpResponseRedirect
from django.forms import formset_factory
from django.views.decorators.http import require_http_methods
from datamodel.models import *
import json
from datamodel.importer import *
from django.db.models import Max
from django.contrib.auth.models import User
from dateutil import relativedelta
from exact_algo import algorithm
from datamodel.schedule_service import *
from datamodel.status_service import *
from datamodel.person_service import *
from datamodel.exporter import *
from gurobipy import *
import time
import random
from django.db import transaction
import calendar
from django.utils.dateformat import DateFormat
from django.utils.translation import gettext as _
from django.shortcuts import get_object_or_404
from datetime import datetime as dt
import statistics

# This function checks whether a user is an employee
def is_staff(user):
    return user.is_staff


# View for the start page that is accessible to all users
def allgemein(request):
    return render(request, 'frontend/allgemein.html')


# View for the registration page that is accessible to all users
def registration(request):
    return render(request, 'frontend/registration.html')


# View for the admin page that is only accessible to employees
@user_passes_test(is_staff)
def admin(request):
    return render(request, 'frontend/admin.html')


# View of students for logged-in users
@login_required
def student(request):
    # Get or creates a person based on user name of logged-in user and retrieves all organisation groups from database
    person, created = Personen.objects.get_or_create(name=request.user.username, defaults={'id_ext': 0})
    organisationsgruppen = Organisationsgruppe.objects.all()

    # Creates a form and fills it with  data of POST request
    if request.method == 'POST':
        form = HospitalPreferenceForm(request.POST, organisationsgruppen=organisationsgruppen, person=person)
        if form.is_valid():
            # Updates or creates priorities for organisational groups and person
            for organisation in organisationsgruppen:
                priority_field = form.cleaned_data.get(f'priority_{organisation.id}')
                if priority_field is not None:
                    priority, created = OrganisationsGruppenPriorities.objects.update_or_create(
                        person=person,
                        organisationsgruppe=organisation,
                        defaults={'priority': priority_field}
                    )

            # Create person data based on the transmitted data (create_person_data can be found at datamodel\person_service.py)
            create_person_data(person, request.POST.get('ausbildung_start'), request.POST.get('ausbildung_end'), request.POST.get('ausbildung_choice'))
            
            # Sucess message after POST request
            return render(request, 'frontend/student.html', {'form': form, 'message': 'Ihre Präferenzen wurden erfolgreich gespeichert.'})
    
    # Form afer GET request, render of frontend/student.html
    else:
        form = HospitalPreferenceForm(organisationsgruppen=organisationsgruppen, person=person)

    return render(request, 'frontend/student.html', {'form': form})


# Function that gets all organisation groups and returns them as a JSON response
def get_organisationsgruppen(request):
    organisationsgruppen = Organisationsgruppe.objects.all().values('id', 'name')
    data = list(organisationsgruppen)
    return JsonResponse(data, safe=False)


# Function for registering a user
def register(request):
    # Creates form with POST data, saves and logs in user, directs user to login
    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('login')
    #Form afer GET request, render of frontend/registration.html
    else:
        form = StudentRegistrationForm()
    return render(request, 'frontend/registration.html', {'form': form})


# Function for user login
def user_login(request):
    if request.method == 'POST':
        # Gets user name and password from POST data
        username = request.POST.get('username')
        password = request.POST.get('password')
        # Authenticates user (error message in case of failure), logs user in, forwarding depending on user role
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if user.is_staff:
                return redirect('adminaktuell')
            else:
                return redirect('student')
        else:
            return render(request, 'frontend/login.html', {'error': 'Falscher Benutzername oder Passwort'})
    # after GET request renders 'frontend/login.html'
    else:
        return render(request, 'frontend/login.html')
    

# View for admins to start algorithm
# Check if old input data is available to pass to HTML-Template otherwise empty data is passed
def aerg(request):
    try:
        objectiveweights = Parameter.objects.get(pk=0)
        context = {
            'objectiveweights': objectiveweights,
            'algorithm_sufficient_quality': '{:.2f}'.format(objectiveweights.algorithm_sufficient_quality),
        }
    except Parameter.DoesNotExist:
        context = {
            'objectiveweights': None,
            'algorithm_sufficient_quality': None,
        }

    return render(request, 'frontend/aerg.html', context)


# View for students to enter absence
def studentAusfall(request):
    return render(request, 'frontend/student_ausfall.html')


# Function for selecting the next colour from the palette
def get_next_color(existing_colors):
    color_palette = [color[0] for color in Organisationsgruppe.COLOR_PALETTE]
    available_colors = [color for color in color_palette if color not in existing_colors]
    if available_colors:
        return random.choice(available_colors)
    else:
        # When all colours have been used, generate a new random colour
        return "#{:06x}".format(random.randint(0, 0xFFFFFF))
    

# Function for displaying the timetable view
def bloecke_auswertung(request):
    month_range = request.GET.get('month_range', '12')

    if month_range != 'alles':
        month_range = int(month_range)

    schedules = Schedule.objects.select_related(
        'organisationsgruppe', 'ausbildungsstaette', 'ausbildungsinhalt'
    ).all().order_by('start_date')

    persons = Schedule.objects.values_list('person_id', flat=True).distinct().order_by('person_id')

    # Organise months and labels
    month_labels = []
    for schedule in schedules:
        start_date = schedule.start_date
        month_label = DateFormat(start_date).format('F Y')
        if month_label not in month_labels:
            month_labels.append(month_label)
        if month_range != 'alles' and len(month_labels) >= month_range:
            break

    # Get all Organisationsgruppen
    org_groups = Organisationsgruppe.objects.all()
    existing_colors = set(org_group.color for org_group in org_groups if org_group.color != '#FF0000')

    # Update the colours of the Organisationsgruppen that still have the default colour
    for org_group in org_groups:
        if org_group.color == '#FF0000':
            new_color = get_next_color(existing_colors)
            org_group.color = new_color
            org_group.save()
            existing_colors.add(new_color)

    org_group_colors = {org_group.name: org_group.color for org_group in org_groups}

    schedules_with_colors = []
    for schedule in schedules:
        org_group_name = schedule.organisationsgruppe.name if schedule.organisationsgruppe else ''
        color = org_group_colors.get(org_group_name, 'white')
        schedule_info = {
            'id': schedule.id,
            'person': schedule.person_id,
            'month_label': DateFormat(schedule.start_date).format('F Y'),
            'month': schedule.month,
            'color': color,
            'organisationsgruppe': org_group_name,
            'ausbildungsstaette': schedule.ausbildungsstaette.name if schedule.ausbildungsstaette else '',
            'ausbildungsinhalt': schedule.ausbildungsinhalt.name if schedule.ausbildungsinhalt else '',
        }
        schedules_with_colors.append(schedule_info)

    context = {
        'schedules': schedules_with_colors,
        'persons': persons,
        'months': month_labels,
        'org_group_colors': org_group_colors,
        'selected_range': month_range
    }

    return render(request, 'frontend/bloecke_auswertung.html', context)


# View for detailed algorithm results
def detailansicht_auswertung(request):
    #store data from schedule model
    schedules = Schedule.objects.select_related(
        'person',
        'ausbildungsstaette',
        'dienstposten',
        'ausbildungsblock',
        'ausbildungsstelle',
        'ausbildungspfad',
        'ausbildungserfordernis',
        'ausbildungsinhalt'
    ).all()

    # Check if data is available in schedule and find the max number of months (e.g. for dynamic table width)
    if schedules.exists():
        max_month = schedules.aggregate(Max('month'))['month__max']
    else:
        max_month = 0

    # create list of the month labels for header
    month_labels = []
    for schedule in schedules:
        start_date = schedule.start_date
        month_label = DateFormat(start_date).format('F Y')
        if month_label not in month_labels:
            month_labels.append(month_label)

    # Prepare data for template and add relevant data for person's month
    data = {}
    for schedule in schedules:
        person = schedule.person
        month = schedule.month
        if person not in data:
            data[person] = {}
        data[person][month] = {
            'organisationsgruppe': schedule.organisationsgruppe,  
            'ausbildungsstaette': schedule.ausbildungsstaette,  
            'dienstposten': schedule.dienstposten, 
            'ausbildungsstelle': schedule.ausbildungsstelle,  
            'ausbildungsinhalt': schedule.ausbildungsinhalt, 
        }

    # Conversion of data into structure accessible for template
    template_data = []
    for person, assignments in data.items():
        person_data = {'person': person, 'assignments': []}
        # add allocations for each month or None and add data to list
        for month in range(0, max_month + 1):
            if month in assignments:
                person_data['assignments'].append(assignments[month])
            else:
                person_data['assignments'].append(None)
        template_data.append(person_data)

    # Pass data to HTML-Template
    context = {
        'data': template_data,
        'months': month_labels,
        'month_count': max_month + 1
    }

    return render(request, 'detailansicht_auswertung.html', context)


# Get data from schedule model as list
def get_schedule(request):
    schedule = Schedule.objects.all()
    schedule_list = list(schedule)
    return JsonResponse(schedule_list, safe=False)


# Function to save parameters from def aerg and execute the algorithm (after submit)
def set_objectiveweights(request):
    if request.method == 'POST':
        try:
            # Load existing parameters with pk=0 to overwrite or create a new data set
            objectiveweights = get_object_or_404(Parameter, pk=0)
            
            # Update and saving data from POST request in database
            objectiveweights.objectiveweights_single_month_assignments = request.POST.get('singleMonthAssignments')
            objectiveweights.objectiveweights_months_without_training = request.POST.get('monthsWithoutTraining')
            objectiveweights.objectiveweights_consecutive_months_without_training = request.POST.get('consecutiveMonthsWithoutTraining')
            objectiveweights.objectiveweights_hospital_changes = request.POST.get('hospitalChanges')
            objectiveweights.objectiveweights_department_changes = request.POST.get('departmentChanges')
            objectiveweights.objectiveweights_months_at_cooperation_partner = request.POST.get('monthsAtCooperationPartner')
            objectiveweights.objectiveweights_violated_preferences = request.POST.get('violatedPreferences')
            objectiveweights.objectiveweights_var_months_without_training = request.POST.get('varMonthsWithoutTraining')
            objectiveweights.objectiveweights_var_violated_preferences = request.POST.get('varViolatedPreferences')
            objectiveweights.objectiveweights_departments_without_training = request.POST.get('departmentsWithoutTraining')
            objectiveweights.objectiveweights_var_weighted_months_without_training = request.POST.get('objectiveweights_var_weighted_months_without_training')
            objectiveweights.algorithm_penalization_value = request.POST.get('penalization_value')
            objectiveweights.algorithm_max_seconds_runtime = request.POST.get('max_seconds_runtime')
            objectiveweights.algorithm_sufficient_quality = request.POST.get('sufficient_quality')
            objectiveweights.algorithm_strict_var = 'checkbox_field' in request.POST
            objectiveweights.weekly_hours_needed_for_accreditation = request.POST.get('weekly_hours_needed_for_accreditation', 40) #is not queried on website, but is a prerequisite in database, has no influence on algorithm yet
            objectiveweights.start_date = request.POST.get('auswertung_start')
            objectiveweights.end_date = request.POST.get('auswertung_end')
        
            objectiveweights.save()

            # Starts algorithm based on specified parameters, if algorithm_strict_var is True certain other variables are passed
            if objectiveweights.algorithm_strict_var:
                model, x, y, z, vvp, vmwt, vwmwt, cmwt, dwt, hc, dc, sma = algorithm.IP_solver(['x','z'], int(objectiveweights.algorithm_penalization_value), int(objectiveweights.algorithm_max_seconds_runtime), float(objectiveweights.algorithm_sufficient_quality))
            else:
                model, x, y, z, vvp, vmwt, vwmwt, cmwt, dwt, hc, dc, sma = algorithm.IP_solver([], int(objectiveweights.algorithm_penalization_value), int(objectiveweights.algorithm_max_seconds_runtime), float(objectiveweights.algorithm_sufficient_quality))

            # If model is not unsolvable, the plan is updated
            if model.Status != GRB.INFEASIBLE:
                
                # Prepares X, Y and Z values 
                X = {}
                for x_indices in x.keys():
                    if x[x_indices].x > 0:
                        if len(x_indices) > 3:
                            X[(x_indices[0], x_indices[1])] = x_indices[2:]

                Y = {}
                for y_indices in y.keys():
                    if y[y_indices].x > 0:
                        if len(y_indices) > 3:
                            Y[(y_indices[0], y_indices[1])] = y_indices[2:]

                Z = {}
                for z_indices in z.keys():
                    if z[z_indices].x > 0:
                        if len(z_indices) > 5:
                            if z_indices[0] not in ['+1','-1']:
                                Z[(z_indices[0], z_indices[1])] = z_indices[2:]

                update_schedule(X, Y, Z)

                # Number of months in planning period
                for param in Parameter.objects.all():
                    start_date_plan = param.start_date
                    end_date_plan = param.end_date
                amount_of_months = abs((end_date_plan.year - start_date_plan.year) * 12 + end_date_plan.month - start_date_plan.month)+1

                # Statistical values for various parameters
                all_persons = Personen.objects.all()
                all_organisationsgruppen = Organisationsgruppe.objects.all()

                # Calculates the variance of the amounts of violated preferences
                if vvp != {}:
                    vvp_stat = (amount_of_months/12)*vvp[0].x
                else:
                    vvp_stat = None

                # Calculates the variance of the amounts of months without training
                if vmwt != {}:    
                    vmwt_stat = (amount_of_months/12)*vmwt[0].x
                else:
                    vmwt_stat = None

                # Calculates the variance of the amounts of weighted months without training
                if vwmwt != {}:
                    vwmwt_stat = vwmwt[0].x
                else:
                    vwmwt_stat = None

                # Calculates different statistical values for the amounts of consecutive months without training
                if cmwt != {}:
                    cmwt_stat = len([cmwt_indices for cmwt_indices in cmwt.keys() if cmwt[cmwt_indices].x > 0.5])
                    cmwt_per_stud_list = [len([cmwt_indices for cmwt_indices in cmwt.keys() if cmwt[cmwt_indices].x > 0.5 and cmwt_indices[1] == stud.id])
                                          for stud in all_persons]
                    cmwt_median_stat = statistics.median(cmwt_per_stud_list)
                    cmwt_mean_stat = statistics.mean(cmwt_per_stud_list)
                    cmwt_max_stat = max(cmwt_per_stud_list)
                else:
                    cmwt_stat = None
                    cmwt_median_stat = None
                    cmwt_mean_stat = None
                    cmwt_max_stat = None

                # Calculates different statistical values for the amounts of departments without training
                if dwt != {}:
                    dwt_stat = len([dwt_indices for dwt_indices in dwt.keys() if dwt[dwt_indices].x > 0.5])  
                    dwt_per_stud_list = [len([dwt_indices for dwt_indices in dwt.keys() if dwt[dwt_indices].x > 0.5 and dwt_indices[1] == stud.id])
                                         for stud in all_persons]
                    dwt_median_stat = statistics.median(dwt_per_stud_list)
                    dwt_mean_stat = statistics.mean(dwt_per_stud_list)
                    dwt_max_stat = max(dwt_per_stud_list)
                else:
                    dwt_stat = None
                    dwt_median_stat = None
                    dwt_mean_stat = None
                    dwt_max_stat = None

                # Calculates different statistical values for the amounts of hospital changes
                if hc != {}:
                    hc_stat = len([hc_indices for hc_indices in hc.keys() if hc[hc_indices].x > 0.5])
                    hc_per_stud_list = [len([hc_indices for hc_indices in hc.keys() if hc[hc_indices].x > 0.5 and hc_indices[1] == stud.id])
                                        for stud in all_persons]
                    hc_median_stat = statistics.median(hc_per_stud_list)
                    hc_mean_stat = statistics.mean(hc_per_stud_list)
                    hc_max_stat = max(hc_per_stud_list)
                else:
                    hc_stat = None
                    hc_median_stat = None
                    hc_mean_stat = None
                    hc_max_stat = None

                # Calculates different statistical values for the amounts of department changes
                if dc != {}:
                    dc_stat = len([dc_indices for dc_indices in dc.keys() if dc[dc_indices].x > 0.5])
                    dc_per_stud_list = [len([dc_indices for dc_indices in dc.keys() if dc[dc_indices].x > 0.5 and dc_indices[1] == stud.id])
                                        for stud in all_persons]
                    dc_median_stat = statistics.median(dc_per_stud_list)
                    dc_mean_stat = statistics.mean(dc_per_stud_list)
                    dc_max_stat = max(dc_per_stud_list)
                else:
                    dc_stat = None
                    dc_median_stat = None
                    dc_mean_stat = None
                    dc_max_stat = None

                # Calculates different statistical values for the amounts of single month assignments
                if sma != {}:
                    sma_stat = len([sma_indices for sma_indices in sma.keys() if sma[sma_indices].x > 0.5])
                    sma_per_stud_list = [len([sma_indices for sma_indices in sma.keys() if sma[sma_indices].x > 0.5 and sma_indices[1] == stud.id])
                                         for stud in all_persons]
                    sma_median_stat = statistics.median(sma_per_stud_list)
                    sma_mean_stat = statistics.mean(sma_per_stud_list)
                    sma_max_stat = max(sma_per_stud_list)
                else:
                    sma_stat = None
                    sma_median_stat = None
                    sma_mean_stat = None
                    sma_max_stat = None

                # Calculates different statistical values for the amounts of months without training
                mwt_stat = len([mwt_indices for mwt_indices in y.keys() 
                                if len(mwt_indices) == 3 and mwt_indices[2] == 0
                                and y[mwt_indices].x > 0.5 and y[mwt_indices[0], mwt_indices[1], 1].x < 0.5])
                mwt_per_stud_list = [len([mwt_indices for mwt_indices in y.keys() 
                                     if len(mwt_indices) == 3 and mwt_indices[2] == 0
                                     and y[mwt_indices].x > 0.5 and y[mwt_indices[0], mwt_indices[1], 1].x < 0.5 
                                     and mwt_indices[1] == stud.id]) for stud in all_persons]
                mwt_median_stat = statistics.median(mwt_per_stud_list)
                mwt_mean_stat = statistics.mean(mwt_per_stud_list)
                mwt_max_stat = max(mwt_per_stud_list)

                # Calculates different statistical values for the amounts of months at cooperation partner
                macp_stat = len([macp_indices for macp_indices in x.keys() for h in all_organisationsgruppen
                                 if x[macp_indices].x > 0.5 and macp_indices[2] == h.id and len(macp_indices) > 4 and h.is_kooperationspartner])
                macp_per_stud_list = [len([macp_indices for macp_indices in x.keys() for h in all_organisationsgruppen
                                      if x[macp_indices].x > 0.5 and macp_indices[2] == h.id and len(macp_indices) > 4
                                      and h.is_kooperationspartner and macp_indices[1] == stud.id]) for stud in all_persons]
                macp_median_stat = statistics.median(macp_per_stud_list)
                macp_mean_stat = statistics.mean(macp_per_stud_list)
                macp_max_stat = max(macp_per_stud_list)

                def one_value_out_of_list(L:list):
                    if len(L) != 1:
                        return 3
                    for l in L:
                        return l
                    
                stud_ogp_list = {}
                stud_ogp_of_h = {}
                for stud in all_persons:
                    stud_ogp_list[stud] = stud.organisationsgruppenpriorities_set.all()
                    for h in all_organisationsgruppen:
                        stud_ogp_of_h[stud, h] = one_value_out_of_list([ogp.priority for ogp in stud_ogp_list[stud] if ogp.organisationsgruppe_id == h.id])

                # Calculates different statistical values for the amounts of violated preference occurrences
                vpo_stat = len([vpo_indices for vpo_indices in x.keys() for stud in all_persons for h in all_organisationsgruppen
                                if len(vpo_indices) == 5 and vpo_indices[1] == stud.id and vpo_indices[2] == h.id
                                and x[vpo_indices].x > 0.5 and stud_ogp_of_h[stud, h] > min([ogp.priority for ogp in stud_ogp_list[stud]])])
                vpo_per_stud_list = [len([vpo_indices for vpo_indices in x.keys() for h in all_organisationsgruppen
                                     if len(vpo_indices) == 5 and vpo_indices[1] == stud.id and vpo_indices[2] == h.id
                                     and x[vpo_indices].x > 0.5 and stud_ogp_of_h[stud, h] > min([ogp.priority for ogp in stud_ogp_list[stud]])])
                                     for stud in all_persons]
                vpo_median_stat = statistics.median(vpo_per_stud_list)
                vpo_mean_stat = statistics.mean(vpo_per_stud_list)
                vpo_max_stat = max(vpo_per_stud_list)

                # Calculates different statistical values for the amounts of violated preference weights
                vpw_stat = len([vpw_indices for vpw_indices in x.keys() for stud in all_persons for h in all_organisationsgruppen
                                if len(vpw_indices) == 5 and vpw_indices[1] == stud.id and vpw_indices[2] == h.id
                                and x[vpw_indices].x > 0.5 and stud_ogp_of_h[stud, h]-1 == min([ogp.priority for ogp in stud_ogp_list[stud]])]) + 2*len([vpw_indices for vpw_indices in x.keys() for stud in all_persons for h in all_organisationsgruppen
                                                                                                                                                         if len(vpw_indices) == 5 and vpw_indices[1] == stud.id and vpw_indices[2] == h.id
                                                                                                                                                         and x[vpw_indices].x > 0.5 and stud_ogp_of_h[stud, h]-2 == min([ogp.priority for ogp in stud_ogp_list[stud]])])
                vpw_per_stud_list = [len([vpw_indices for vpw_indices in x.keys() for h in all_organisationsgruppen
                                     if len(vpw_indices) == 5 and vpw_indices[1] == stud.id and vpw_indices[2] == h.id
                                     and x[vpw_indices].x > 0.5 and stud_ogp_of_h[stud, h]-1 == min([ogp.priority for ogp in stud_ogp_list[stud]])]) + 2*len([vpw_indices for vpw_indices in x.keys() for h in all_organisationsgruppen
                                                                                                                                                              if len(vpw_indices) == 5 and vpw_indices[1] == stud.id and vpw_indices[2] == h.id
                                                                                                                                                              and x[vpw_indices].x > 0.5 and stud_ogp_of_h[stud, h]-2 == min([ogp.priority for ogp in stud_ogp_list[stud]])])
                                     for stud in all_persons]
                vpw_median_stat = statistics.median(vpw_per_stud_list)
                vpw_mean_stat = statistics.mean(vpw_per_stud_list)
                vpw_max_stat = max(vpw_per_stud_list)

                # If a not strict allocation is created, the amounts of broken constraints will be calculated here
                if objectiveweights.algorithm_strict_var:
                    mww_stat = 0
                    mww_median_stat = 0
                    mww_mean_stat = 0
                    mww_max_stat = 0

                    mpiso_stat = 0
                    mpiso_median_stat = 0
                    mpiso_mean_stat = 0
                    mpiso_max_stat = 0

                    mpisa_stat = 0
                    mpisa_median_stat = 0
                    mpisa_mean_stat = 0
                    mpisa_max_stat = 0

                    mpico_stat = 0
                    mpico_median_stat = 0
                    mpico_mean_stat = 0
                    mpico_max_stat = 0

                    mpica_stat = 0
                    mpica_median_stat = 0
                    mpica_mean_stat = 0
                    mpica_max_stat = 0

                    epico_stat = 0
                    epico_median_stat = 0
                    epico_mean_stat = 0
                    epico_max_stat = 0

                    epica_stat = 0
                    epica_median_stat = 0
                    epica_mean_stat = 0
                    epica_max_stat = 0
                else:
                    mww_stat = len([mww_indices for mww_indices in x.keys() 
                                    if len(mww_indices) == 3 and x[mww_indices].x > 0.5])                    
                    mww_per_stud_list = [len([mww_indices for mww_indices in x.keys() 
                                         if len(mww_indices) == 3 and x[mww_indices].x > 0.5
                                         and mww_indices[1] == stud.id]) for stud in all_persons]
                    mww_median_stat = statistics.median(mww_per_stud_list)
                    mww_mean_stat = statistics.mean(mww_per_stud_list)
                    mww_max_stat = max(mww_per_stud_list)

                    mpiso_stat = len([mpiso_indices for mpiso_indices in z.keys() 
                                      if len(mpiso_indices) == 4 and z[mpiso_indices].x > 0.5])
                    mpiso_per_stud_list = [len([mpiso_indices for mpiso_indices in z.keys() 
                                           if len(mpiso_indices) == 4 and z[mpiso_indices].x > 0.5
                                           and mpiso_indices[0] == stud.id]) for stud in all_persons]
                    mpiso_median_stat = statistics.median(mpiso_per_stud_list)
                    mpiso_mean_stat = statistics.mean(mpiso_per_stud_list)
                    mpiso_max_stat = max(mpiso_per_stud_list)

                    mpisa_stat = sum(z[mpisa_ind].x for mpisa_ind in [mpisa_indices for mpisa_indices in z.keys() if len(mpisa_indices) == 4])
                    mpisa_per_stud_list = [sum(z[mpisa_ind].x for mpisa_ind in [mpisa_indices for mpisa_indices in z.keys() 
                                           if len(mpisa_indices) == 4 and mpisa_indices[0] == stud.id]) for stud in all_persons]
                    mpisa_median_stat = statistics.median(mpisa_per_stud_list)
                    mpisa_mean_stat = statistics.mean(mpisa_per_stud_list)
                    mpisa_max_stat = max(mpisa_per_stud_list)

                    mpico_stat = len([mpico_indices for mpico_indices in z.keys() 
                                     if mpico_indices[0] == "-1" and z[mpico_indices].x > 0.5])
                    mpico_per_stud_list = [len([mpico_indices for mpico_indices in z.keys() 
                                          if mpico_indices[0] == "-1" and z[mpico_indices].x > 0.5
                                          and mpico_indices[1] == stud.id]) for stud in all_persons]
                    mpico_median_stat = statistics.median(mpico_per_stud_list)
                    mpico_mean_stat = statistics.mean(mpico_per_stud_list)
                    mpico_max_stat = max(mpico_per_stud_list)

                    mpica_stat = sum(z[mpica_ind].x for mpica_ind in [mpica_indices for mpica_indices in z.keys() if mpica_indices[0] == "-1"])
                    mpica_per_stud_list = [sum(z[mpica_ind].x for mpica_ind in [mpica_indices for mpica_indices in z.keys() 
                                           if mpica_indices[0] == "-1" and mpica_indices[1] == stud.id]) for stud in all_persons]
                    mpica_median_stat = statistics.median(mpica_per_stud_list)
                    mpica_mean_stat = statistics.mean(mpica_per_stud_list)
                    mpica_max_stat = max(mpica_per_stud_list)

                    epico_stat = len([epico_indices for epico_indices in z.keys() 
                                     if epico_indices[0] == "+1" and z[epico_indices].x > 0.5])
                    epico_per_stud_list = [len([epico_indices for epico_indices in z.keys() 
                                          if epico_indices[0] == "+1" and z[epico_indices].x > 0.5
                                          and epico_indices[1] == stud.id]) for stud in all_persons]
                    epico_median_stat = statistics.median(epico_per_stud_list)
                    epico_mean_stat = statistics.mean(epico_per_stud_list)
                    epico_max_stat = max(epico_per_stud_list)

                    epica_stat = sum(z[epica_ind].x for epica_ind in [epica_indices for epica_indices in z.keys() if epica_indices[0] == "+1"])
                    epica_per_stud_list = [sum(z[epica_ind].x for epica_ind in [epica_indices for epica_indices in z.keys() 
                                           if epica_indices[0] == "+1" and epica_indices[1] == stud.id]) for stud in all_persons]
                    epica_median_stat = statistics.median(epica_per_stud_list)
                    epica_mean_stat = statistics.mean(epica_per_stud_list)
                    epica_max_stat = max(epica_per_stud_list)

                # All calculated statistical values get loaded into the database
                statistic = ScheduleStatistics(date = dt.now(),                                              
                                               variance_violated_preferences = vvp_stat,
                                               variance_months_without_training = vmwt_stat,
                                               variance_weighted_months_without_training = vwmwt_stat,
                                               consecutive_months_without_training = cmwt_stat,
                                               consecutive_months_without_training_median = cmwt_median_stat,
                                               consecutive_months_without_training_mean  = cmwt_mean_stat,
                                               consecutive_months_without_training_max = cmwt_max_stat,
                                               departments_without_training = dwt_stat,
                                               departments_without_training_median = dwt_median_stat,
                                               departments_without_training_mean = dwt_mean_stat,
                                               departments_without_training_max = dwt_max_stat,
                                               hospital_changes = hc_stat,
                                               hospital_changes_median = hc_median_stat,
                                               hospital_changes_mean = hc_mean_stat,
                                               hospital_changes_max = hc_max_stat,
                                               department_changes = dc_stat,
                                               department_changes_median = dc_median_stat,
                                               department_changes_mean = dc_mean_stat,
                                               department_changes_max = dc_max_stat,
                                               single_month_assignments = sma_stat,
                                               single_month_assignments_median = sma_median_stat,
                                               single_month_assignments_mean = sma_mean_stat,
                                               single_month_assignments_max = sma_max_stat,
                                               months_without_training = mwt_stat,
                                               months_without_training_median = mwt_median_stat,
                                               months_without_training_mean = mwt_mean_stat,
                                               months_without_training_max = mwt_max_stat,
                                               months_at_cooperation_partner = macp_stat,
                                               months_at_cooperation_partner_median = macp_median_stat,
                                               months_at_cooperation_partner_mean = macp_mean_stat,
                                               months_at_cooperation_partner_max = macp_max_stat,     
                                               violated_preferences_occurrences = vpo_stat,
                                               violated_preferences_occurrences_median = vpo_median_stat,
                                               violated_preferences_occurrences_mean = vpo_mean_stat,
                                               violated_preferences_occurrences_max = vpo_max_stat,      
                                               violated_preferences_weight = vpw_stat,
                                               violated_preferences_weight_median = vpw_median_stat,
                                               violated_preferences_weight_mean = vpw_mean_stat,
                                               violated_preferences_weight_max = vpw_max_stat,     
                                               months_without_work = mww_stat,
                                               months_without_work_median = mww_median_stat,
                                               months_without_work_mean = mww_mean_stat,
                                               months_without_work_max = mww_max_stat,
                                               missing_progress_in_subject_occurrences = mpiso_stat,
                                               missing_progress_in_subject_occurrences_median = mpiso_median_stat,
                                               missing_progress_in_subject_occurrences_mean = mpiso_mean_stat,
                                               missing_progress_in_subject_occurrences_max = mpiso_max_stat,
                                               missing_progress_in_subject_amount = mpisa_stat,
                                               missing_progress_in_subject_amount_median = mpisa_median_stat,
                                               missing_progress_in_subject_amount_mean = mpisa_mean_stat,
                                               missing_progress_in_subject_amount_max = mpisa_max_stat,
                                               missing_progress_in_content_occurrences = mpico_stat,
                                               missing_progress_in_content_occurrences_median = mpico_median_stat,
                                               missing_progress_in_content_occurrences_mean = mpico_mean_stat,
                                               missing_progress_in_content_occurrences_max = mpico_max_stat,
                                               missing_progress_in_content_amount = mpica_stat,
                                               missing_progress_in_content_amount_median = mpica_median_stat,
                                               missing_progress_in_content_amount_mean = mpica_mean_stat,
                                               missing_progress_in_content_amount_max = mpica_max_stat,
                                               excess_progress_in_content_occurrences = epico_stat,
                                               excess_progress_in_content_occurrences_median = epico_median_stat,
                                               excess_progress_in_content_occurrences_mean = epico_mean_stat,
                                               excess_progress_in_content_occurrences_max = epico_max_stat,
                                               excess_progress_in_content_amount = epica_stat,
                                               excess_progress_in_content_amount_median = epica_median_stat,
                                               excess_progress_in_content_amount_mean = epica_mean_stat,
                                               excess_progress_in_content_amount_max = epica_max_stat)
                statistic.save()
            
            #Redirects to detailansicht_auswertung/ after end of algorithm
            return redirect('detailansicht_auswertung/')
        
        # If error occurs, redirect to frontend/aerg.html with error message
        except Exception as e:
            error_message = f'Es ist der Fehler: "{str(e)}" aufgetreten. Versuchen Sie ein neue Auswertung mit anderen Werten für die Parameter zu starten.'
            return render(request, 'detailansicht_auswertung.html', {'error_message': error_message})
    
    # If  request is not POST render frontend/aerg.html
    return render(request, 'frontend/aerg.html')


# Function for the timetable view of a logged-in student
@login_required
def serg(request):
    month_range = request.GET.get('month_range', '12')

    if month_range != 'alles':
        month_range = int(month_range)

    # Get the Personen instance for the logged-in user
    try:
        person = Personen.objects.get(name=request.user.username)
    except Personen.DoesNotExist:
        person = None

    if person:
        # Filter schedules by the logged-in user's Personen instance
        schedules = Schedule.objects.select_related(
            'organisationsgruppe', 'ausbildungsstaette', 'ausbildungsinhalt'
        ).filter(person=person).order_by('start_date')

        persons = [person.name]  
    else:
        schedules = []
        persons = []

    # Organisiere Monate und Beschriftungen
    month_labels = []
    for schedule in schedules:
        start_date = schedule.start_date
        month_label = DateFormat(start_date).format('F Y')
        if month_label not in month_labels:
            month_labels.append(month_label)
        if month_range != 'alles' and len(month_labels) >= int(month_range):
            break

    # Organise months and labels
    org_groups = Organisationsgruppe.objects.all()
    existing_colors = set(org_group.color for org_group in org_groups if org_group.color != '#FF0000')

    # Update the colours of the Organisationsgruppen that still have the default colour
    for org_group in org_groups:
        if org_group.color == '#FF0000':
            new_color = get_next_color(existing_colors)
            org_group.color = new_color
            org_group.save()
            existing_colors.add(new_color)

    org_group_colors = {org_group.name: org_group.color for org_group in org_groups}

    schedules_with_colors = []
    for schedule in schedules:
        org_group_name = schedule.organisationsgruppe.name if schedule.organisationsgruppe else ''
        color = org_group_colors.get(org_group_name, 'white')
        schedule_info = {
            'id': schedule.id,
            'person': person.name,
            'month_label': DateFormat(schedule.start_date).format('F Y'),
            'color': color,
            'organisationsgruppe': org_group_name,
            'ausbildungsstaette': schedule.ausbildungsstaette.name if schedule.ausbildungsstaette else '',
            'ausbildungsinhalt': schedule.ausbildungsinhalt.name if schedule.ausbildungsinhalt else '',
        }
        schedules_with_colors.append(schedule_info)

    context = {
        'schedules': schedules_with_colors,
        'persons': persons,
        'months': month_labels,
        'org_group_colors': org_group_colors,
        'selected_range': month_range 
    }

    return render(request, 'frontend/serg.html', context)


# Function for adminaktuell
def adminaktuell(request):
    organisationsgruppen = Organisationsgruppe.objects.prefetch_related('ausbildungsstaette_set', 'dienstposten_set').all()
    return render(request, 'frontend/adminaktuell.html', {'organisationsgruppen': organisationsgruppen})


# Function for students to save absence or reedit that
@login_required
def create_student_ausfall(request):
    print('In create_student_ausfall view')
    person, created = Personen.objects.get_or_create(name=request.user.username, defaults={'id_ext': 0})

    if request.method == 'POST':
        print('POST data:', request.POST)
        
        # Delete existing entries for the student
        Unterbrechungszeiten.objects.filter(person=person).delete()

        # Extract the data from POST
        start_dates = request.POST.getlist('start_date')
        end_dates = request.POST.getlist('end_date')
        
        num_entries = len(start_dates)

        for i in range(num_entries):
            data = {
                'start_date': start_dates[i],
                'end_date': end_dates[i]
            }
            
            form = UnterbrechungszeitenForm(data, person=person)
            if form.is_valid():
                unterbrechungszeiten = form.save(commit=False)
                unterbrechungszeiten.person = person
                unterbrechungszeiten.save()
                print(f'Form {i+1} saved successfully')
            else:
                print(f'Form {i+1} has errors:', form.errors)


        entries = Unterbrechungszeiten.objects.filter(person=person)      

        print('entries: ' + str(entries))  
        
        return render(request, 'frontend/student_ausfall.html', {'form': UnterbrechungszeitenForm(person=person), 'entries': entries, 'message': 'Ihre Ausfälle wurden erfolgreich gespeichert.'})
    
    else:
        print("in get create_student_ausfall")
        form = UnterbrechungszeitenForm(person=person)
        entries = Unterbrechungszeiten.objects.filter(person=person)

        print('entries: ' + str(entries))
    
    print('entries: ' + str(entries))
    return render(request, 'frontend/student_ausfall.html', {'form': form, 'entries': entries})

# Function for admins to create or edit hospitals
@user_passes_test(is_staff)
def create_or_edit_hospital(request, organisation_id=None):
    print('inside create_or_edit_hospital')
    organisationsgruppe = None
    ausbildungsstaetten = None
    dienstposten = None
    ausbildungsstaette_tags = None
    planbare_ausbildungsbloecke = None
    ausbildungsstelle = None
    genehmigte_fachgebiete = None    
    
    if organisation_id:
        print('organisation_id exists')
        # load objects
    
        organisationsgruppe = Organisationsgruppe.objects.get(id=organisation_id)

        ausbildungsstaetten = Ausbildungsstaette.objects.filter(organisationsgruppe=organisationsgruppe)

        dienstposten = Dienstposten.objects.filter(organisationsgruppe=organisationsgruppe)

        ausbildungsstaette_tags = AusbildungsstaettenTags.objects.filter(ausbildungsstaette__organisationsgruppe=organisationsgruppe)

        planbare_ausbildungsbloecke = PlanbareAusbildungsbloecke.objects.filter(ausbildungsstaette__organisationsgruppe=organisationsgruppe)

        ausbildungsstelle = Ausbildungsstelle.objects.filter(planbarer_ausbildungsblock__ausbildungsstaette__organisationsgruppe=organisationsgruppe)

        genehmigte_fachgebiete = GenehmigteFachgebiete.objects.filter(planbarer_ausbildungsblock__ausbildungsstaette__organisationsgruppe=organisationsgruppe)

    if request.method == 'POST':
        print('in post')

        # Extract data from POST request
        koorperationspartner = request.POST.get('koorperationspartner') == 'ja'
        krankenhausname = request.POST.get('krankenhausname')

        # editing (if existend) stores the id of the hospital that has been edited
        print(request.POST.get('editing'))
        if request.POST.get('editing'):
            try:
                # Fetch the existing organisation group to update it
                organisationsgruppe = Organisationsgruppe.objects.get(id=request.POST.get('editing'))
                organisationsgruppe.is_kooperationspartner = koorperationspartner
                organisationsgruppe.name = krankenhausname
                organisationsgruppe.save()
                created = False
            except Organisationsgruppe.DoesNotExist:
                # Log or handle the case where the organisation_id does not exist
                print(f"Organisation with id {organisation_id} does not exist.")
        else:
            # Create a new hospital if no organisation_id is provided
            organisationsgruppe, created = Organisationsgruppe.objects.update_or_create(
                id_ext=0,
                is_kooperationspartner=request.POST.get('koorperationspartner') == 'ja',
                name=request.POST.get('krankenhausname')
            )


        print('Organisation tuple:', (organisationsgruppe, created))
        print('Organisation ID:', organisationsgruppe.id)



        # Ausbildungsstaette
        ausbildungsstaette, created = Ausbildungsstaette.objects.update_or_create(
            id_ext=0,
            organisationsgruppe=organisationsgruppe,
            name=request.POST.get('ausbildungsstaette_name')
        )

        # AusbildungsstaettenTags
        ausbildungsstaette_tags = request.POST.getlist('ausbildungsstaette_tags')
        for tag in ausbildungsstaette_tags:
            AusbildungsstaettenTags.objects.update_or_create(
                ausbildungsstaette=ausbildungsstaette,
                tag=tag
            )

        # Planbare Ausbildungsbloecke
        planbare_ausbildungsblock_id = request.POST.get('planbarer_ausbildungsblock_id')
        print('planbare ausblidungsblock start:' + str(request.POST.get('planbarer_ausbildungsblock_start')))
        if not Ausbildungsbloecke.objects.filter(id=planbare_ausbildungsblock_id).exists():
            ausbildungsblock, created = Ausbildungsbloecke.objects.update_or_create(id_ext=0)
        else:
            ausbildungsblock, created = Ausbildungsbloecke.objects.get(id=planbare_ausbildungsblock_id)

        planbare_ausbildungsbloecke, created = PlanbareAusbildungsbloecke.objects.update_or_create(
            ausbildungsblock=ausbildungsblock,
            ausbildungsstaette=ausbildungsstaette,
            start_date=request.POST.get('planbarer_ausbildungsblock_start')
        )

        # Ausbildungsstelle
        start_dates = request.POST.getlist('start_date_ausbildungsStellen')
        durations_in_month = request.POST.getlist('duration_ausbildungsStellen')
        for start_date, duration in zip(start_dates, durations_in_month):
            Ausbildungsstelle.objects.update_or_create(
                id_ext=0,
                planbarer_ausbildungsblock=planbare_ausbildungsbloecke,
                start_date=start_date,
                duration_in_month=duration
            )

        # Genehmigte Fachgebiete
        fachgebiete_ids = request.POST.getlist('fachgebietID')
        durations_genehmigteFachgebiete = request.POST.getlist('duration_genehmigteFachgebiete')
        for fachgebiet_id, duration in zip(fachgebiete_ids, durations_genehmigteFachgebiete):
            if not Fachgebiete.objects.filter(id=fachgebiet_id).exists():
                fachgebiet, created = Fachgebiete.objects.update_or_create(id_ext=0)
            else:
                fachgebiet, created = Fachgebiete.objects.get_or_create(id=fachgebiet_id)

            genehmigte_fachgebiete = GenehmigteFachgebiete.objects.update_or_create(
                planbarer_ausbildungsblock=planbare_ausbildungsbloecke,
                fachgebiet=fachgebiet,
                duration_in_month=duration
            )

        # Dienstposten (first category)
        ausbildungsstaette_dienstposten_start = request.POST.get('ausbildungsstaette_dienstposten_start')
        ausbildungsstaette_dienstposten_end = request.POST.get('ausbildungsstaette_dienstposten_end')
        ausbildungsstaette_dienstposten_hours = request.POST.get('ausbildungsstaette_dienstposten_hours')

        # Ensure that these are correctly assigned and not nullable if required
        if ausbildungsstaette_dienstposten_start and ausbildungsstaette_dienstposten_end and ausbildungsstaette_dienstposten_hours:
            try:
                ausbildungsstaette_dienstposten = Dienstposten.objects.get(
                    id_ext=0,
                    organisationsgruppe=organisationsgruppe,
                    ausbildungsstaette=ausbildungsstaette
                )
                ausbildungsstaette_dienstposten.start_date = ausbildungsstaette_dienstposten_start
                ausbildungsstaette_dienstposten.end_date = ausbildungsstaette_dienstposten_end
                ausbildungsstaette_dienstposten.hours = ausbildungsstaette_dienstposten_hours
                ausbildungsstaette_dienstposten.save()
            except Dienstposten.DoesNotExist:
                ausbildungsstaette_dienstposten = Dienstposten.objects.create(
                    id_ext=0,
                    organisationsgruppe=organisationsgruppe,
                    ausbildungsstaette=ausbildungsstaette,
                    start_date=ausbildungsstaette_dienstposten_start,
                    end_date=ausbildungsstaette_dienstposten_end,
                    hours=ausbildungsstaette_dienstposten_hours
                )

        occupational_groups = request.POST.getlist('ausbildungsstaette_dienstposten_occupationalgroups')
        for occupational_group_id in occupational_groups:
            if not OccupationalGroups.objects.filter(id=occupational_group_id).exists():
                occupational_group, created = OccupationalGroups.objects.update_or_create(id=0)
            else:
                occupational_group, created = OccupationalGroups.objects.get_or_create(id=occupational_group_id)

            FoccupationalGroups = OccupationalGroupsDienstposten.objects.update_or_create(
                dienstposten=ausbildungsstaette_dienstposten,
                occupational_group=occupational_group
            )

        associated_ausbildungsbloecke = request.POST.getlist(
            'ausbildungsstaette_dienstposten_associatedausbildungsbloecke')
        for ausbildungsblock_id in associated_ausbildungsbloecke:
            if Ausbildungsbloecke.objects.filter(id=ausbildungsblock_id).exists():
                ausbildungsblock, created = Ausbildungsbloecke.objects.get_or_create(id=ausbildungsblock_id)
            else:
                ausbildungsblock, created = Ausbildungsbloecke.objects.get_or_create(id=0)

            FassociatedAusbildungsbloecke = AssociatedAusbildungsbloecke.objects.update_or_create(
                dienstposten=ausbildungsstaette_dienstposten,
                ausbildungsblock=ausbildungsblock
            )   

        # Dienstposten (second category)
        dienstposten_start = request.POST.get('dienstposten_start')
        dienstposten_end = request.POST.get('dienstposten_end')
        dienstposten_hours = request.POST.get('dienstposten_hours')

        print('diensposten_end: ' + dienstposten_end) 

        # Ensure that these are correctly assigned and not nullable if required
        if dienstposten_start and dienstposten_end and dienstposten_hours:
            try:
                dienstposten = Dienstposten.objects.get(
                    id_ext=0,
                    organisationsgruppe=organisationsgruppe,
                    ausbildungsstaette=ausbildungsstaette
                )
                dienstposten.start_date = dienstposten_start
                dienstposten.end_date = dienstposten_end
                dienstposten.hours = dienstposten_hours
                dienstposten.save()
            except Dienstposten.DoesNotExist:
                dienstposten = Dienstposten.objects.create(
                    id_ext=0,
                    organisationsgruppe=organisationsgruppe,
                    ausbildungsstaette=ausbildungsstaette,
                    start_date=dienstposten_start,
                    end_date=dienstposten_end,
                    hours=dienstposten_hours
                )    

        occupational_groups = request.POST.getlist('dienstposten_occupationalgroups')
        for occupational_group_id in occupational_groups:
            if not OccupationalGroups.objects.filter(id=occupational_group_id).exists():
                occupational_group, created = OccupationalGroups.objects.update_or_create(id_ext=0)
            else:
                occupational_group, created = OccupationalGroups.objects.get_or_create(id=occupational_group_id)

            OccupationalGroupsDienstposten.objects.update_or_create(
                dienstposten=dienstposten,
                occupational_group=occupational_group
            )

        associated_ausbildungsbloecke = request.POST.getlist('dienstposten_associatedausbildungsbloecke')
        for ausbildungsblock_id in associated_ausbildungsbloecke:
            if not Ausbildungsbloecke.objects.filter(id=ausbildungsblock_id).exists():
                ausbildungsblock, created = Ausbildungsbloecke.objects.update_or_create(id_ext=0)
            else:
                ausbildungsblock, created = Ausbildungsbloecke.objects.get_or_create(id=ausbildungsblock_id)

            AssociatedAusbildungsbloecke.objects.update_or_create(
                dienstposten=dienstposten,
                ausbildungsblock=ausbildungsblock
            )

        return redirect('adminaktuell')
        
    else: 
        print('not POST')

        organisationsgruppe=organisationsgruppe
        ausbildungsstaette = ausbildungsstaetten
        dienstposten = dienstposten
        ausbildungsstaette_tags = ausbildungsstaette_tags
        planbare_ausbildungsbloecke = planbare_ausbildungsbloecke
        ausbildungsstelle = ausbildungsstelle
        genehmigte_fachgebiete = genehmigte_fachgebiete

        print(f"Hospital: {organisationsgruppe}")

        # Query all Dienstposten objects
        all_dienstposten = Dienstposten.objects.filter(organisationsgruppe=organisationsgruppe)

        # Filter Dienstposten with ausbildungsstaette_id
        ausbildungsstaette_dienstposten = all_dienstposten.filter(ausbildungsstaette__isnull=False)

        # Filter Dienstposten without ausbildungsstaette_id
        regular_dienstposten = all_dienstposten.filter(ausbildungsstaette__isnull=True)

        print(f"Dienstposten all: {all_dienstposten}")
        print(f"Dienstposten with asu: {ausbildungsstaette_dienstposten}")
        print(f"Dienstposten wihtout: {regular_dienstposten}")

        asb_pairs = []
        ogd_pairs = []

        for dp in all_dienstposten:
            
            # Query AssociatedAusbildungsbloecke objects for dp
            asb = AssociatedAusbildungsbloecke.objects.filter(dienstposten=dp)
            asb_ids = [obj.id for obj in asb if obj.id]  # Extract valid IDs
            asb_pairs.extend([(dp.id, asb_id) for asb_id in asb_ids])
            
            # Query OccupationalGroupsDienstposten objects for dp
            ogd = OccupationalGroupsDienstposten.objects.filter(dienstposten=dp)
            ogd_ids = [obj.id for obj in ogd if obj.id]  # Extract valid IDs
            ogd_pairs.extend([(dp.id, ogd_id) for ogd_id in ogd_ids])

        # Create dictionaries for regular_dienstposten
        regular_dienstposten_list = [
            {
                "id": dp.id,
                "start_date": dp.start_date,
                "end_date": dp.end_date,
                "hours": dp.hours,
                "associatedausbildungsbloecke": next((pair[1] for pair in asb_pairs if pair[0] == dp.id), None),
                "occupationalgroupsdienstposten": next((pair[1] for pair in ogd_pairs if pair[0] == dp.id), None)
            }
            for dp in regular_dienstposten
        ]

        # Create dictionaries for ausbildungsstaette_dienstposten
        ausbildungsstaette_dienstposten_list = [
            {
                "id": dp.id,
                "start_date": dp.start_date,
                "end_date": dp.end_date,
                "hours": dp.hours,
                "associatedausbildungsbloecke": next((pair[1] for pair in asb_pairs if pair[0] == dp.id), None),
                "occupationalgroupsdienstposten": next((pair[1] for pair in ogd_pairs if pair[0] == dp.id), None)
            }
            for dp in ausbildungsstaette_dienstposten
        ]

        data = {
            "organisationsgruppe": {
                "id": organisationsgruppe.id,
                "id_ext": organisationsgruppe.id_ext,
                "is_kooperationspartner": organisationsgruppe.is_kooperationspartner,
                "name": organisationsgruppe.name,
            },
            "ausbildungsstaetten": ausbildungsstaetten,
            "dienstposten": regular_dienstposten_list,
            "ausbildungsstaette_dienstposten": ausbildungsstaette_dienstposten_list,
            "ausbildungsstaette_tags": ausbildungsstaette_tags,
            "planbarer_ausbildungsblock": planbare_ausbildungsbloecke,
            "ausbildungsstelle": ausbildungsstelle,
            "genehmigte_fachgebiete": genehmigte_fachgebiete
        }

        print('Data json: ' + str(data))
        
        return render(request, 'frontend/admin.html', data)




@require_http_methods(["DELETE"])
def delete_organisation(request, id):
    try:
        organisation = Organisationsgruppe.objects.get(pk=id)
        organisation.delete()
        return JsonResponse({'status': 'success'})
    except Organisationsgruppe.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Organisationsgruppe nicht gefunden'}, status=404)
    
# Function for fetching the statistics page
def statistik_auswertung(request):
    # Retrieve the latest data record
    eintrag = ScheduleStatistics.objects.latest('date')
    return render(request, 'statistik_auswertung.html', {'eintrag': eintrag})


@user_passes_test(is_staff)
def import_export(request):
    dmStatusDefault, created = DatamodelStatus.objects.using("default").get_or_create(
            id=0,
            defaults={"is_admin_primary": True, "is_user_primary": True},
        )

    dmStatusOnlyDatamodel, created = DatamodelStatus.objects.using("only_datamodel").get_or_create(
            id=0,
            defaults={"is_admin_primary": False, "is_user_primary": False},
        )

    return render(request, 'frontend/import_export.html', {'status_default': dmStatusDefault, 'status_only_datamodel': dmStatusOnlyDatamodel})

@user_passes_test(is_staff)
def activate_admin_primary(request):
    # switch the database for admins
    set_admin_primary()
    return HttpResponseRedirect("/import_export/")
    
@user_passes_test(is_staff)
def activate_user_primary(request):
    # switch the database for users
    set_user_primary()
    return HttpResponseRedirect("/import_export/")

@user_passes_test(is_staff)
def export_file_default(request):
    # export of the default database
    status_default = DatamodelStatus.objects.using("default").get(id=0) 
    file_path = f'json_files/export_{"live_db" if status_default.is_user_primary else "test_db"}_{request.user.username}_{time.strftime("%d_%m_%Y-%H_%M_%S")}.json'
    export_db("default", file_path)

    if os.path.exists(file_path):
        with open(file_path, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type="application/json")
            response['Content-Disposition'] = 'attachment; filename=' + os.path.basename(file_path)
            return response
    raise Http404

@user_passes_test(is_staff)
def export_file_only_datamodel(request):
    # export of the datamodel database
    status_default = DatamodelStatus.objects.using("only_datamodel").get(id=0) 
    file_path = f'json_files/export_{"live_db" if status_default.is_user_primary else "test_db"}_{request.user.username}_{time.strftime("%d_%m_%Y-%H_%M_%S")}.json'
    export_db("only_datamodel", file_path)

    if os.path.exists(file_path):
        with open(file_path, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type="application/json")
            response['Content-Disposition'] = 'attachment; filename=' + os.path.basename(file_path)
            return response
    raise Http404

@user_passes_test(is_staff)
def import_file(request):
    if request.method == "POST":
        form = UploadForm(request.POST, request.FILES)
        if form.is_valid():
            # check, which db to use for the import
            # default db
            status_default = DatamodelStatus.objects.using("default").get(id=0)        
            if not status_default.is_user_primary:
                status_default.import_file = request.FILES["import_file"]
                status_default.save(using="default")

                load_file(status_default, "default")

            # only_datamodel db
            status_only_datamodel = DatamodelStatus.objects.using("only_datamodel").get(id=0)
            if not status_only_datamodel.is_user_primary:
                status_only_datamodel.import_file = request.FILES["import_file"]
                status_only_datamodel.save(using="only_datamodel")

                load_file(status_only_datamodel, "only_datamodel")

            return HttpResponseRedirect("/import_export/")
    else:
        form = UploadForm()
    return render(request, "frontend/upload.html", {"form": form})