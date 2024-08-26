from django.shortcuts import render
from django.views import View
from .models import Procedure, Record, Occupation, FavoriteProcedure, User, Plan, FavoriteFolder, Cid
from .process_files import DataImporter
from django.shortcuts import redirect
from django.views.generic import ListView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import JsonResponse
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from .forms import EmailAuthenticationForm, UserRegistrationForm, UserEditForm, PasswordResetEmailForm, SetPasswordForm, FavoriteFolderForm, RecordMedicalForm
from django.views.generic import DetailView
from django.urls import reverse
from django.utils.translation import gettext
from django.http import HttpResponse
from django.views.generic import FormView
# from .utils import download_file_from_ftp, Scraper
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
import os
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import EmailMessage
from cbo.tokens import account_activation_token
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.shortcuts import render, redirect, get_object_or_404
import json
from django.conf import settings


# @method_decorator(login_required(login_url='/login'), name='dispatch')
class UploadFilesView(View):
    template_name = 'create/send_files.html'

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        arquivos = request.FILES.getlist('arquivos_txt')

        for arquivo in arquivos:
            if 'tb_procedimento' in arquivo.name:
                DataImporter.import_procedure_data(arquivo)
            elif 'tb_ocupacao' in arquivo.name:
                DataImporter.import_occupation_data(arquivo)
            elif 'tb_registro' in arquivo.name:
                DataImporter.import_record_data(arquivo)
            elif 'tb_cid' in arquivo.name:
                DataImporter.import_cid_data(arquivo)
            elif 'rl_procedimento_cid' in arquivo.name:
                DataImporter.import_procedure_has_cid_data(arquivo)
            elif 'rl_procedimento_ocupacao' in arquivo.name:
                DataImporter.import_procedure_has_occupation_data(arquivo)
            elif 'rl_procedimento_registro' in arquivo.name:
                DataImporter.import_procedure_has_record_data(arquivo)

        return redirect('home')


@method_decorator(login_required(login_url='/login'), name='dispatch')
class DownloadFilesView(View):
    template_name = 'download/download_files.html'

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        ftp_url = Scraper.get_last_download_link()
        if ftp_url:
            file_path_ftp = ''
            BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            DATA_DIR = os.path.join(BASE_DIR, 'temp_data')
            local_save_path = DATA_DIR
            download_file_from_ftp(ftp_url, file_path_ftp, local_save_path)

        return HttpResponse("Arquivo baixado com sucesso!")

    @method_decorator(login_required(login_url='/login'))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    

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
        context['favorite_folders'] = FavoriteFolder.objects.filter(user=user)

        return context

    @method_decorator(login_required(login_url='/login'))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)


@method_decorator(login_required(login_url='/login'), name='dispatch')
class SearchView(View):
    def get(self, request, *args, **kwargs):
        query = request.GET.get('q')
        record_name = request.GET.get('record_name')

        if query:
            user_occupations = request.user.occupations.all()

            procedures_list = Procedure.objects.filter(
                Q(name__icontains=query) &
                Q(procedures_has_occupation__occupation__in=user_occupations)
            ).select_related()

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
            user = request.user

            for procedure in procedures:
                if user.is_authenticated and user.occupations.exists():
                    related_occupations = procedure.procedures_has_occupation.filter(
                        occupation__in=user.occupations.all()
                    )
                    procedure.related_occupations_names = [relation.occupation.name for relation in related_occupations]

                data.append({
                    'code': procedure.procedure_code,
                    'name': procedure.name,
                    'records_names': procedure.get_records_names(),
                    'has_more_results': has_more_results,
                    'favorite': procedure.is_favorite(self.request.user),
                    'occupations_names': procedure.related_occupations_names,
                })

            return JsonResponse({'procedures': data})

    @method_decorator(login_required(login_url='/login'))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)


class UserLoginView(LoginView):
    template_name = 'front/login.html'
    authentication_form = EmailAuthenticationForm

    def form_valid(self, form):
        response = super().form_valid(form)
        return HttpResponseRedirect(reverse_lazy('home'))

    def form_invalid(self, form):
        response = super().form_invalid(form)
        messages.error(self.request, 'Credenciais inválidas. Tente novamente.')
        return HttpResponseRedirect(reverse_lazy('login'))


class LogoutView(LogoutView):
    next_page = reverse_lazy('login')


@method_decorator(login_required(login_url='/login'), name='dispatch')
class ChatView(View):
    template_name = 'front/chat.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)


@method_decorator(login_required(login_url='/login'), name='dispatch')
class ProcedureDetailView(DetailView):
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
class ProcedureListView(ListView):
    template_name = 'front/procedure_list.html'
    procedures_per_page = 30

    def get(self, request, *args, **kwargs):
        user_occupations = request.user.occupations.all()

        query = request.GET.get('q', '')

        record_name = request.GET.get('record_name', '')

        procedures_list = Procedure.objects.filter(
                Q(name__icontains=query) &
                Q(procedures_has_occupation__occupation__in=user_occupations)
            ).select_related()

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
class ProcedureFavoriteView(ListView):
    template_name = 'front/procedure_favorite.html'
    procedures_per_page = 30
    context_object_name = 'procedures'

    def get_queryset(self):
        user = self.request.user
        favorite_procedures_codes = FavoriteProcedure.objects.filter(user=user).values_list('procedure__procedure_code', flat=True)

        return Procedure.objects.filter(procedure_code__in=favorite_procedures_codes).order_by('-favoriteprocedure__created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        favorite_folders = FavoriteFolder.objects.filter(user=user)
        
        for folder in favorite_folders:
            folder.procedures = Procedure.objects.filter(
                favoriteprocedure__folder=folder,
                favoriteprocedure__deleted__isnull=True
            )

            for procedure in folder.procedures:
                if user.is_authenticated and user.occupations.exists():
                    related_occupations = procedure.procedures_has_occupation.filter(
                        occupation__in=user.occupations.all()
                    )
                    procedure.related_occupations_names = [relation.occupation.name for relation in related_occupations]

        context['records'] = Record.objects.all()
        context['favorite_folders'] = favorite_folders
        return context
    
    def post(self, request, *args, **kwargs):
        form = FavoriteFolderForm(request.POST)
        if form.is_valid():
            folder = form.save(commit=False)
            folder.user = request.user
            folder.save()
            messages.success(request, 'Pasta de favoritos criada com sucesso!')
        else:
            messages.error(request, 'Ocorreu um erro ao criar a pasta de favoritos.')
        
        return redirect(request.path_info)
    

@method_decorator(login_required(login_url='/login'), name='dispatch')
class ProcedureLoadMoreView(View):
    procedures_per_page = 30

    def get(self, request, *args, **kwargs):
        user_occupations = request.user.occupations.all()

        query = request.GET.get('q')
        record_name = request.GET.get('record_name', '')  

        if query:
            procedures_list = Procedure.objects.filter(
                Q(name__icontains=query) &
                Q(procedures_has_occupation__occupation__in=user_occupations)
            ).select_related().order_by('name')

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
    

class UserRegistrationView(View):
    template_name = 'create/register_user.html'

    def get(self, request, selected_plan, *args, **kwargs):
        form = UserRegistrationForm(initial={'plan': selected_plan}, use_required_attribute=False)
        occupations = Occupation.objects.all()

        plans = Plan.objects.all()
        plans_json = json.dumps(list(plans.values('id', 'name', 'max_occupations', 'description')))

        context = {
            'form': form,
            'occupations': occupations,
            'selected_plan': request.GET.get('selected_plan'),
            'plans_json': plans_json,
        }

        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        form = UserRegistrationForm(request.POST, use_required_attribute=False)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()

            selected_occupations = form.cleaned_data['occupation']
            for occupation in selected_occupations:
                user.occupations.add(occupation)
            user.save()

            default_folder, _ = FavoriteFolder.objects.get_or_create(
                user=user,
                name="Geral",
                description="Meus Favoritos"
            )

            self.activateEmail(request, user, form.cleaned_data.get('email'))

            return redirect('login')
        else:
            return render(request, self.template_name, {'form': form})
        
    def activateEmail(self, request, user, to_email):
        mail_subject = "Ativação da sua conta Sem B.O"
        message = render_to_string('email/email_verification.html', {
            'user': user.first_name,
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            'token': account_activation_token.make_token(user),
            'protocol': 'https' if request.is_secure() else 'http',
            'domain': settings.DOMAIN,
        })
        email = EmailMessage(mail_subject, message, to=[to_email])
        email.content_subtype = 'html' 
        if email.send():
            messages.success(request, f'Olá {user.first_name}, enviamos um email para {to_email}, por favor verifique-o para validar seu cadastro')
        else:
            messages.error(request, f'Tivemos um problema ao enviar a validação para seu email ({to_email}), por favor cheque se você digitou seu email corretamente!')
            

@method_decorator(login_required(login_url='/login'), name='dispatch')
class UserProfileView(View):
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
        

@method_decorator(login_required(login_url='/login'), name='dispatch')
class AddRemoveFavoriteView(View):
    def post(self, request, *args, **kwargs):
        procedure_id = request.POST.get('procedure_id')
        selected_folders_ids = [int(folder_id) for folder_id in request.POST.getlist('folders[]')]

        if procedure_id:
            user = request.user
            is_favorite = False
            
            FavoriteProcedure.objects.filter(
                user=user,
                procedure_id=procedure_id
            ).exclude(folder_id__in=selected_folders_ids).delete()

            favorite_folders = FavoriteProcedure.objects.filter(user=user, procedure_id=procedure_id)

            for folder_id in selected_folders_ids:
                try:
                    favorite, created = FavoriteProcedure.objects.get_or_create(
                        user=user,
                        procedure_id=procedure_id,
                        folder_id=folder_id
                    )
                    if created:
                        is_favorite = True
                except IntegrityError as e:
                    return JsonResponse({'error': str(e)}, status=400)
                
            return JsonResponse({'is_favorite': is_favorite})
        else:
            return JsonResponse({'error': 'Dados incompletos ou inválidos'}, status=400)


@method_decorator(login_required(login_url='/login'), name='dispatch')
class FavoriteProcedureListView(View):
    procedures_per_page = 30

    def get(self, request, *args, **kwargs):
        user = request.user

        favorite_procedures = FavoriteProcedure.objects.filter(user=user).values_list('procedure', flat=True)

        procedures_list = Procedure.objects.filter(
            Q(pk__in=favorite_procedures)
        ).prefetch_related('procedures_has_record__record')

        record_name = request.GET.get('record_name', '')

        if record_name != 'all' and record_name:
            procedures_list = procedures_list.filter(procedures_has_record__record__name=record_name)

        procedures_list = procedures_list.prefetch_related('procedures_has_record__record')

        query = request.GET.get('q')
        if query:
            procedures_list = procedures_list.filter(name__icontains=query)

        page = request.GET.get('page', 1)
        paginator = Paginator(procedures_list, self.procedures_per_page)

        try:
            procedures = paginator.page(page)
        except PageNotAnInteger:
            procedures = paginator.page(1)
        except EmptyPage:
            procedures = paginator.page(paginator.num_pages)

        favorite_folders = FavoriteFolder.objects.filter(user=user)
        data = []
        for folder in favorite_folders:
            folder_procedures = Procedure.objects.filter(favoriteprocedure__folder=folder)

            for procedure in folder_procedures:
                if user.is_authenticated and user.occupations.exists():
                    related_occupations = procedure.procedures_has_occupation.filter(
                        occupation__in=user.occupations.all()
                    )
                    procedure.related_occupations_names = [relation.occupation.name for relation in related_occupations]

                procedure_dict = {
                    'folder_id': folder.id,
                    'folder_name': folder.name,
                    'folder_description': folder.description,
                    'procedure_name': procedure.name,
                    'procedure_code': procedure.procedure_code,
                    'records_names': procedure.get_records_names(),
                    'favorite': True,
                    'occupations_of_users': procedure.related_occupations_names
                }

                data.append(procedure_dict)

        return JsonResponse({'procedures': data})


class PasswordResetRequestView(View):
    template_name = 'password_reset/email_password_reset.html'

    def get(self, request):
        form = PasswordResetEmailForm()
        return render(
            request=request,
            template_name=self.template_name,
            context={"form": form}
        )

    def post(self, request):
        form = PasswordResetEmailForm(request.POST)
        if form.is_valid():
            user_email = form.cleaned_data['email']
            associetad_user = get_user_model().objects.filter(Q(email=user_email)).first()
            if associetad_user:
                mail_subject = "Redefina sua senha Sem B.O"
                message = render_to_string('email/password_reset_email.html', {
                    'user': associetad_user.first_name,
                    'uid': urlsafe_base64_encode(force_bytes(associetad_user.pk)),
                    'token': account_activation_token.make_token(associetad_user),
                    'protocol': 'https' if request.is_secure() else 'http',
                    'domain': '192.168.0.108:8000'
                })
                email = EmailMessage(mail_subject, message, to=[associetad_user.email])
                email.content_subtype = 'html' 
                if email.send():
                    messages.success(request, f'Olá {associetad_user.first_name}, enviamos um email para {associetad_user.email} com as instruções para redefinir sua senha!')
                else:
                    messages.error(request, 'Seu email não consta no nosso sistema! <b>Por favor, digite um email válido!</b>')

            return redirect('login')
        

class PasswordResetConfirmView(View):
    template_name = 'password_reset/password_reset.html'

    def get(self, request, uidb64, token):
        User = get_user_model()
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
            form = SetPasswordForm(user)

            return render(
                request=request,
                template_name=self.template_name,
                context = {
                    "form": form,
                    "uidb64": uidb64,
                    "token": token,
                }
            )
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

    def post(self, request, uidb64, token):
        User = get_user_model()
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is not None and account_activation_token.check_token(user, token):
            form = SetPasswordForm(user, request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, 'Sua senha foi alterada com sucesso!')
                return redirect('login')
            else:
                for field, field_errors in form.errors.items():
                    for error in field_errors:
                       messages.error(request, gettext(error))
                return redirect('password_reset_confirm', uidb64=uidb64, token=token)
        else:
            messages.error(request, 'Esse link de redefinição de senha é inválido ou expirou.')
        return redirect('login')


class SelectPlanView(View):
    def get(self, request):
        order = ['Plano Essencial', 'Plano Essencial +', 'Plano Codificador/Faturista']
        plans = Plan.objects.all().order_by('name')
        plans_ordered = sorted(plans, key=lambda x: order.index(x.name) if x.name in order else len(order))

        return render(request, 'create/select_plan.html', {'plans': plans_ordered})

    def post(self, request):
        selected_plan_id = request.POST.get('selected_plan_id')
        redirect_url = reverse('register', kwargs={'selected_plan': selected_plan_id})
        return JsonResponse({'redirect_url': redirect_url})


class CreateFavoriteFolderView(View):
    def post(self, request):
        form = FavoriteFolderForm(request.POST)
        if form.is_valid():
            folder = form.save(commit=False)
            folder.user = request.user
            folder.save()
            return redirect('sucess-page')
        else:
            return render(request, self.template_name, {'form': form})
        

class CheckFavoriteView(View):
    def post(self, request, *args, **kwargs):
        procedure_id = request.POST.get('procedure_id')
        user = request.user

        if procedure_id:
            favorites = FavoriteProcedure.objects.filter(user=user, procedure_id=procedure_id)
            favorite_folders = []
            is_favorite = False

            for favorite in favorites:
                if favorite.folder:
                    favorite_folders.append(favorite.folder.id)
            
            if favorite_folders:
                is_favorite = True

            return JsonResponse({'is_favorite': is_favorite, 'favorite_folders': favorite_folders})
        else:
            return JsonResponse({'error': 'Dados incompletos ou inválidos'}, status=400)


class EditFolderView(View):
    def post(self, request, folder_id):
        folder = get_object_or_404(FavoriteFolder, id=folder_id)
        form = FavoriteFolderForm(request.POST, instance=folder)
        if form.is_valid():
            form.save()
            messages.success(request, 'Pasta de favoritos editada com sucesso')
            return redirect('procedure_favorite')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'Erro no campo {field}: {error}')
            return redirect('procedure_favorite')


class DeleteFolderView(View):
    def post(self, request, folder_id):
        folder = get_object_or_404(FavoriteFolder, id=folder_id)
        folder.delete()
        return JsonResponse({'message': 'Pasta de favoritos excluída com sucesso'}, status=200)
    

class MedicalRecordHomeView(View):
    template_name = 'front/medical_record_home.html'

    def get(self, request):
        occupations = request.user.occupations.all()
        form = RecordMedicalForm()
        context = {
            'form': form
        }
        
        return render(request, self.template_name, context)


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


class CidAutocomplete(View):
    def get(self, request):
        term = request.GET.get('term', '')
        user = request.user
        occupations = user.occupations.all()

        procedures = Procedure.objects.filter(
            procedures_has_occupation__occupation__in=occupations
        )

        cids = Cid.objects.filter(
            cids_has_procedure__procedure__in=procedures,
            name__icontains=term
        )[:10]

        results = [{'id': cid.cid_code, 'text': cid.name} for cid in cids]
        return JsonResponse({'results': results})


def activate(request, uidb64, token):
    User =  get_user_model()
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except:
        user = None

    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.email_verified = True
        user.save()

        email = 'rafaelpinheirodesigner@gmail.com'
        send_info_user_email(to_email=email)

        messages.success(request, 'Obrigado por confirmar seu email, sua conta está ativada!')
    else:
        messages.error(request, 'O link de ativação é inválido!')

    return redirect('login')

def send_info_user_email(to_email):
    mail_subject = "Novo usuário cadastrado!"
    message = render_to_string('email/info_user_email.html', {
        'count': User.objects.count(),
    })

    email = EmailMessage(mail_subject, message, to=[to_email])
    email.content_subtype = 'html' 
    email.send()