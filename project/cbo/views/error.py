from django.views.generic.base import TemplateView


class Error404View(TemplateView):
    template_name = 'errors/404.html'
    