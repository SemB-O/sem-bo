from django.db import models
from ._base import BaseModel


class SigtapSyncHistory(BaseModel):
    """
    Histórico de sincronizações com o SIGTAP.
    Registra cada execução do comando de sincronização.
    """
    
    STATUS_CHOICES = [
        ('in_progress', 'Em Progresso'),
        ('success', 'Sucesso'),
        ('failed', 'Falha'),
        ('partial', 'Parcial'),
    ]
    
    started_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Data e hora de início da sincronização"
    )
    
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Data e hora de conclusão da sincronização"
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='in_progress',
        db_index=True,
        help_text="Status da sincronização"
    )
    
    competence_code = models.CharField(
        max_length=6,
        null=True,
        blank=True,
        help_text="Código da competência sincronizada (YYYYMM)"
    )
    
    files_processed = models.IntegerField(
        default=0,
        help_text="Número de arquivos processados"
    )
    
    files_total = models.IntegerField(
        default=0,
        help_text="Número total de arquivos esperados"
    )
    
    procedures_count = models.IntegerField(
        default=0,
        help_text="Total de procedimentos após sincronização"
    )
    
    occupations_count = models.IntegerField(
        default=0,
        help_text="Total de ocupações após sincronização"
    )
    
    cids_count = models.IntegerField(
        default=0,
        help_text="Total de CIDs após sincronização"
    )
    
    records_count = models.IntegerField(
        default=0,
        help_text="Total de registros após sincronização"
    )
    
    competences_synced = models.IntegerField(
        default=0,
        help_text="Total de competências sincronizadas"
    )
    
    error_message = models.TextField(
        blank=True,
        help_text="Mensagem de erro, se houver"
    )
    
    details = models.JSONField(
        default=dict,
        blank=True,
        help_text="Detalhes adicionais da sincronização (arquivos, logs, etc.)"
    )
    
    duration_seconds = models.FloatField(
        null=True,
        blank=True,
        help_text="Duração da sincronização em segundos"
    )
    
    triggered_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sigtap_syncs',
        help_text="Usuário que iniciou a sincronização (se manual)"
    )
    
    is_automatic = models.BooleanField(
        default=False,
        help_text="Indica se foi uma sincronização automática"
    )

    class Meta:
        db_table = 'sigtap_sync_history'
        verbose_name = 'Histórico de Sincronização SIGTAP'
        verbose_name_plural = 'Históricos de Sincronização SIGTAP'
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['-started_at']),
            models.Index(fields=['status']),
            models.Index(fields=['competence_code']),
        ]

    def __str__(self):
        status_display = self.get_status_display()
        date_str = self.started_at.strftime('%d/%m/%Y %H:%M')
        return f"{status_display} - {date_str}"

    @property
    def formatted_started_at(self):
        """Retorna data de início formatada para exibição."""
        return self.started_at.strftime('%d/%m/%Y às %H:%M')

    @property
    def formatted_completed_at(self):
        """Retorna data de conclusão formatada para exibição."""
        if self.completed_at:
            return self.completed_at.strftime('%d/%m/%Y às %H:%M')
        return None

    @property
    def formatted_duration(self):
        """Retorna duração formatada."""
        if self.duration_seconds:
            minutes = int(self.duration_seconds // 60)
            seconds = int(self.duration_seconds % 60)
            if minutes > 0:
                return f"{minutes}m {seconds}s"
            return f"{seconds}s"
        return None

    @property
    def success_rate(self):
        """Calcula taxa de sucesso baseada em arquivos processados."""
        if self.files_total > 0:
            return (self.files_processed / self.files_total) * 100
        return 0

    def mark_as_completed(self, status='success', error_message=''):
        """Marca a sincronização como concluída."""
        from django.utils import timezone
        
        self.completed_at = timezone.now()
        self.status = status
        
        if error_message:
            self.error_message = error_message
        
        # Calcula duração
        if self.started_at and self.completed_at:
            delta = self.completed_at - self.started_at
            self.duration_seconds = delta.total_seconds()
        
        self.save()

    def update_counts(self):
        """Atualiza contadores com valores atuais do banco."""
        from cbo.models import Procedure, Occupation, Cid, Record, Competence
        
        self.procedures_count = Procedure.objects.count()
        self.occupations_count = Occupation.objects.count()
        self.cids_count = Cid.objects.count()
        self.records_count = Record.objects.count()
        self.competences_synced = Competence.objects.count()
        self.save()

    @classmethod
    def get_last_successful_sync(cls):
        """Retorna a última sincronização bem-sucedida."""
        return cls.objects.filter(status='success').first()

    @classmethod
    def get_last_sync(cls):
        """Retorna a última sincronização (qualquer status)."""
        return cls.objects.first()

    @classmethod
    def get_sync_statistics(cls):
        """Retorna estatísticas gerais de sincronizações."""
        from django.db.models import Count, Avg, Sum
        
        stats = cls.objects.aggregate(
            total=Count('id'),
            successful=Count('id', filter=models.Q(status='success')),
            failed=Count('id', filter=models.Q(status='failed')),
            avg_duration=Avg('duration_seconds'),
            total_files=Sum('files_processed'),
        )
        
        return stats
