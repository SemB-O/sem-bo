from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.db.models import Q
from django.views import View
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import JsonResponse
from ..models import Procedure
from .occupation import get_active_occupation


@method_decorator(login_required(login_url='/login'), name='dispatch')
class SearchView(View):
    def get(self, request, *args, **kwargs):
        query = request.GET.get('q')
        record_name = request.GET.get('record_name')

        if query:
            active_occupation = get_active_occupation(request)
            occupation_filter = [active_occupation] if active_occupation else []

            procedures_list = Procedure.objects.filter(
                (Q(name__icontains=query) | Q(procedure_code__icontains=query))
                & Q(procedures_has_occupation__occupation__in=occupation_filter)
            )

            if record_name and record_name != 'all':
                procedures_list = procedures_list.filter(procedures_has_record__record__name=record_name)

            procedures_list = procedures_list.prefetch_related('procedures_has_record__record')

            page = request.GET.get('page', 1)
            paginator = Paginator(procedures_list, 20)

            try:
                procedures = paginator.page(page)
            except PageNotAnInteger:
                procedures = paginator.page(1)
            except EmptyPage:
                procedures = paginator.page(paginator.num_pages)

            data = []
            has_more_results = procedures.has_next()

            for procedure in procedures:
                data.append({
                    'code': procedure.procedure_code,
                    'name': procedure.name,
                    'records_names': procedure.get_records_names(),
                    'has_more_results': has_more_results,
                    'favorite': procedure.is_favorite(self.request.user),
                })

            return JsonResponse({'procedures': data})

    @method_decorator(login_required(login_url='/login'))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)