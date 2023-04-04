# Copyright (c) 2021 Seagate Technology LLC and/or its Affiliates

import os
import datetime
import hashlib
import pandas as pd


MAX_RETENTION_DAYS = 30
HISTORY_COLS = [
    '@timestamp',
    # 'SERIAL_NUM',
    # 'EVENT_DATE',
    'EVENT_TYPE',
    'EXCEPTION_STATUS',
    'EXCEPTION_CODE',
    'EXCEPTION_REASON',
    'LAST_FAIL_ID',
    'LAST_FAIL_ROW',
    'LAST_FAIL_DESC',
    'PROCESS_TIME',
    'INDEX_NAME',
    'FILE_NAME',
    'FILE_SIZE_COMPRESSED',
    'FILE_SIZE_UNCOMPRESSED',
    'FILE_LAST_MODIFIED',
    'FILE_HASH',
    'NUM_SAMPLES',
    'SUCCESS_CNT',
    'ERROR_CNT',

    'HOST_ADDR',
    'HOST_NAME',
    'HOST_PORT',
    'REMOTE_ADDR',
    'REMOTE_PORT',
    'REQUEST_METHOD',
    'REQUEST_URI',
    'REQUEST_URL_SCHEME',
    'USER_AGENT',
    'SEND_TO_ELK',
]


def makeID(paintext, unique=False):
    if unique:
        paintext = "{}@{}".format(paintext, datetime.datetime.now().strftime('%d-%b-%Y %H:%M:%S:%f'))
    return hashlib.md5(paintext.encode()).hexdigest()


def fatdict(data):
    resp = {}
    def toFatdict(data, keychain=''):
        for key, value in data.items():
            if keychain:
                key = keychain + "." + key

            if isinstance(value, dict):
                toFatdict(value, key)
            else:
                resp[key] = value

    toFatdict(data)
    return resp


def unique(sequence):
    seen = set()
    return [x for x in sequence if not (x in seen or seen.add(x))]


def system_history_log_init(target_folder='logs'):
    force_new_log = False

    if not os.path.isdir(target_folder):
        os.makedirs(target_folder, exist_ok=True)

    try:
        df = pd.read_csv(filepath_or_buffer=os.path.join(target_folder, 'history.csv'),
                                    delimiter=',',
                                    skipinitialspace=True,
                                    header=0,
                                    #nrows=2,
                                    #usecols=column_types.keys(),
                                    #dtype=column_types,
                                    parse_dates=['@timestamp', 'FILE_LAST_MODIFIED',],
                                    na_values=['NA', 'NONE', 'NAN', '', ],
                                    keep_default_na=False,
                                    infer_datetime_format=True,
                                    index_col=False,
                                    low_memory=False,
                                    #error_bad_lines=True,
                                    #warn_bad_lines=True,
                                    verbose=False)

        # Clean-up old history
        df.reset_index(drop=True, inplace=True)
        d1 = pd.Timestamp.utcnow() + pd.offsets.Day(-MAX_RETENTION_DAYS)
        fix_index = df[df['@timestamp'] < d1].index
        if len(fix_index):
            df.drop(fix_index, inplace=True)
            df.reset_index(drop=True, inplace=True)
            df.to_csv(path_or_buf=os.path.join(target_folder, 'history.csv'), index=False)
        print('**** loaded existing history ****')
    except Exception as e:
        force_new_log = True

    if force_new_log:
        params = {col: [] for col in HISTORY_COLS}
        df = pd.DataFrame(params)
        df.to_csv(path_or_buf=os.path.join(target_folder, 'history.csv'), index=False)

    return df
