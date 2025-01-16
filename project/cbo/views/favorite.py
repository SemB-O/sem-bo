from django.http import JsonResponse
from django.db import IntegrityError
from django.views.generic import ListView
from django.contrib import messages
from django.views import View
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.decorators import method_decorator
from ..models import FavoriteProcedure, Procedure, FavoriteFolder, Record
from ..forms.favorite import FavoriteFolderForm


@method_decorator(login_required(login_url='/login'), name='dispatch')
class FavoriteView(ListView):
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
class FavoriteProceduresListView(View):
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
            procedures_list = procedures_list.filter(
                (Q(name__icontains=query) | Q(procedure_code__icontains=query))
            )

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


@method_decorator(login_required(login_url='/login'), name='dispatch')
class ToggleFavoriteView(View):
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


class CreateFolderView(View):
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
    