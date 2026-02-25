"""
Views para pesquisa rápida SIGTAP no dashboard admin
"""
from django.views.generic import ListView
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.db.models import Q, Count
from django.core.paginator import Paginator
from ..models import Procedure, Cid, Occupation


@method_decorator(staff_member_required, name='dispatch')
class ProcedureSearchView(ListView):
    """View para pesquisa de procedimentos SIGTAP"""
    model = Procedure
    template_name = 'admin/sigtap_search/procedures.html'
    context_object_name = 'procedures'
    paginate_by = 50
    
    def get_queryset(self):
        queryset = Procedure.objects.all()
        search_term = self.request.GET.get('search', '').strip()
        
        if search_term:
            queryset = queryset.filter(
                Q(procedure_code__icontains=search_term) |
                Q(name__icontains=search_term)
            )
        
        return queryset.select_related().prefetch_related(
            'procedures_has_occupation__occupation',
            'procedures_has_record__record'
        ).order_by('procedure_code')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_term'] = self.request.GET.get('search', '')
        context['total_results'] = self.get_queryset().count()
        return context


@method_decorator(staff_member_required, name='dispatch')
class CidSearchView(ListView):
    """View para pesquisa de CIDs"""
    model = Cid
    template_name = 'admin/sigtap_search/cids.html'
    context_object_name = 'cids'
    paginate_by = 50
    
    def get_queryset(self):
        queryset = Cid.objects.all()
        search_term = self.request.GET.get('search', '').strip()
        
        if search_term:
            queryset = queryset.filter(
                Q(cid_code__icontains=search_term) |
                Q(name__icontains=search_term)
            )
        
        return queryset.order_by('cid_code')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_term'] = self.request.GET.get('search', '')
        context['total_results'] = self.get_queryset().count()
        return context


@method_decorator(staff_member_required, name='dispatch')
class OccupationSearchView(ListView):
    """View para pesquisa de ocupações (CBO)"""
    model = Occupation
    template_name = 'admin/sigtap_search/occupations.html'
    context_object_name = 'occupations'
    paginate_by = 50
    
    def get_queryset(self):
        queryset = Occupation.objects.all()
        search_term = self.request.GET.get('search', '').strip()
        
        if search_term:
            queryset = queryset.filter(
                Q(occupation_code__icontains=search_term) |
                Q(name__icontains=search_term)
            )
        
        # Anota quantidade de procedimentos relacionados
        queryset = queryset.annotate(
            procedure_count=Count('occupations_has_procedure')
        )
        
        return queryset.order_by('occupation_code')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_term'] = self.request.GET.get('search', '')
        context['total_results'] = self.get_queryset().count()
        return context
