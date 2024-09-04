from django.views import View
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.shortcuts import render


@method_decorator(login_required(login_url='/login'), name='dispatch')
class ChatView(View):
    template_name = 'front/chat.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)