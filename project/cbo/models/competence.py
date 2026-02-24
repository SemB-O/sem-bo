from django.db import models
from ._base import BaseModel


class Competence(BaseModel):
    """
    Modelo para armazenar as competências (mês/ano de vigência) do SIGTAP.
    
    Tipos de competências:
    - Reais: formato YYYYMM (ex: 202601 = Janeiro/2026)
    - Atemporais: formato com 9999 no final (ex: 099999, 249999) ou apenas 9999
      Indicam vigência permanente/sem data de fim
    """
    
    code = models.CharField(
        max_length=6,
        unique=True,
        db_index=True,
        help_text="Código da competência no formato YYYYMM ou com 9999 para vigências atemporais"
    )
    
    is_atemporal = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Indica se a competência é atemporal (vigência permanente)"
    )
    
    year = models.IntegerField(
        null=True,
        blank=True,
        help_text="Ano da competência (extraído do código quando aplicável)"
    )
    
    month = models.IntegerField(
        null=True,
        blank=True,
        help_text="Mês da competência (1-12, quando aplicável)"
    )
    
    formatted_date = models.CharField(
        max_length=10,
        null=True,
        blank=True,
        help_text="Data formatada MM/YYYY para exibição"
    )
    
    description = models.TextField(
        blank=True,
        help_text="Descrição adicional da competência"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'competence'
        verbose_name = 'Competência'
        verbose_name_plural = 'Competências'
        ordering = ['-code']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['is_atemporal']),
            models.Index(fields=['-year', '-month']),
        ]

    def __str__(self):
        if self.is_atemporal:
            return f"{self.code} (Atemporal)"
        return f"{self.formatted_date or self.code}"

    def save(self, *args, **kwargs):
        """
        Processa o código da competência e extrai informações automáticas.
        """
        if self.code:
            # Verifica se é atemporal (termina com 9999 ou é apenas 9999)
            self.is_atemporal = self.code.endswith('9999') or self.code == '9999'
            
            if not self.is_atemporal and len(self.code) == 6:
                # Extrai ano e mês de competências reais (YYYYMM)
                try:
                    self.year = int(self.code[:4])
                    self.month = int(self.code[4:6])
                    self.formatted_date = f"{self.code[4:6]}/{self.code[:4]}"
                except (ValueError, IndexError):
                    # Se falhar, marca como atemporal
                    self.is_atemporal = True
            elif not self.is_atemporal and len(self.code) == 4:
                # Formato antigo MMAA (ex: 0180, 0280)
                try:
                    self.month = int(self.code[:2])
                    self.year = 1900 + int(self.code[2:4])
                    self.formatted_date = f"{self.code[:2]}/{self.year}"
                except (ValueError, IndexError):
                    self.is_atemporal = True
        
        super().save(*args, **kwargs)

    @classmethod
    def get_latest_real_competence(cls):
        """
        Retorna a competência real (não atemporal) mais recente.
        """
        return cls.objects.filter(is_atemporal=False).order_by('-code').first()

    @classmethod
    def get_all_real_competences(cls):
        """
        Retorna todas as competências reais ordenadas da mais recente para a mais antiga.
        """
        return cls.objects.filter(is_atemporal=False).order_by('-code')

    @classmethod
    def get_atemporal_competences(cls):
        """
        Retorna todas as competências atemporais.
        """
        return cls.objects.filter(is_atemporal=True).order_by('code')

    @classmethod
    def create_from_code(cls, code):
        """
        Cria ou retorna uma competência existente a partir do código.
        """
        competence, created = cls.objects.get_or_create(code=code)
        return competence
