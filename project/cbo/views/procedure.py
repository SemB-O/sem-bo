from django.views.generic import DetailView, ListView
from django.views import View
from django.db.models import Q
from django.http import JsonResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.urls import reverse
from django.shortcuts import render
from ..models import Procedure, FavoriteFolder, FavoriteProcedure, Record


@method_decorator(login_required(login_url='/login'), name='dispatch')
class DetailView(DetailView):
    model = Procedure
    template_name = 'front/procedure_detail.html'
    context_object_name = 'procedure'
    slug_field = 'procedure_code'
    slug_url_kwarg = 'procedure_code'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        procedure = context['procedure']
        related_occupations = procedure.procedures_has_occupation.filter(
            occupation__in=user.occupations.all()
        )
        procedure.related_occupations_names = [relation.occupation.name for relation in related_occupations]
        
        user = self.request.user
        favorites = procedure.is_favorite(user)
        
        context['procedure'] = procedure
        context['favorite_folders'] = FavoriteFolder.objects.filter(user=user)
        context['favorite'] = favorites
        context['procedure_urls'] = {procedure.procedure_code: reverse('procedure_detail', args=[procedure.procedure_code])}
        return context


@method_decorator(login_required(login_url='/login'), name='dispatch')
class ListView(ListView):
    template_name = 'front/procedure_list.html'
    procedures_per_page = 30

    def get(self, request, *args, **kwargs):
        user_occupations = request.user.occupations.all()

        query = request.GET.get('q', '')

        record_name = request.GET.get('record_name', '')

        procedures_list = Procedure.objects.filter(
            (Q(name__icontains=query) | Q(procedure_code__icontains=query))
            & Q(procedures_has_occupation__occupation__in=user_occupations)
        )

        if record_name != 'all' and record_name:
            procedures_list = procedures_list.filter(procedures_has_record__record__name=record_name)

        procedures_list = procedures_list.prefetch_related('procedures_has_record__record')

        page = request.GET.get('page', 1)
        paginator = Paginator(procedures_list, self.procedures_per_page)

        try:
            procedures = paginator.page(page)
        except PageNotAnInteger:
            procedures = paginator.page(1)
        except EmptyPage:
            procedures = paginator.page(paginator.num_pages)

        records = Record.objects.all()

        user = request.user

        favorite_procedures_codes = FavoriteProcedure.objects.filter(user=user).values_list('procedure__procedure_code', flat=True)
        favorite_folders = FavoriteFolder.objects.filter(user=user)

        for procedure in procedures:
            procedure.favorite = procedure.procedure_code in favorite_procedures_codes

            if user.is_authenticated and user.occupations.exists():
                related_occupations = procedure.procedures_has_occupation.filter(
                    occupation__in=user.occupations.all()
                )
                procedure.related_occupations_names = [relation.occupation.name for relation in related_occupations]

        context = {
            'procedures': procedures,
            'has_next': procedures.has_next(),
            'record_name': record_name,
            'records': records,
            'favorite': favorite_procedures_codes,
            'favorite_folders': favorite_folders,
        }
        
        return render(request, self.template_name, context)
    

@method_decorator(login_required(login_url='/login'), name='dispatch')
class LoadMoreView(View):
    procedures_per_page = 30

    def get(self, request, *args, **kwargs):
        user_occupations = request.user.occupations.all()

        query = request.GET.get('q')
        record_name = request.GET.get('record_name', '')  

        if query:
            procedures_list = Procedure.objects.filter(
                (Q(name__icontains=query) | Q(procedure_code__icontains=query))
                & Q(procedures_has_occupation__occupation__in=user_occupations)
            ).order_by('name')

            if record_name != 'all':
                procedures_list = procedures_list.filter(procedures_has_record__record__name=record_name)

            procedures_list = procedures_list.prefetch_related('procedures_has_record__record')

        else:
            procedures_list = Procedure.objects.filter(
                Q(procedures_has_occupation__occupation__in=user_occupations)
            ).prefetch_related('procedures_has_record__record').order_by('name')

            if record_name != 'all' and record_name:
                procedures_list = procedures_list.filter(procedures_has_record__record__name=record_name)

            procedures_list = procedures_list.prefetch_related('procedures_has_record__record')

        page = request.GET.get('page', 1)
        paginator = Paginator(procedures_list, self.procedures_per_page)

        try:
            procedures = paginator.page(page)
        except PageNotAnInteger:
            procedures = paginator.page(1)
        except EmptyPage:
            procedures = paginator.page(paginator.num_pages)

        data = []
        has_more_results = procedures.has_next()

        user = request.user

        for procedure in procedures:
            if user.is_authenticated and user.occupations.exists():
                related_occupations = procedure.procedures_has_occupation.filter(
                    occupation__in=user.occupations.all()
                )
                procedure.related_occupations_names = [relation.occupation.name for relation in related_occupations]

            data.append({
                'name': procedure.name,
                'code': procedure.procedure_code,
                'records_names': procedure.get_records_names(),
                'has_more_results': has_more_results,
                'favorite': procedure.is_favorite(self.request.user),
                'occupations_of_users': procedure.related_occupations_names
            })

        return JsonResponse({'procedures': data})
    
    
@method_decorator(login_required(login_url='/login'), name='dispatch')
class ProcedureAutocomplete(View):
    def get(self, request):
        term = request.GET.get('term', '')
        user = request.user
        occupations = user.occupations.all()

        procedures = Procedure.objects.filter(
            procedures_has_occupation__occupation__in=occupations,
            name__icontains=term
        )[:10]

        results = [{'id': proc.procedure_code, 'text': proc.name} for proc in procedures]
        return JsonResponse({'results': results})
