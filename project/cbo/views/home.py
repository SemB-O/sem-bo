from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import ListView
from ..models import Procedure, Record, FavoriteProceduresFolder


@method_decorator(login_required(login_url='/login'), name='dispatch')
class Home(ListView):
    model = Procedure
    template_name = 'front/home.html'
    context_object_name = 'procedures'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['records'] = Record.objects.all()
        context['request'] = self.request

        user = self.request.user
        context['user'] = user
        context['favorite_folders'] = FavoriteProceduresFolder.objects.filter(user=user)

        return context

    @method_decorator(login_required(login_url='/login'))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)