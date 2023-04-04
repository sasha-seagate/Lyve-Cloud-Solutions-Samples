# Copyright (c) 2021 Seagate Technology LLC and/or its Affiliates

import os
import io
import socket
import time
import datetime
import dateutil
import pandas as pd
import multiprocessing
import concurrent.futures
import enlighten
from tqdm import tqdm

import helpers.utils
import helpers.s3 as s3
from helpers.config_manager import cfg as SERVICE_CONFIG

from parsers.console import ParserConsole
from parsers.audit import ParserAudit
from parsers.iam import ParserIAM
from parsers.history import ParserEngineStats
from typing import Optional
from destination import elk_connector


def log_console_handler(log):
    ret = {}
    parser = ParserConsole(config=SERVICE_CONFIG, debug=False)
    parser.load(buffer=log['body'], filename=log['key'], filehash=log.get('etag', ''))

    for dst in SERVICE_CONFIG.get('destination'):
        ret[dst] = parser.sendTo(dst)
    return ret


def log_audit_handler(log):
    ret = {}
    parser = ParserAudit(config=SERVICE_CONFIG, debug=False)
    parser.load(buffer=log['body'], filename=log['key'], filehash=log.get('etag', ''))

    for dst in SERVICE_CONFIG.get('destination'):
        ret[dst] = parser.sendTo(dst)

    return ret


def log_iam_handler(log):
    ret = {}
    parser = ParserIAM(config=SERVICE_CONFIG, debug=False)
    parser.load(buffer=log['body'], filename=log['key'], filehash=log.get('etag', ''))

    for dst in SERVICE_CONFIG.get('destination'):
        ret[dst] = parser.sendTo(dst)
    return ret


def log_parser_engine_handler(logs):
    ret = {}
    parser = ParserEngineStats(config=SERVICE_CONFIG, logs=logs)

    for dst in SERVICE_CONFIG.get('destination'):
        if dst in ['elasticsearch', 'opensearch',]:
            ret[dst] = parser.sendTo(dst)
    return ret


def parse_logs(s3_objs_meta, debug=False):
    start_time = time.perf_counter()
    event_date = s3_objs_meta.get('event_date', datetime.datetime.now().astimezone().isoformat())
    ret = {
        '@timestamp'             : event_date,
        # 'EVENT_DATE'             : event_date,
        'EVENT_TYPE'             : '',
        'EXCEPTION_STATUS'       : '',
        'EXCEPTION_CODE'         : '',
        'EXCEPTION_REASON'       : '',
        'LAST_FAIL_ID'           : '',
        'LAST_FAIL_ROW'          : None,
        'LAST_FAIL_DESC'         : '',
        'PROCESS_TIME'           : None,
        'FILE_NAME'              : s3_objs_meta['key'],
        'FILE_SIZE_COMPRESSED'   : s3_objs_meta['size'],
        'FILE_SIZE_UNCOMPRESSED' : None,
        'FILE_LAST_MODIFIED'     : s3_objs_meta['last_modified'],
        'FILE_HASH'              : s3_objs_meta['etag'],
        'NUM_SAMPLES'            : None,
        'SUCCESS_CNT'            : None,
        'ERROR_CNT'              : None,

        'HOST_ADDR'              : None, #socket.gethostname(),
        'HOST_NAME'              : socket.gethostbyname(socket.gethostname()),
        'HOST_PORT'              : None,
        'REMOTE_ADDR'            : None,
        'REMOTE_PORT'            : None,
        'REQUEST_METHOD'         : None,
        'REQUEST_URI'            : None,
        'REQUEST_URL_SCHEME'     : None,
        'USER_AGENT'             : None,
        'SEND_TO_ELK'            : False,
    }

    if debug: print('--> seq_no: {seq_no} -- step 1.1-incomming'.format(seq_no=s3_objs_meta['seq_no']))
    if not isinstance(s3_objs_meta['body'], (io.BytesIO, io.BufferedReader)):
        ret.update({
            'EXCEPTION_STATUS' : 'FAIL',
            'EXCEPTION_REASON' : 'Not a BytesIO',
        })
        return ret

    full_filepath = s3_objs_meta['key'].split("/")
    if len(full_filepath) == 2:
        resp = None
        filename = full_filepath[1]
        log_type = filename.split('-')[0]
        ret.update({
            'EVENT_TYPE'          : log_type,
            'FILE_SIZE_COMPRESSED'   : s3_objs_meta['size'],
            'FILE_SIZE_UNCOMPRESSED' : s3_objs_meta['body'].__sizeof__(),
        })

        if debug: print('--> seq_no: {seq_no} -- step 1.2-preprocess'.format(seq_no=s3_objs_meta['seq_no']))
        if filename.startswith('Console'):
            resp = log_console_handler(log=s3_objs_meta)
        elif filename.startswith('S3'):
            if debug: print('--> seq_no: {seq_no} -- {filename} | step 1.3-audit-preprocess'.format(seq_no=s3_objs_meta['seq_no'], filename=s3_objs_meta['key']))
            resp = log_audit_handler(log=s3_objs_meta)
            if debug: print('--> seq_no: {seq_no} -- step 1.4-audit-resp: {resp}'.format(seq_no=s3_objs_meta['seq_no'], resp=resp))
        elif filename.startswith('IAM'):
            resp = log_iam_handler(log=s3_objs_meta)
        else:
            ret.update({
                'EXCEPTION_STATUS' : 'FAIL',
                'EXCEPTION_REASON' : 'Unknown Log Type. Only API Audit, Console, and IAM are supported.',
            })

        if debug: print('--> seq_no: {seq_no} -- {filename} | step 1.5-elk-history'.format(seq_no=s3_objs_meta['seq_no'], filename=s3_objs_meta['key']))

        if resp:
            for target, value in resp.items():
                if target in ['elasticsearch', 'opensearch',]:
                    if isinstance(value, dict):
                        ret.update({
                            'EXCEPTION_STATUS'    : 'PASS',
                            'EXCEPTION_CODE'      : '0',
                            'EXCEPTION_REASON'    : 'PASS',
                            'INDEX_NAME'          : value.get('INDEX_NAME'),
                            'LAST_FAIL_ID'        : value.get('LAST_FAIL_ID'),
                            'LAST_FAIL_ROW'       : value.get('LAST_FAIL_ROW'),
                            'LAST_FAIL_DESC'      : value.get('LAST_FAIL_DESC'),
                            'USER_AGENT'          : target,
                            'PROCESS_TIME'        : value.get('PROCESS_TIME'),
                            'NUM_SAMPLES'         : value.get('NUM_SAMPLES'),
                            'SUCCESS_CNT'         : value.get('SUCCESS_CNT'),
                            'ERROR_CNT'           : value.get('ERROR_CNT'),
                            'SEND_TO_ELK'         : value.get('SEND_TO_ELK'),
                        })
                    else:
                        ret.update({
                            'EXCEPTION_STATUS'    : 'FAIL',
                            'EXCEPTION_CODE'      : '-1',
                            'EXCEPTION_REASON'    : 'RESPOSNE DATA IS NOT A DICTIONARY',
                            'INDEX_NAME'          : '',
                            'LAST_FAIL_ID'        : '',
                            'LAST_FAIL_ROW'       : None,
                            'LAST_FAIL_DESC'      : '',
                            'USER_AGENT'          : target,
                            'PROCESS_TIME'        : None,
                            'NUM_SAMPLES'         : None,
                            'SUCCESS_CNT'         : None,
                            'ERROR_CNT'           : None,
                            'SEND_TO_ELK'         : False
                        })
                    break
    else:
        ret.update({
            'EXCEPTION_STATUS'     : 'FAIL',
            'EXCEPTION_REASON'     : 'Invalid filename',
        })

    ret.update({
        'PROCESS_TIME'          : time.perf_counter() - start_time,
    })

    # -- Send Parser Log Result to ELK
    resp = log_parser_engine_handler(logs=[ret])

    if debug: print('--> seq_no: {seq_no} -- step 1.6-outgoing: {resp}'.format(seq_no=s3_objs_meta['seq_no'], resp=ret))
    return ret


def download_and_parse_objets(q, bucket, s3_objs_meta, *args, **kwargs):
    # Multiprocessing Proxy Namespace
    g                  = kwargs.get('g', None)
    seq_no             = kwargs.get('seq_no', None)

    skip_history_check = kwargs.get('skip_history_check', False)
    skip_download      = kwargs.get('skip_download', False)

    params = {
        'event_date'   : datetime.datetime.now().astimezone().isoformat(),
        'seq_no'       : seq_no,

        'key'          : s3_objs_meta['Key'],
        'size'         : s3_objs_meta['Size'],
        'last_modified': s3_objs_meta['LastModified'],
        'etag'         : s3_objs_meta['ETag'].strip('"'),
        'status'       : '',
        'body'         : None,
        'g'            : g,
    }

    if not skip_history_check:
        if not g.df.empty:
            if len(g.df[(g.df['FILE_NAME'] == s3_objs_meta['Key']) & (g.df['EXCEPTION_STATUS'].isin(['pass', 'PASS',]))].index):
                # params['status'] = 'downloaded'
                skip_download = True

    if not skip_download:
        # --Downloading log section --
        file_buffer = io.BytesIO()
        conn = s3.connect()
        conn.download_fileobj(bucket, s3_objs_meta['Key'], file_buffer)
        file_buffer.seek(0)
        params['body'] = file_buffer
        params['status'] = 'new'

        # -- Parsing log section --
        resp = parse_logs(s3_objs_meta=params, debug=False)
        params['history'] = resp
        del params['body']
    else:
        params['status'] = 'skipped'

    # -- Tracking history section --
    try:
        q.put(params, block=True)
    except Exception as e:
        print(f'Exception!, s3-download_objets, seq_no: {seq_no}, meta:, {s3_objs_meta}, error: {e}')

    return params


def log_recevicer(q, results, *args, **kwargs):
    while True:
        try:
            if not q.empty():
                params = q.get(block=False)
                seq_no = params.get('seq_no', 1)
                status = params.get('status', 'skipped')
                g      = params.get('g', None)
                resp   = params.get('history', {})

                if status == 'new':
                    results.append(resp)
                    g.df = pd.concat(objs=[g.df, pd.DataFrame.from_dict([resp])], axis=0, ignore_index=True)

                if (seq_no % 10) == 0:
                    g.df.to_csv(path_or_buf=os.path.join('logs', 'history.csv'), index=False)
        except Exception as e:
            print(f'Exception!, log_recevicer, seq_no: {seq_no}, meta:, {params}, error: {e}', flush=True)


def run(date_range, df_history, folder_prefix, debug=False):
    start_time_overall = time.perf_counter()
    event_date         = datetime.datetime.now()
    exception_status = ''
    exception_code   = ''
    exception_reason = ''

    ret = {
        '@timestamp'          : event_date.astimezone().isoformat(),
        'EXCEPTION_STATUS'    : '',
        'EXCEPTION_CODE'      : '',
        'EXCEPTION_REASON'    : '',
        'PROCESS_TIME'        : None,
        'FOLDER_PREFIX'       : folder_prefix,
    }

    if not date_range:
        exception_status = 'FAIL'
        exception_code   = '-1'
        exception_reason = 'Not specify datetime in date_range.'
        ret.update(
            {
                'EXCEPTION_STATUS'    : exception_status,
                'EXCEPTION_CODE'      : exception_code,
                'EXCEPTION_REASON'    : exception_reason,
            }
        )
        return ret

    # Connect to S3 Lyve Cloud
    s3conn = s3.connect()
    bucket = SERVICE_CONFIG.get('lyvecloud.log_bucket')
    latestLogFound = s3.search_objects(conn=s3conn,
                      bucket=bucket,
                      date_range=date_range,
                      deep_search=False,
                      folder_prefix=folder_prefix,
                      sort_result=True,
                      debug=debug)
    print('---> Found : {} items that matched your search criteria.'.format(len(latestLogFound)), flush=True)


    if len(latestLogFound):
        # Shared memory through multiprocessing server process.
        with multiprocessing.Manager() as mp_manager:
            # create a hosted object and get a proxy object
            g_workspace        = mp_manager.Namespace()
            g_workspace.df     = df_history
            g_workspace.bucket = bucket

            # Create a queue within the context of the manager
            q = mp_manager.Queue(maxsize=32)
            results = mp_manager.list()

            latestLogFound = [
                {
                    'q'                 : q,
                    'g'                 : g_workspace,
                    'bucket'            : bucket,
                    'seq_no'            : seq_no,
                    's3_objs_meta'      : s3_objs_meta,
                    'skip_download'     : False,
                    'skip_history_check': False,
                } for seq_no, s3_objs_meta in enumerate(latestLogFound)
            ]

            total_objs = len(latestLogFound)
            print('total jobs:', total_objs)

            # max_thread_pool = SERVICE_CONFIG.get('opensearch.max_thread_pool', -1)
            max_process_pool = SERVICE_CONFIG.get('opensearch.max_process_pool', -1)
            # num_workers = min(len(latestLogFound), os.cpu_count())
            num_workers = min(len(latestLogFound), os.cpu_count()) if max_process_pool <= 0 else min(len(latestLogFound), os.cpu_count(), max_process_pool)
            if debug: print('Total reserved worker processes: ', num_workers)

            p1 = multiprocessing.Process(target=log_recevicer, args=(q, results))
            p1.start()

            start_time = time.perf_counter()

            with enlighten.Manager() as pbar_manager:
                with pbar_manager.counter(total=total_objs, desc='Check & Download Logs:', unit='items', color='yellow') as tocks:
                    with concurrent.futures.ProcessPoolExecutor(max_workers=num_workers) as executor:
                        futures = {executor.submit(download_and_parse_objets, **param_kwargs): idx for idx, param_kwargs in enumerate(latestLogFound)}
                        # wait for all tasks to complete by getting all results
                        for future in concurrent.futures.as_completed(futures):
                            idx = futures[future]

                            try:
                                resp = future.result()
                            except Exception as e:
                                print(f'Exception!, job-process-executor, seq_no: {idx}, error: {e}')

                            tocks.update()

            # -- the non-progress bar version
            # with concurrent.futures.ProcessPoolExecutor(max_workers=num_workers) as executor:
            #     # futures = {executor.submit(s3.download_objets, **param_kwargs): idx for idx, param_kwargs in enumerate(latestLogFound)}
            #     futures = {executor.submit(download_and_parse_objets, **param_kwargs): idx for idx, param_kwargs in enumerate(latestLogFound)}

            #     # wait for all tasks to complete by getting all results
            #     for future in concurrent.futures.as_completed(futures):
            #         idx = futures[future]

            #         try:
            #             resp = future.result()
            #         except Exception as e:
            #             print(f'Exception!, job-process-executor, seq_no: {idx}, error: {e}')

            while not q.empty():
                time.sleep(1)

            p1.terminate()
            p1.join()
            p1.close()

            print(flush=True)
            print('Saving history...')
            print('History dataframe shape: ', g_workspace.df.shape)
            g_workspace.df.to_csv(path_or_buf=os.path.join('logs', 'history.csv'), index=False)
            process_time = time.perf_counter() - start_time
            print('process_time:', process_time)

            exception_status = 'PASS'
            exception_code   = '0'
            exception_reason = ''
    else:
        exception_status = 'FAIL'
        exception_code   = '-999'
        exception_reason = 'No log file to download.'

    print(flush=True)
    ret.update(
        {
            'EXCEPTION_STATUS'    : exception_status,
            'EXCEPTION_CODE'      : exception_code,
            'EXCEPTION_REASON'    : exception_reason,
            'PROCESS_TIME'        : time.perf_counter() - start_time_overall,
        }
    )

    return ret



def ingress_helper(app_config, *args, **kwargs):
    debug                  = kwargs.get('debug', False)
    last_n_days            = kwargs.get('last_n_days', 0)
    last_n_hours           = kwargs.get('last_n_hours', 1)
    last_n_mins            = kwargs.get('last_n_mins', 0)
    t_last                 = kwargs.get('t_last', None)
    t_now                  = kwargs.get('t_now', None)

    use_relative_datetime_range = False
    if t_now and t_last:
        try:
            t_last = dateutil.parser.parse(t_last).replace(second=0, microsecond=0).astimezone(tz=datetime.timezone.utc)
            t_now  = dateutil.parser.parse(t_now).replace(second=0, microsecond=0).astimezone(tz=datetime.timezone.utc)
        except Exception as e:
            use_relative_datetime_range = True
            print('Exception in using specific datetime range:' + str(e))
    else:
        use_relative_datetime_range = True
        t_now = datetime.datetime.now(tz=datetime.timezone.utc).replace(second=0, microsecond=0)

    if use_relative_datetime_range:
        t_last = t_now - datetime.timedelta(days=last_n_days, hours=last_n_hours, minutes=last_n_mins)

    folder_prefix_list = pd.date_range(start=t_last, end=t_now, periods=None, freq='D', tz=None, normalize=False, name=None, inclusive=None)
    folder_prefix_list = [item.strftime('%B-%Y') for item in folder_prefix_list.to_pydatetime()]
    folder_prefix_list = helpers.utils.unique(sequence=folder_prefix_list)

    print('folder_prefix_list:', folder_prefix_list)
    print('datetime rage     :')
    print('{timezone:>32s}|From: {start_time:26s} --> End: {stop_time}'.format(
        timezone=t_last.astimezone(tz=datetime.timezone.utc).tzname(),
        start_time=t_last.astimezone(tz=datetime.timezone.utc).isoformat(),
        stop_time=t_now.astimezone(tz=datetime.timezone.utc).isoformat(),))
    print('{timezone:>32s}|From: {start_time:26s} --> End: {stop_time}'.format(
        timezone=t_last.astimezone().tzname(),
        start_time=t_last.astimezone().isoformat(),
        stop_time=t_now.astimezone().isoformat(),))
    print()

    for folder_prefix in folder_prefix_list:
        kwargs = {
            'date_range'   : {'time_zone': 'utc', 'gte': t_last, 'lt': t_now},
            'df_history'   : app_config['HISTORY_TRACKING'],
            'folder_prefix': folder_prefix,
            'debug'        : False,
        }

        print('Runing job for folder_prefix:', folder_prefix)
        try:
            resp = run(**kwargs)
        except Exception as e:
            resp = {
                'FOLDER_PREFIX'   : folder_prefix,
                'EXCEPTION_STATUS': 'FAIL',
                'EXCEPTION_CODE'  : -1,
                'EXCEPTION_REASON': str(e)
            }

        print('---- Summary ----')
        print('FOLDER_PREFIX   :', resp.get('FOLDER_PREFIX'))
        print('@timestamp      :', resp.get('@timestamp'))
        print('EXCEPTION_STATUS:', resp.get('EXCEPTION_STATUS'))
        print('EXCEPTION_CODE  :', resp.get('EXCEPTION_CODE'))
        print('EXCEPTION_REASON:', resp.get('EXCEPTION_REASON'))
        print('PROCESS_TIME    :', resp.get('PROCESS_TIME'))
        print('-' * 80)
        print()
