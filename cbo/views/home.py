from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import ListView
from django.shortcuts import redirect
from ..models import Procedure, Record, FavoriteProceduresFolder
from .occupation import get_active_occupation


@method_decorator(login_required(login_url='/login'), name='dispatch')
class Home(ListView):
    model = Procedure
    template_name = 'front/home.html'
    context_object_name = 'procedures'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            # Users with multiple occupations must pick one before accessing home
            if request.user.occupations.count() > 1 and not request.session.get('active_occupation_code'):
                return redirect('select_occupation')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['records'] = Record.objects.all()
        context['request'] = self.request

        user = self.request.user
        context['user'] = user
        context['favorite_folders'] = FavoriteProceduresFolder.objects.filter(user=user)
        context['active_occupation'] = get_active_occupation(self.request)

        return context