from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views import View
from django.utils.decorators import method_decorator
from django.db.models import Count, Q
from django.http import JsonResponse
from django.core.management import call_command
from django.core.cache import cache
from cbo.models import Plan, PlanBenefit, Procedure, Occupation, Cid, User, Competence, SigtapSyncHistory
import threading


def is_superuser(user):
    return user.is_superuser


def admin_required(view_class):
    return method_decorator([login_required, user_passes_test(is_superuser)], name='dispatch')(view_class)


@admin_required
class AdminDashboardView(View):
    template_name = 'admin/dashboard.html'

    def get(self, request):
        # Busca última sincronização bem-sucedida do histórico
        last_sync = SigtapSyncHistory.get_last_successful_sync()
        
        if last_sync:
            last_sync_date = last_sync.formatted_started_at
            last_sync_month = last_sync.competence_code
            if last_sync_month and len(last_sync_month) == 6:
                # Formata YYYYMM para MM/YYYY
                last_sync_month = f"{last_sync_month[4:6]}/{last_sync_month[:4]}"
        else:
            # Fallback para cache (backward compatibility)
            last_sync_month = cache.get('sigtap_last_sync_month', 'Nunca')
            last_sync_date = cache.get('sigtap_last_sync_date', 'Nunca')
            
            # Formata a data se existir
            if last_sync_date != 'Nunca':
                from django.utils.dateparse import parse_datetime
                sync_datetime = parse_datetime(last_sync_date)
                if sync_datetime:
                    last_sync_date = sync_datetime.strftime('%d/%m/%Y às %H:%M')
        
        # Busca a última competência real (não atemporal) do modelo Competence
        latest_competence_obj = Competence.get_latest_real_competence()
        
        if latest_competence_obj:
            formatted_competence = latest_competence_obj.formatted_date
            latest_competence_raw = latest_competence_obj.code
        else:
            formatted_competence = 'Não disponível'
            latest_competence_raw = None
        
        context = {
            'total_plans': Plan.objects.count(),
            'total_benefits': PlanBenefit.objects.count(),
            'total_procedures': Procedure.objects.count(),
            'total_occupations': Occupation.objects.count(),
            'total_cids': Cid.objects.count(),
            'total_users': User.objects.count(),
            'active_plans': Plan.objects.filter(is_active=True).count(),
            'recent_plans': Plan.objects.order_by('-id')[:5],
            'sigtap_last_sync_month': last_sync_month,
            'sigtap_last_sync_date': last_sync_date,
            'latest_competence': formatted_competence,
            'latest_competence_raw': latest_competence_raw,
            'last_sync_history': last_sync,  # Objeto completo para mais detalhes
        }
        return render(request, self.template_name, context)


@admin_required
class PlanListView(View):
    template_name = 'admin/plan_list.html'

    def get(self, request):
        plans = Plan.objects.annotate(
            benefit_count=Count('benefits')
        ).order_by('-id')
        
        search = request.GET.get('search', '')
        if search:
            plans = plans.filter(
                Q(name__icontains=search) | Q(description__icontains=search)
            )
        
        context = {'plans': plans, 'search': search}
        return render(request, self.template_name, context)


@admin_required
class PlanCreateView(View):
    template_name = 'admin/plan_form.html'

    def get(self, request):
        context = {
            'benefits': PlanBenefit.objects.filter(is_active=True),
            'action': 'Criar'
        }
        return render(request, self.template_name, context)

    def post(self, request):
        try:
            plan = Plan.objects.create(
                name=request.POST.get('name'),
                max_occupations=request.POST.get('max_occupations'),
                description=request.POST.get('description'),
                price=request.POST.get('price'),
                is_active=request.POST.get('is_active') == 'on'
            )
            
            self._add_benefits_to_plan(plan, request)
            messages.success(request, f'Plano "{plan.name}" criado com sucesso!')
            return redirect('admin-plan-list')
        except Exception as e:
            messages.error(request, f'Erro ao criar plano: {str(e)}')
            return redirect('admin-plan-create')

    def _add_benefits_to_plan(self, plan, request):
        for benefit_id in request.POST.getlist('benefits'):
            benefit = PlanBenefit.objects.get(id=benefit_id)
            available = request.POST.get(f'benefit_available_{benefit_id}') == 'on'
            plan.add_benefit(benefit, available=available)


@admin_required
class PlanEditView(View):
    template_name = 'admin/plan_form.html'

    def get(self, request, pk):
        plan = get_object_or_404(Plan, pk=pk)
        benefit_availability = {
            assoc.plan_benefit_id: assoc.available 
            for assoc in plan.plan_benefits.all()
        }
        
        context = {
            'plan': plan,
            'benefits': PlanBenefit.objects.filter(is_active=True),
            'plan_benefit_ids': list(plan.benefits.values_list('id', flat=True)),
            'benefit_availability': benefit_availability,
            'action': 'Editar'
        }
        return render(request, self.template_name, context)

    def post(self, request, pk):
        plan = get_object_or_404(Plan, pk=pk)
        
        try:
            plan.name = request.POST.get('name')
            plan.max_occupations = request.POST.get('max_occupations')
            plan.description = request.POST.get('description')
            plan.price = request.POST.get('price')
            plan.is_active = request.POST.get('is_active') == 'on'
            plan.save()
            
            plan.plan_benefits.all().delete()
            PlanCreateView()._add_benefits_to_plan(plan, request)
            
            messages.success(request, f'Plano "{plan.name}" atualizado com sucesso!')
            return redirect('admin-plan-list')
        except Exception as e:
            messages.error(request, f'Erro ao atualizar plano: {str(e)}')
            return redirect('admin-plan-edit', pk=pk)


@admin_required
class PlanDeleteView(View):
    def post(self, request, pk):
        plan = get_object_or_404(Plan, pk=pk)
        plan_name = plan.name
        plan.delete()
        messages.success(request, f'Plano "{plan_name}" excluído com sucesso!')
        return redirect('admin-plan-list')


@admin_required
class BenefitListView(View):
    template_name = 'admin/benefit_list.html'

    def get(self, request):
        benefits = PlanBenefit.objects.annotate(
            plan_count=Count('plans')
        ).order_by('-id')
        
        search = request.GET.get('search', '')
        if search:
            benefits = benefits.filter(
                Q(name__icontains=search) | Q(description__icontains=search)
            )
        
        context = {'benefits': benefits, 'search': search}
        return render(request, self.template_name, context)


@admin_required
class BenefitCreateView(View):
    template_name = 'admin/benefit_form.html'

    def get(self, request):
        return render(request, self.template_name, {'action': 'Criar'})

    def post(self, request):
        try:
            benefit = PlanBenefit.objects.create(
                name=request.POST.get('name'),
                description=request.POST.get('description'),
                icon=request.POST.get('icon', ''),
                is_active=request.POST.get('is_active') == 'on'
            )
            messages.success(request, f'Benefício "{benefit.name}" criado com sucesso!')
            return redirect('admin-benefit-list')
        except Exception as e:
            messages.error(request, f'Erro ao criar benefício: {str(e)}')
            return redirect('admin-benefit-create')


@admin_required
class BenefitEditView(View):
    template_name = 'admin/benefit_form.html'

    def get(self, request, pk):
        benefit = get_object_or_404(PlanBenefit, pk=pk)
        return render(request, self.template_name, {'benefit': benefit, 'action': 'Editar'})

    def post(self, request, pk):
        benefit = get_object_or_404(PlanBenefit, pk=pk)
        
        try:
            benefit.name = request.POST.get('name')
            benefit.description = request.POST.get('description')
            benefit.icon = request.POST.get('icon', '')
            benefit.is_active = request.POST.get('is_active') == 'on'
            benefit.save()
            
            messages.success(request, f'Benefício "{benefit.name}" atualizado com sucesso!')
            return redirect('admin-benefit-list')
        except Exception as e:
            messages.error(request, f'Erro ao atualizar benefício: {str(e)}')
            return redirect('admin-benefit-edit', pk=pk)


@admin_required
class BenefitDeleteView(View):
    def post(self, request, pk):
        benefit = get_object_or_404(PlanBenefit, pk=pk)
        benefit_name = benefit.name
        benefit.delete()
        messages.success(request, f'Benefício "{benefit_name}" excluído com sucesso!')
        return redirect('admin-benefit-list')


@admin_required
class AdminUploadSigtapView(View):
    template_name = 'admin/upload_sigtap.html'

    def get(self, request):
        # Busca última sincronização bem-sucedida do histórico
        last_sync = SigtapSyncHistory.get_last_successful_sync()
        
        if last_sync:
            last_sync_date = last_sync.formatted_started_at
            last_sync_month = last_sync.competence_code
            if last_sync_month and len(last_sync_month) == 6:
                # Formata YYYYMM para MM/YYYY
                last_sync_month = f"{last_sync_month[4:6]}/{last_sync_month[:4]}"
        else:
            # Fallback para cache (backward compatibility)
            last_sync_month = cache.get('sigtap_last_sync_month', 'Nunca')
            last_sync_date = cache.get('sigtap_last_sync_date', 'Nunca')
            
            # Formata a data se existir
            if last_sync_date != 'Nunca':
                from django.utils.dateparse import parse_datetime
                sync_datetime = parse_datetime(last_sync_date)
                if sync_datetime:
                    last_sync_date = sync_datetime.strftime('%d/%m/%Y às %H:%M')
        
        # Busca a última competência real (não atemporal) do modelo Competence
        latest_competence_obj = Competence.get_latest_real_competence()
        
        if latest_competence_obj:
            formatted_competence = latest_competence_obj.formatted_date
        else:
            formatted_competence = 'Não disponível'
        
        # Busca histórico de sincronizações
        sync_history = SigtapSyncHistory.objects.order_by('-started_at')[:10]
        
        context = {
            'total_procedures': Procedure.objects.count(),
            'total_occupations': Occupation.objects.count(),
            'total_cids': Cid.objects.count(),
            'sigtap_last_sync_date': last_sync_date,
            'latest_competence': formatted_competence,
            'sync_history': sync_history,
        }
        
        return render(request, self.template_name, context)

    def post(self, request):
        import time
        import logging
        from django.db import transaction
        from ..process_files import DataImporter

        logger = logging.getLogger(__name__)
        files = request.FILES.getlist('arquivos_txt')

        if not files:
            messages.error(request, 'Nenhum arquivo selecionado.')
            return redirect('admin-upload-sigtap')

        FILE_IMPORTERS = {
            'tb_procedimento': DataImporter.import_procedure_data,
            'tb_ocupacao': DataImporter.import_occupation_data,
            'tb_registro': DataImporter.import_record_data,
            'tb_cid': DataImporter.import_cid_data,
            'rl_procedimento_cid': DataImporter.import_procedure_has_cid_data,
            'rl_procedimento_ocupacao': DataImporter.import_procedure_has_occupation_data,
            'rl_procedimento_registro': DataImporter.import_procedure_has_record_data,
            'tb_descricao': DataImporter.import_description_data,
        }

        start_time = time.time()
        logger.info("Starting SIGTAP file upload from admin panel")

        try:
            with transaction.atomic():
                for file in files:
                    file_start = time.time()
                    logger.info(f"Processing: {file.name}")

                    for file_type, importer in FILE_IMPORTERS.items():
                        if file_type in file.name:
                            importer(file)
                            break

                    logger.info(f"Processed {file.name} in {time.time() - file_start:.2f}s")

            logger.info(f"Upload completed in {time.time() - start_time:.2f}s")
            messages.success(request, f'{len(files)} arquivo(s) SIGTAP processado(s) com sucesso!')
            return redirect('admin-dashboard')
            
        except Exception as e:
            logger.error(f"Upload error: {str(e)}")
            messages.error(request, f'Erro ao processar arquivos: {str(e)}')
            return redirect('admin-upload-sigtap')


@admin_required
class SyncSigtapNowView(View):
    """View para sincronização manual instantânea da SIGTAP"""
    
    def post(self, request):
        import json
        
        # Verifica se é uma confirmação de sobrescrita
        try:
            body = json.loads(request.body)
            allow_overwrite = body.get('allow_overwrite', False)
        except:
            allow_overwrite = False
        
        # Limpa progresso anterior
        cache.delete('sigtap_sync_progress')
        
        def run_sync():
            """Executa o comando em thread separada"""
            try:
                if allow_overwrite:
                    call_command('sync_sigtap', allow_overwrite=True)
                else:
                    call_command('sync_sigtap')
            except Exception as e:
                cache.set('sigtap_sync_progress', {
                    'step': 0,
                    'message': f'Erro: {str(e)}',
                    'percentage': 0
                }, timeout=3600)
        
        # Inicia sincronização em background
        thread = threading.Thread(target=run_sync, daemon=True)
        thread.start()
        
        return JsonResponse({'status': 'started'})


@admin_required
class SyncSigtapProgressView(View):
    """View para retornar o progresso da sincronização"""
    
    def get(self, request):
        progress = cache.get('sigtap_sync_progress', {
            'step': 0,
            'message': 'Aguardando início...',
            'percentage': 0
        })
        return JsonResponse(progress)


@admin_required
class SigtapStatsView(View):
    """View para retornar estatísticas detalhadas da SIGTAP"""
    
    def get(self, request):
        from django.db.models import Max, Min, Count
        from cbo.models import Record
        
        # Busca competências de cada tabela
        procedure_stats = Procedure.objects.aggregate(
            latest=Max('competence_date'),
            oldest=Min('competence_date'),
            total=Count('id')
        )
        
        occupation_stats = Occupation.objects.aggregate(
            total=Count('id')
        )
        
        cid_stats = Cid.objects.aggregate(
            total=Count('id')
        )
        
        record_stats = Record.objects.aggregate(
            latest=Max('competence_date'),
            total=Count('id')
        )
        
        # Formata competências
        def format_competence(comp):
            if comp and len(comp) == 6:
                return f"{comp[4:6]}/{comp[:4]}"
            return 'N/A'
        
        data = {
            'procedures': {
                'total': procedure_stats['total'],
                'latest_competence': format_competence(procedure_stats['latest']),
                'oldest_competence': format_competence(procedure_stats['oldest']),
            },
            'occupations': {
                'total': occupation_stats['total'],
            },
            'cids': {
                'total': cid_stats['total'],
            },
            'records': {
                'total': record_stats['total'],
                'latest_competence': format_competence(record_stats['latest']),
            },
        }
        
        
        return JsonResponse(data)


@admin_required
class UserListView(View):
    """View para listagem e gerenciamento de usuários"""
    template_name = 'admin/user_list.html'

    def get(self, request):
        users = User.objects.select_related('plan').prefetch_related('occupations').order_by('-id')
        
        # Filtros
        search = request.GET.get('search', '')
        plan_filter = request.GET.get('plan', '')
        verified_filter = request.GET.get('verified', '')
        active_filter = request.GET.get('active', '')
        
        if search:
            users = users.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(email__icontains=search) |
                Q(CPF__icontains=search) |
                Q(telephone__icontains=search)
            )
        
        if plan_filter:
            users = users.filter(plan_id=plan_filter)
        
        if verified_filter:
            users = users.filter(email_verified=(verified_filter == 'true'))
        
        if active_filter:
            users = users.filter(is_active=(active_filter == 'true'))
        
        # Estatísticas
        total_users = User.objects.count()
        verified_users = User.objects.filter(email_verified=True).count()
        active_users = User.objects.filter(is_active=True).count()
        users_with_plan = User.objects.filter(plan__isnull=False).count()
        
        # Lista de planos para o filtro
        plans = Plan.objects.all().order_by('name')
        
        context = {
            'users': users,
            'plans': plans,
            'search': search,
            'plan_filter': plan_filter,
            'verified_filter': verified_filter,
            'active_filter': active_filter,
            'total_users': total_users,
            'verified_users': verified_users,
            'active_users': active_users,
            'users_with_plan': users_with_plan,
        }
        return render(request, self.template_name, context)


@admin_required
class UserDetailView(View):
    """View para detalhes de um usuário específico"""
    
    def get(self, request, pk):
        user = get_object_or_404(User.objects.select_related('plan').prefetch_related('occupations'), pk=pk)
        
        # Busca pastas de favoritos do usuário
        from cbo.models import Folder
        folders = Folder.objects.filter(user=user).prefetch_related('procedures').order_by('-id')
        
        # Serializa os dados do usuário
        user_data = {
            'id': user.id,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'CPF': user.CPF,
            'telephone': user.telephone,
            'date_of_birth': str(user.date_of_birth) if user.date_of_birth else None,
            'occupational_registration': user.occupational_registration,
            'is_active': user.is_active,
            'email_verified': user.email_verified,
            'is_superuser': user.is_superuser,
            'plan': {
                'name': user.plan.name,
                'description': user.plan.description
            } if user.plan else None,
            'occupations': [
                {'name': occ.name, 'code': occ.code}
                for occ in user.occupations.all()
            ]
        }
        
        # Serializa pastas
        folders_data = [
            {
                'id': folder.id,
                'name': folder.name,
                'procedures_count': folder.procedures.count()
            }
            for folder in folders
        ]
        
        context = {
            'user_obj': user_data,
            'folders': folders_data,
        }
        
        return JsonResponse(context)


@admin_required
class UserToggleActiveView(View):
    """View para ativar/desativar usuário"""
    
    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        user.is_active = not user.is_active
        user.save()
        
        status = 'ativado' if user.is_active else 'desativado'
        messages.success(request, f'Usuário {user.get_full_name()} foi {status} com sucesso!')
        
        return redirect('admin-user-list')


@admin_required
class UserDeleteView(View):
    """View para deletar usuário"""
    
    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        user_name = user.get_full_name()
        user.delete()
        
        messages.success(request, f'Usuário {user_name} foi deletado com sucesso!')
        return redirect('admin-user-list')
