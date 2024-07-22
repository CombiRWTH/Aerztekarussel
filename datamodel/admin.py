from django.contrib import admin

from .models import *

admin.site.register(DatamodelStatus)
admin.site.register(Fachgebiete)
admin.site.register(Ausbildungsbloecke)
admin.site.register(Ausbildungserfordernisse)
admin.site.register(Ausbildungsinhalte)
admin.site.register(AusbildungsinhalteTags)
admin.site.register(AusbildungsStellenAnforderungen)
admin.site.register(OccupationalGroups)
admin.site.register(Personal)

admin.site.register(Organisationsgruppe)
admin.site.register(Ausbildungsstaette)
admin.site.register(AusbildungsstaettenTags)
admin.site.register(Dienstposten)
admin.site.register(OccupationalGroupsDienstposten)
admin.site.register(AssociatedAusbildungsbloecke)
admin.site.register(PlanbareAusbildungsbloecke)
admin.site.register(Ausbildungsstelle)
admin.site.register(GenehmigteFachgebiete)

admin.site.register(Personen)
admin.site.register(PlanungsParameter)
admin.site.register(AllowedOrganisationUnits)
admin.site.register(AusbildungsPfade)
admin.site.register(OrganisationsGruppenPriorities)
admin.site.register(Unterbrechungszeiten)
admin.site.register(AusbildungsbloeckePfad)
admin.site.register(AusbildungserfordernissePfad)
admin.site.register(AusbildungsinhaltePfad)
admin.site.register(PlannedAusbildungsstelleByFachgebieteMonths)

admin.site.register(Zuweisungen)
admin.site.register(DienstpostenZuweisungen)
admin.site.register(AusbildungsstellenZuweisungen)

admin.site.register(Parameter)
admin.site.register(ConsideredAusbildungstypen)