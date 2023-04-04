# Copyright (c) 2021 Seagate Technology LLC and/or its Affiliates

import concurrent.futures
import multiprocessing
import datetime
import time
import io
import os
import pandas as pd
import numpy as np
import boto3
import botocore.client
import enlighten
from helpers.config_manager import cfg as SERVICE_CONFIG


def connect():
    s3_config = botocore.client.Config(
        connect_timeout=30,
        read_timeout=30,
        retries={'max_attempts': 2},
        # max_pool_connections=32,
        )

    conn = boto3.client('s3',
                        aws_access_key_id=SERVICE_CONFIG.get('lyvecloud.access_key'),
                        aws_secret_access_key=SERVICE_CONFIG.get('lyvecloud.secret_key'),
                        endpoint_url=SERVICE_CONFIG.get('lyvecloud.endpoint_url'),
                        config=s3_config
                        )

    return conn


def create_bucket(conn, name):
    conn.create_bucket(Bucket=name)


def upload_file(conn, bucket, file_name, object_name=None):
    if object_name is None:
        object_name = file_name
    try:
        response = conn.upload_file(file_name, bucket, object_name)
    except Exception as e:
        print("[s3.upload_file] error", e)
        return False
    return True


def upload_bytesIO(conn, bucket, file_io, object_name):
    try:
        response = conn.upload_fileobj(file_io, bucket, object_name)
    except Exception as e:
        print("[s3.upload_bytesIO] error", e)
        return False
    return True


def download_file(conn, bucket, file_name, object_name=None):
    if object_name is None:
        object_name = file_name
    conn.download_file(bucket, object_name, file_name)


def download_bytesIO(conn, bucket, file_buffer, object_name):
    conn.download_fileobj(bucket, object_name, file_buffer)


def delete_file(conn, bucket, object_name):
    conn.delete_object(Bucket=bucket, Key=object_name)


def list_file(conn, bucket, deep_search=False):
    result = conn.list_objects_v2(Bucket=bucket, Prefix='', Delimiter='/')
    if not 'CommonPrefixes' in result:
        return

    total_subfolders = len(result['CommonPrefixes'])
    print(f'Found {total_subfolders} folders-prefix at root level.')
    print('Folders-prefix at root level list:', result['CommonPrefixes'])

    if deep_search:
        print('Looking into every sub-folders....')
        for item in result['CommonPrefixes']:
            subfolder_prefix = item.get('Prefix', '')
            result = conn.list_objects_v2(Bucket=bucket, Prefix=subfolder_prefix, Delimiter='')

            if not 'Contents' in result:
                continue

            total_objs = len(result['Contents'])
            print('Folder-prefix: {}, Found: {} objects.'.format(subfolder_prefix, total_objs))
            print('Noted that the .list_objects function returns the first 1000 keys.')

            for c in result['Contents']:
                print('{:16s}|{:64s}|{:16d}|{:24s}'.format(subfolder_prefix, c['Key'], c['Size'], c['LastModified'].astimezone().isoformat()))
    else:
        subfolder_prefix = datetime.datetime.now().strftime('%B-%Y')
        print()
        print('Looking into just the current month folder-prefix:', subfolder_prefix)

        result = conn.list_objects_v2(Bucket=bucket, Prefix=subfolder_prefix, Delimiter='')
        if not 'Contents' in result:
            return

        total_objs = len(result['Contents'])
        print('Folder-prefix: {}, Found: {} objects'.format(subfolder_prefix, total_objs))
        print('Noted that the .list_objects_v2 function returns the first 1000 keys.')

        for c in result['Contents']:
            print('{:16s}|{:64s}|{:16d}|{:24s}'.format(subfolder_prefix, c['Key'], c['Size'], c['LastModified'].astimezone().isoformat()))


def list_bucket(conn):
    response = conn.list_buckets()

    print('Existing buckets:')
    for bucket in response['Buckets']:
        print(f'  {bucket["Name"]}')


def paginate_results(conn, bucket, mode='prefix', prefix='', delim='', max_items=None, page_size=1000, sort_result=False, apply_filter=False, jmespath_filters=None):
    result = None

    # Create a reusable Paginator
    paginator = conn.get_paginator('list_objects_v2')

    # Create a PageIterator from the Paginator
    operation_parameters = {
        'Bucket'   : bucket,
        'Prefix'   : prefix,
        'Delimiter': delim,
    }

    page_iterator = paginator.paginate(PaginationConfig={'MaxItems': max_items, 'PageSize': page_size}, **operation_parameters)

    if apply_filter and jmespath_filters:
        filtered_iterator = page_iterator.search(jmespath_filters)
        result = [item for item in filtered_iterator if item]
    else:
        if mode == 'prefix':
            result = [item for page in page_iterator for item in page.get('CommonPrefixes') if item]
        elif mode == 'objects':
            result = [item for page in page_iterator for item in page.get('Contents') if item]

    if sort_result:
        if mode == 'prefix':
            result = sorted(result, key=lambda d: d['Prefix'], reverse=True)
        elif mode == 'objects':
            result = sorted(result, key=lambda d: d['LastModified'], reverse=True)

    return result


def download_objets(q, bucket, s3_objs_meta, *args, **kwargs):
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
        file_buffer = io.BytesIO()
        conn = connect()
        conn.download_fileobj(bucket, s3_objs_meta['Key'], file_buffer)
        file_buffer.seek(0)
        params['body'] = file_buffer
        params['status'] = 'new'
    else:
        params['status'] = 'skipped'

    try:
        q.put(params, block=True)
    except Exception as e:
        print(f'Exception!, s3-download_objets, seq_no: {seq_no}, meta:, {s3_objs_meta}, error: {e}')

    return params


def search_objects(conn, bucket, date_range, *args, **kwargs):
    """
    This function uses a paginator to list  all items by date_range criteria.

    """

    folder_prefix   = kwargs.get('folder_prefix', None)
    deep_search     = kwargs.get('deep_search', False)
    sort_result     = kwargs.get('sort_result', False)
    max_items       = kwargs.get('max_items', None)
    debug           = kwargs.get('debug', False)
    s3_objs_meta    = []

    if not date_range:
        if debug: print('Error. Not define date_range.')
        return s3_objs_meta

    t_now  = date_range.get('lt')
    t_last = date_range.get('gte')

    # Apply filters template
    jmespath_search_criteria = f"Contents[?(to_string(LastModified) >= '\"{t_last}\"') && (to_string(LastModified) < '\"{t_now}\"') && (Size > `0`)][]"

    if deep_search:
        if debug: print('Listing all folders-prefix at root level...')
        folders = paginate_results(conn=conn,
            bucket=bucket,
            mode='prefix',
            prefix='',
            delim='/',
            max_items=max_items,
            sort_result=sort_result,
            apply_filter=False,
            jmespath_filters=None)

        if debug:
            print('Found {0} folders-prefix at root level.'.format(len(folders)))
            print('Folders-prefix at root level list:', folders)

        if debug: print('Warning! [deep_search=True] detected. Ignoring [folder_prefix] parameter and perform deepsearch by looking into every folders-prefix in the root level.')
        for folder in folders:
            folder_prefix = folder.get('Prefix', '')

            result = paginate_results(conn=conn,
                bucket=bucket,
                mode='objects',
                prefix=folder_prefix,
                delim='',
                max_items=max_items,
                sort_result=sort_result,
                apply_filter=True,
                jmespath_filters=jmespath_search_criteria)

            total_objs = len(result)
            if total_objs:
                s3_objs_meta.extend(result)
            if debug: print('Folder-prefix: {}, Found: {} objects.'.format(folder_prefix, total_objs))
        if debug: print('Total (All-Folders) Found: {} objects.'.format(len(s3_objs_meta)))
    else:
        if not folder_prefix:
            folder_prefix = datetime.datetime.now().strftime('%B-%Y')
            if debug: print('Warning! [deep_search=False] but folder_prefix is not set. Auto set default to [folder_prefix={}]'.format(folder_prefix))

        result = paginate_results(conn=conn,
            bucket=bucket,
            mode='objects',
            prefix=folder_prefix,
            delim='',
            max_items=max_items,
            sort_result=sort_result,
            apply_filter=True,
            jmespath_filters=jmespath_search_criteria)

        total_objs = len(result)
        if total_objs:
            s3_objs_meta.extend(result)
        if debug: print('Folder-prefix: {}, Found: {} objects.'.format(folder_prefix, total_objs))

    return s3_objs_meta
