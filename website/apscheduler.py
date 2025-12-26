import os
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore, register_events
from django_apscheduler.models import DjangoJobExecution
from django.core.management import call_command
import threading

logger = logging.getLogger(__name__)

_scheduler: BackgroundScheduler | None = None


def start():
    global _scheduler
    if _scheduler is not None:
        return

    # Start persistent Selenium watcher automatically if enabled
    if os.environ.get('UFALOFT_WATCH_ENABLED', '0') == '1':
        interval = os.environ.get('UFALOFT_WATCH_INTERVAL_MIN', '60')
        index_field = os.environ.get('UFALOFT_INDEX_FIELD', 'first_name')
        verbose = os.environ.get('UFALOFT_VERBOSE', '1')  # default verbose on
        headless = os.environ.get('UFALOFT_HEADLESS', '0')

        def run_watch():
            try:
                args = ['--interval-min', str(interval), '--index-field', index_field]
                if verbose == '1':
                    args.append('--verbose')
                if headless == '1':
                    args.append('--headless')
                logger.info(f'Starting UFALOFT watcher with args: {args}')
                call_command('ufaloft_watch', *args)
            except Exception as e:
                logger.exception('UFALOFT watcher stopped: %s', e)

        t = threading.Thread(target=run_watch, name='UfaloftWatcher', daemon=True)
        t.start()
        logger.info('UFALOFT watcher thread started')
    elif os.environ.get('UFALOFT_SCHEDULE_ENABLED', '0') != '1':
        logger.info('UFALOFT scheduler disabled. Set UFALOFT_SCHEDULE_ENABLED=1 to enable.')

    scheduler = BackgroundScheduler(timezone=os.environ.get('TZ', 'UTC'))
    scheduler.add_jobstore(DjangoJobStore(), 'default')

    def job_sync():
        try:
            call_command('sync_ufaloft_statuses')
        except Exception as e:
            logger.exception('UFALOFT sync failed: %s', e)

    scheduler.add_job(
        job_sync,
        'interval',
        id='ufaloft_sync_job',
        minutes=60,
        replace_existing=True,
        max_instances=1,
        coalesce=True,
        jobstore='default',
    )

    register_events(scheduler)
    scheduler.start()
    _scheduler = scheduler
    logger.info('UFALOFT scheduler started (every 60 minutes)')

