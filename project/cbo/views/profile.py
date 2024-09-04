from django.views import View
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
from django.contrib import messages
from ..forms import UserEditForm


@method_decorator(login_required(login_url='/login'), name='dispatch')
class ProfileView(View):
    template_name = 'front/profile.html'

    def get(self, request, *args, **kwargs):
        form = UserEditForm(instance=request.user)
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = UserEditForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Perfil atualizado com sucesso.')
            return redirect('profile')
        else:
            messages.error(request, 'Ocorreu um erro ao atualizar o perfil. Por favor, verifique os dados e tente novamente.')
            return render(request, self.template_name, {'form': form})
        