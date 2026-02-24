from apscheduler.schedulers.background import BackgroundScheduler
from django.core.management import call_command
from django.core.cache import cache
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def should_sync_sigtap():
    """
    Verifica se deve tentar sincronizar SIGTAP baseado em:
    - Período de atualização: dia 3 a 18 de cada mês
    - Se já sincronizou a versão do mês atual
    """
    now = datetime.now()
    current_day = now.day
    current_month = now.strftime('%Y%m')  # Ex: 202601
    
    # Verifica se está no período de atualização (dia 3 a 18)
    if not (3 <= current_day <= 18):
        logger.info(f'📅 Fora do período de atualização (dia {current_day}). Aguardando dias 3-18.')
        return False
    
    # Verifica se já sincronizou este mês
    last_sync_month = cache.get('sigtap_last_sync_month')
    
    if last_sync_month == current_month:
        logger.info(f'✅ SIGTAP do mês {current_month} já sincronizado. Aguardando próximo mês.')
        return False
    
    logger.info(f'🔄 Iniciando tentativa de sincronização SIGTAP para {current_month}')
    return True


def sync_sigtap_job():
    """Job agendado para sincronizar SIGTAP automaticamente"""
    try:
        if not should_sync_sigtap():
            return
        
        logger.info('🤖 Iniciando sincronização automática SIGTAP...')
        call_command('sync_sigtap')
        
        # Marca que sincronizou este mês
        current_month = datetime.now().strftime('%Y%m')
        cache.set('sigtap_last_sync_month', current_month, timeout=None)
        
        logger.info(f'✅ Sincronização automática SIGTAP concluída para {current_month}')
    except Exception as e:
        logger.error(f'❌ Erro na sincronização automática SIGTAP: {str(e)}')


def start():
    """Inicia o scheduler de tarefas automáticas"""
    scheduler = BackgroundScheduler()
    
    # Sincronização SIGTAP diária durante período de atualização (dias 3-18)
    # Executa todo dia às 3h da manhã
    scheduler.add_job(
        sync_sigtap_job,
        'cron',
        day='3-18',  # Apenas entre dia 3 e 18
        hour=3,
        minute=0,
        id='sigtap_sync_monthly',
        replace_existing=True,
        max_instances=1
    )
    
    scheduler.start()
    logger.info('📅 Scheduler iniciado: SIGTAP será sincronizado diariamente (dias 3-18) às 3h')
