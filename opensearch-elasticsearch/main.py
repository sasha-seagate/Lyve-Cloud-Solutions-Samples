from flask import Flask, render_template, jsonify, request, send_file, redirect, flash, url_for, make_response, Response, stream_with_context
from flask_cors import CORS, cross_origin
from flask_apscheduler import APScheduler
from jinja2  import TemplateNotFound

#import gc
import glob
import importlib
import io
import logging
import os
import pathlib
#import pickle
#import shutil
import sys
import warnings
#import zipfile
import multiprocessing
import concurrent.futures
import threading

import datetime
import dateutil
import time

import json
import pandas as pd

#import hashlib
#import requests
import secrets
import socket
#import urllib

#import helpers.config_manager as config
from helpers.config_manager import cfg as service_config
import helpers.s3 as s3
import helpers.utils
import job.executor
from destination import elk_connector
from setting.my_settings import *

import enlighten

# ---- Service Imformation ----
APP_TITLE       = 'Lyve Cloud: Log Gatway for OpenSearch/ElasticSearch'
SERVICE_NAME    = 'lyve-log-gateway-elk-opensearch'
SERVICE_VERSION = '2023.04.01.1a'
SERVICE_CONTACT = 'thanit.karnthak@seagate.com'
SERVER_NAME     = 'localhost'
HOST_NAME       = socket.gethostname()
HOST_ADDR       = socket.gethostbyname(HOST_NAME)


warnings.filterwarnings('ignore')
app = Flask(__name__, static_folder='static', static_url_path='/static')
cors = CORS(app, resources={r"/api/*": {"origins": "*"}})
scheduler = APScheduler()

app.config['TASK_SCH']         = scheduler
app.config['SECRET_KEY']       = secrets.token_urlsafe(16)
app.config['SERVICE_NAME']     = SERVICE_NAME
app.config['LAST_UP_DATETIME'] = datetime.datetime.now()
app.config['TESTING']          = False
logging.getLogger('werkzeug').disabled = False
os.environ['WERKZEUG_RUN_MAIN'] = 'false'

scheduler.api_enabled = True
scheduler.init_app(app)
scheduler.start()


##   -------------------------------
##   System Services
##   -------------------------------
def system_health_check(config, skip_listing_file=True):
    from destination import elk_connector

    # Connect to S3 Lyve Cloud
    bucket_name = config.get('lyvecloud.log_bucket')

    print('Connecting to Lyve Cloud... ', end='')
    s3conn = s3.connect()
    if s3conn is not None:
        print('OK')

        print('Listing Bucket on Lyve Cloud... ')
        s3.list_bucket(conn=s3conn)

        if not skip_listing_file:
            print()
            print('-' * 80)
            print('Lising Files on Lyve Cloud...')
            s3.list_file(conn=s3conn, bucket=bucket_name, deep_search=False)
    else:
        print('Unable to connect to S3 Server')

    print()
    print('-' * 80)
    for dst in config.get('destination'):
        print(f'Connecting to: {dst}')
        if dst in ['elasticsearch', 'opensearch',]:
            client = elk_connector.Elastic_Connector(distro_name=dst, config=config)
            client._connect()
            resp = client._info()

            if isinstance(resp, dict):
                for k, v in resp.items():
                    print('{attr:32s}: {value}'.format(attr=k, value=v))
            else:
                print('Response: ', '-- invalid --')

            client._close()

    print('---- End ----')


def system_log_init():
    app.config['HISTORY_TRACKING'] = helpers.utils.system_history_log_init()


##   -------------------------------
##   Scheduler Tasks
##   -------------------------------
def Scheduler_Log_Downloader(jobs_config=None, run_mode='auto'):
    event_date = datetime.datetime.now()

    scheduler  = app.config['TASK_SCH']
    try:
        scheduler.remove_job('Scheduler_Log_Downloader')
    except:
        pass

    print('timestamp: {timestamp}'.format(timestamp=event_date.astimezone().isoformat()))
    app.config['HISTORY_TRACKING'] = helpers.utils.system_history_log_init()
    job.executor.ingress_helper(app_config=app.config,
        last_n_days   = LAST_X_DAYS,
        last_n_hours  = LAST_X_HOURS,
        last_n_mins   = LAST_X_MINS,
    )

    scheduler.add_job(func=Scheduler_Log_Downloader, trigger='cron', hour=CRON_TRIGGER_HOUR, minute=CRON_TRIGGER_MINUTE, timezone=TIMEZONE, jitter=120, args=[jobs_config], id='Scheduler_Log_Downloader', max_instances=1, coalesce=True, replace_existing=True)


def init_scheduler_jobs():
    """
    APScheduler has three types of triggers:
        - date
        - interval
        - cron
        interval and cron repeat forever, date is a one-shot on a given date.
    """

    job_id = 'Scheduler_Log_Downloader'
    next_run_date = datetime.datetime.now() + datetime.timedelta(days=0, hours=0, minutes=0, seconds=5)
    scheduler.add_job(func=Scheduler_Log_Downloader, trigger='date', run_date=next_run_date,  kwargs={'run_mode': 'Initialized'}, id=job_id, max_instances=1, coalesce=True, replace_existing=True)


#########################
###   Dev you sevice  ###
#########################
# Helper - Extract current page name from request
def get_segment(request):
    try:
        segment = request.path.split('/')[-1]
        if segment == '':
            segment = 'index'
        return segment
    except:
        return None


@app.context_processor
def inject_variables():
    # Use a template context processor to pass variables to every template.
    ret = {
        'now'        : datetime.datetime.now().astimezone().isoformat(),
        'app_title'  : APP_TITLE,
        'app_version': SERVICE_VERSION,
        'endpoint_link': '',
    }

    if 'LAST_UP_DATETIME' in app.config:
        ret.update({
            'service_uptime': str(datetime.datetime.now() - app.config.get('LAST_UP_DATETIME', datetime.datetime.now())),
        })

    link_template = """
        <a href="{url}" class="list-group-item list-group-item-action">
        <div class="d-flex justify-content-between">
        <h5 class="mb-1">{destination} Dashboard</h5>
        <small>Tenant: {tenant}</small>
        </div>
        <p class="mb-1">URL: {url}</p>
        </a>
    """

    list_group = []
    for idx, dst in enumerate(service_config.get('destination')):
        allow_data_ingression = service_config.get(f'{dst}.allow_data_ingression', False)
        dashboard_url = service_config.get(f'{dst}.dashboard_url', '')
        tenant = service_config.get(f'{dst}.tenant', '')

        x = link_template.format(destination=dst.upper(), url=dashboard_url, tenant=tenant)
        x = "\n".join([line.strip() for line in x.splitlines()[1:]])

        list_group.append(x)

    ret['endpoint_link'] = '\n'.join(list_group)

    return ret


##   -------------------------------
##   End Point
##   -------------------------------
@app.route('/', methods=['GET',], defaults={'path': 'index.html'})
@app.route('/<path>')
def index(path):
    try:
        # Detect the current page
        segment = get_segment(request)

        # Serve the file (if exists) from app/templates/FILE.html
        return render_template(template_name_or_list=path, segment=segment)
    except TemplateNotFound:
        return render_template(template_name_or_list='page-404.html'), 404


@app.route('/info', methods=['GET',])
def info():
    ret = {
        'SERVICE_NAME'        : SERVICE_NAME,
        'SERVICE_VERSION'     : SERVICE_VERSION,
        'SERVICE_CONTACT'     : SERVICE_CONTACT,
        'SERVICE_UPTIME'      : None,
        'EVENT_DATE'          : datetime.datetime.now().astimezone().isoformat(),
        'HOST_ADDR'           : request.environ.get('HTTP_HOST').split(':')[0],
        'HOST_NAME'           : request.environ.get('SERVER_NAME'),
        'HOST_PORT'           : request.environ.get('HTTP_HOST').split(':')[1],
        'REMOTE_ADDR'         : request.environ.get('REMOTE_ADDR'),
        'REMOTE_PORT'         : request.environ.get('REMOTE_PORT'),
        'REQUEST_METHOD'      : request.environ.get('REQUEST_METHOD'),
        'REQUEST_URI'         : request.environ.get('REQUEST_URI'),
        'REQUEST_URL_SCHEME'  : request.environ.get('wsgi.url_scheme'),
        'USER_AGENT'          : request.environ.get('HTTP_USER_AGENT'),
        }

    if 'LAST_UP_DATETIME' in app.config:
        ret.update({
            'SERVICE_UPTIME': str(datetime.datetime.now() - app.config.get('LAST_UP_DATETIME', datetime.datetime.now())),
        })

    return jsonify(ret)


@app.route('/api/v1/health', methods=['GET',], strict_slashes=False)
@cross_origin()
def api_health_check():
    action    = request.args.get('action', 'view')

    return redirect(url_for('info'))



if __name__ == '__main__':
    if os.name == 'nt':
        os.system('cls')
        os.system('cls')
    else:
        os.system('clear')
        os.system('clear')

    print('-' * 80)
    print('--- Lyve Logs Ingression to ElasticSearch/OpenSearch ---')
    print('-' * 80)

    system_log_init()

    if SERVICE_MODE:
        print('-' * 80)
        print('---- SERVICE_MODE = True ----')
        print('-' * 80)

        if CONFIG_CHECK:
            print('Listing all data destination...')
            for idx, dst in enumerate(service_config.get('destination')):
                allow_data_ingression = service_config.get(f'{dst}.allow_data_ingression', False)
                print(f'{idx}: --> {dst} | IS_ALLOW_DATA_INGRESSION: {allow_data_ingression}')

            print()
            system_health_check(config=service_config)

        if INIT_ISM or INIT_DATA_STREAM:
            for dst in service_config.get('destination'):
                if dst in ['elasticsearch', 'opensearch',]:
                    client = elk_connector.Elastic_Connector(distro_name=dst, config=service_config)
                    client._connect()
                    client._info()

                    if INIT_ISM:
                        print('--- Index State Management  ---')
                        client.manage_ism(run_mode='UPDATE', debug=DEBUG_FLAG)

                    if INIT_DATA_STREAM:
                        print('--- Data Stream Index/Data Type Mapping  ---')
                        client.manage_template(run_mode='UPDATE', debug=DEBUG_FLAG)

                    client._close()
                    print('--- Initialized ISM and Data Stream Index Template completed. ---')
    else:
        for idx, dst in enumerate(service_config.get('destination')):
            allow_data_ingression = service_config.get(f'{dst}.allow_data_ingression', False)

            if not allow_data_ingression:
                print(f'*** Warning *** {idx}: --> {dst} | IS_ALLOW_DATA_INGRESSION: {allow_data_ingression}')

        if RUN_AS_SERVICE:
            print('---- Run as a Scheduler Service ----')

            if ENABLE_SCHEDULE_RUN:
                init_scheduler_jobs()

            app.config['WinDebug'] = True
            app.run(host='0.0.0.0', port=5001, debug=DEBUG_FLAG, use_reloader=False) # set debug=True for auto reloading.
        else:
            print('---- Run as a standalone application (on-premise) ----')
            job.executor.ingress_helper(app_config=app.config,
                t_last=START_DATETIME,
                t_now=STOP_DATETIME,
            )
