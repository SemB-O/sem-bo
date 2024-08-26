from django.contrib import admin
from .models import User, Occupation, Record, Procedure, Cid, ProcedureHasCid, ProcedureHasOccupation, ProcedureHasRecord, Plan, PlanPoint, PlanPointAvailability, FavoriteFolder, FavoriteProcedure

admin.site.register(User)
admin.site.register(Occupation)
admin.site.register(Record)
admin.site.register(Procedure)
admin.site.register(Cid)
admin.site.register(ProcedureHasCid)
admin.site.register(ProcedureHasOccupation)
admin.site.register(ProcedureHasRecord)
admin.site.register(PlanPoint)
admin.site.register(Plan)
admin.site.register(PlanPointAvailability)
admin.site.register(FavoriteFolder)
admin.site.register(FavoriteProcedure)
