from django.contrib import admin
from .models import User, Occupation, Record, Procedure, Cid, ProcedureHasCid, ProcedureHasOccupation, ProcedureHasRecord, Plan, PlanBenefit, PlanHasPlanBenefit, FavoriteProceduresFolder, FavoriteProceduresFolderHasProcedure, Competence, SigtapSyncHistory


@admin.register(Competence)
class CompetenceAdmin(admin.ModelAdmin):
    list_display = ('code', 'formatted_date', 'is_atemporal', 'year', 'month', 'created_at')
    list_filter = ('is_atemporal', 'year')
    search_fields = ('code', 'formatted_date', 'description')
    readonly_fields = ('is_atemporal', 'year', 'month', 'formatted_date', 'created_at', 'updated_at')
    ordering = ('-code',)
    
    fieldsets = (
        ('Informações da Competência', {
            'fields': ('code', 'formatted_date', 'is_atemporal')
        }),
        ('Data Detalhada', {
            'fields': ('year', 'month')
        }),
        ('Detalhes Adicionais', {
            'fields': ('description', 'created_at', 'updated_at')
        }),
    )


@admin.register(SigtapSyncHistory)
class SigtapSyncHistoryAdmin(admin.ModelAdmin):
    list_display = ('formatted_started_at', 'status', 'competence_code', 'files_processed', 'formatted_duration', 'triggered_by')
    list_filter = ('status', 'is_automatic', 'started_at')
    search_fields = ('competence_code', 'error_message')
    readonly_fields = (
        'started_at', 'completed_at', 'formatted_started_at', 'formatted_completed_at',
        'formatted_duration', 'duration_seconds', 'success_rate'
    )
    ordering = ('-started_at',)
    
    fieldsets = (
        ('Status da Sincronização', {
            'fields': ('status', 'started_at', 'completed_at', 'formatted_duration', 'success_rate')
        }),
        ('Informações da Competência', {
            'fields': ('competence_code',)
        }),
        ('Arquivos', {
            'fields': ('files_processed', 'files_total')
        }),
        ('Contadores', {
            'fields': ('procedures_count', 'occupations_count', 'cids_count', 'records_count', 'competences_synced'),
            'classes': ('collapse',)
        }),
        ('Detalhes da Execução', {
            'fields': ('triggered_by', 'is_automatic', 'error_message', 'details'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        # Não permite adicionar manualmente
        return False
    
    def has_delete_permission(self, request, obj=None):
        # Permite deletar históricos antigos
        return request.user.is_superuser


admin.site.register(User)
admin.site.register(Occupation)
admin.site.register(Record)
admin.site.register(Procedure)
admin.site.register(Cid)
admin.site.register(ProcedureHasCid)
admin.site.register(ProcedureHasOccupation)
admin.site.register(ProcedureHasRecord)
admin.site.register(PlanBenefit)
admin.site.register(Plan)
admin.site.register(PlanHasPlanBenefit)
admin.site.register(FavoriteProceduresFolder)
admin.site.register(FavoriteProceduresFolderHasProcedure)
