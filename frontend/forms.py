from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django import forms
from django.forms import inlineformset_factory
from datamodel.models import *

# Registration form
class StudentRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")


# Interruption times form
class UnterbrechungszeitenForm(forms.ModelForm):
    class Meta:
        model = Unterbrechungszeiten
        fields = ['start_date', 'end_date']  


    def __init__(self, *args, **kwargs):
        person = kwargs.pop('person', None)
        super(UnterbrechungszeitenForm, self).__init__(*args, **kwargs)
        self.fields['start_date'].widget.attrs.update({'class': 'custom-class', 'placeholder': 'YYYY-MM-DD'})
        self.fields['end_date'].widget.attrs.update({'class': 'custom-class', 'placeholder': 'YYYY-MM-DD'})
        self.person = person 
    

    def save(self, commit=True):
        start_date = self.cleaned_data.get('start_date')
        end_date = self.cleaned_data.get('end_date')

        if self.person and start_date and end_date:
            unterbrechungszeit, created = Unterbrechungszeiten.objects.update_or_create(
                person=self.person,
                start_date=start_date,
                end_date=end_date,
            )
            return unterbrechungszeit
        else:
            raise ValueError("Person or start_date or end_date missing, cannot save.")


# Hospital preferences form
class HospitalPreferenceForm(forms.Form):
    CHOICES = [
        (1, 'Sehr gut'),
        (2, 'Neutral'),
        (3, 'Sehr schlecht')
    ]

    def __init__(self, *args, **kwargs):
        organisationsgruppen = kwargs.pop('organisationsgruppen', None)
        person = kwargs.pop('person', None)
        super().__init__(*args, **kwargs)
        if organisationsgruppen:
            for organisation in organisationsgruppen:
                initial_priority = 3  # Defaultvalue
                if person:
                    try:
                        existing_priority = OrganisationsGruppenPriorities.objects.get(person=person, organisationsgruppe=organisation)
                        initial_priority = existing_priority.priority
                    except OrganisationsGruppenPriorities.DoesNotExist:
                        pass
                self.fields[f'priority_{organisation.id}'] = forms.ChoiceField(
                    choices=self.CHOICES,
                    initial=initial_priority,
                    label=organisation.name,
                    widget=forms.Select(attrs={'class': 'form-control'})
                )

    def get_initial_priority(self, organisation):
        try:
            priority = OrganisationsGruppenPriorities.objects.get(person=self.person, organisationsgruppe=organisation)
            return priority.priority
        except OrganisationsGruppenPriorities.DoesNotExist:
            return 3  # Defaultvalue 'Sehr schlecht'

    def save(self):
        for field_name, field_value in self.cleaned_data.items():
            organisation_id = int(field_name.split('_')[1])
            priority, created = OrganisationsGruppenPriorities.objects.update_or_create(
                person=self.person,
                organisationsgruppe_id=organisation_id,
                defaults={'priority': field_value}
            )


class UploadForm(forms.ModelForm):
    class Meta:
        model = DatamodelStatus
        fields = ['import_file']