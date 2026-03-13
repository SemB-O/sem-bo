from django.views import View
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
from django.http import JsonResponse

SESSION_KEY = 'active_occupation_code'


def get_active_occupation(request):
    """
    Returns the currently active Occupation for the logged-in user.
    Reads from session; falls back to the user's single occupation when only one exists.
    Returns None if the user has no occupations.
    """
    user = request.user
    if not user.is_authenticated:
        return None

    occupation_code = request.session.get(SESSION_KEY)
    if occupation_code:
        occ = user.occupations.filter(occupation_code=occupation_code).first()
        if occ:
            return occ

    # Auto-select when there is exactly one occupation
    occupations = list(user.occupations.all())
    if len(occupations) == 1:
        request.session[SESSION_KEY] = occupations[0].occupation_code
        return occupations[0]

    return None


@method_decorator(login_required(login_url='/login'), name='dispatch')
class SelectOccupationView(View):
    template_name = 'front/select_occupation.html'

    def get(self, request, *args, **kwargs):
        occupations = request.user.occupations.all()

        # Users with a single occupation are sent straight to home
        if occupations.count() == 1:
            request.session[SESSION_KEY] = occupations.first().occupation_code
            return redirect('home')

        return render(request, self.template_name, {'occupations': occupations})

    def post(self, request, *args, **kwargs):
        occupation_code = request.POST.get('occupation_code')
        user_occupations = request.user.occupations.values_list('occupation_code', flat=True)

        if occupation_code and occupation_code in user_occupations:
            request.session[SESSION_KEY] = occupation_code

        return redirect('home')


@method_decorator(login_required(login_url='/login'), name='dispatch')
class SwitchOccupationView(View):
    """Clears the active occupation and sends the user back to the selection page."""

    def get(self, request, *args, **kwargs):
        # Only meaningful for users with more than one occupation
        if request.user.occupations.count() <= 1:
            return redirect('home')

        request.session.pop(SESSION_KEY, None)
        return redirect('select_occupation')
