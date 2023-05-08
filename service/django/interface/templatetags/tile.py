from datetime import timedelta
from django import template
from django.utils import timezone

'''

****
NOTE
****

# The admin interface is under development.
# This code is temporarily commented out
# to allow the general server to start.

from control.models import Event, Job, JobStatus, JobStatusType
from migrations.core.jobloop import JOB_CHECKIN_GRACE_SECONDS
from migrations.core.jobloop import JOB_CHECKIN_INTERVAL_SECONDS

TICKER_EVENTS = 3

register = template.Library()


@register.inclusion_tag('admin/tile/job.html')
def job_tile():
    jobs = {}
    now = timezone.localtime(timezone.now())
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    seven_days_ago = today-timedelta(days=7)
    tomorrow = today + timedelta(days=1)
    jobstatuscategories = {}
    results = JobStatusType.objects.all()
    for type in results:
        jobstatuscategories[type.id] = type.category
    results = (Job.objects.filter(
        last_jobstatus__create_date__range=(seven_days_ago, tomorrow))
        .prefetch_related('last_jobstatus'))
    jobs['count'] = results.count()
    if results:
        jobs['status'] = {}
        for job in results:
            if job.last_jobstatus:
                last_status = jobstatuscategories[job.last_jobstatus.status_id]
                if (last_status == 'inprogress' and
                        (job.last_jobstatus.create_date <
                         timezone.now() -
                         timedelta(seconds=JOB_CHECKIN_INTERVAL_SECONDS +
                                   JOB_CHECKIN_GRACE_SECONDS))):
                    last_status = 'stuck'
                if last_status not in jobs['status']:
                    jobs['status'][last_status] = 0
                jobs['status'][last_status] = jobs['status'][last_status] + 1
    return {'checkdate': timezone.now(),
            'jobs': jobs,
            'seven_days_ago': str(seven_days_ago),
            'tomorrow': str(tomorrow)}


@register.inclusion_tag('admin/tile/minions.html')
def minion_tile():
    checkdate = timezone.now()
    jobstatus = None
    minions = {}
    try:
        job = (Job.objects.filter(last_jobstatus_type__name='completed',
                                  type__codename='monitor_minions')
               .latest('execution_date'))
    except Job.DoesNotExist:
        job = None
    if job and job is not None:
        jobstatus = JobStatus.objects.filter(status__name='completed',
                                             job__id=job.id)
        jobstatus = jobstatus[0]
        checkdate = jobstatus.create_date
        minions['status'] = {}
        minions['status']['down'] = {}
        minions['status']['up'] = {}
        minions['workers'] = {}
        if 'minions' in jobstatus.memo:
            minions['status']['down'] = jobstatus.memo['minions']['down']
            minions['status']['up'] = jobstatus.memo['minions']['up']
        if 'workers' in jobstatus.memo:
            minions['workers'] = jobstatus.memo['workers']
        pass
    return {'checkdate': checkdate,
            'jobstatus': jobstatus,
            'minions': minions}


@register.inclusion_tag('admin/tile/ticker.html')
def ticker_tile():
    events = {}
    try:
        events = Event.objects.all().order_by('-create_date')[:TICKER_EVENTS]
    except IndexError:
        events = Event.objects.all().order_by('-create_date')
    return {'events': events}
'''
