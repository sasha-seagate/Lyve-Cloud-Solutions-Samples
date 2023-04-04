# Copyright (c) 2021 Seagate Technology LLC and/or its Affiliates
import datetime
import time
import os
import copy
import concurrent.futures
import collections

from helpers.utils import makeID
from .parser_engine import LogParser
from .enums import Action
from destination import elk_connector


class ParserConsole(LogParser):
    """ extract a console log from .gz to dict """

    def __init__(self, config, debug=False):
        super().__init__()
        self.config = config
        self.debug = debug


    def logs(self):
        return self.getLogs()


    def sendTo(self, datasource):
        ret = None

        if datasource == Action.toInflux.value:
            self.__toInfluxdb()
        if datasource == Action.toElasticSearch.value:
            ret = self.__toELK(distro_name='elasticsearch', log_category='console')
        if datasource == Action.toOpenSearch.value:
            ret = self.__toELK(distro_name='opensearch', log_category='console')

        return ret


    def getParsedLogs(self, filename):
        my_bulk_logs = []
        for idx, log in enumerate(self.getLogs()):
            doc_id = makeID(paintext='{}_{}'.format(filename, idx))
            if isinstance(log, dict):
                # Add doc_id
                log['_id'] = doc_id
                log['_op_type'] = 'create'

                # Add @timestamp
                if 'ConsoleEvent.EventTime' in log:
                    value = log['ConsoleEvent.EventTime']

                    if value != '':
                        log.update(
                            {
                                'ConsoleEvent.EventTime':  " ".join(value.split()[:4]),
                                '@timestamp'            :  " ".join(value.split()[:4]),
                            }
                        )

                my_bulk_logs.append(copy.deepcopy(log))
        return my_bulk_logs


    def parsing(self, client, idx_name, log_category, filename, idx, log):
        exception_status = ''
        exception_code   = ''
        exception_reason = ''

        doc_id = makeID(paintext='{}_{}'.format(filename, idx))

        if isinstance(log, dict):
            is_valid_data = False

            # Add @timestamp
            if 'ConsoleEvent.EventTime' in log:
                value = log['ConsoleEvent.EventTime']

                if value != '':
                    is_valid_data = True
                    log.update(
                        {
                            'ConsoleEvent.EventTime':  " ".join(value.split()[:4]),
                            '@timestamp'            :  " ".join(value.split()[:4]),
                        }
                    )

            if is_valid_data:
                try:
                    client._write(id=doc_id, idx_name=idx_name, dict_data=log, op_type='create')

                    exception_status = 'PASS'
                    exception_code   = '0'
                    exception_reason = 'PASS'
                except Exception as e:
                    print('Exception client._write: ', e)
                    exception_status = 'FAIL'
                    exception_code   = '99999'
                    exception_reason = str(e)
            else:
                exception_status = 'FAIL'
                exception_code   = '-1'
                exception_reason = f'Invalid data. Unable to parse the @timestamp field.'
        else:
            exception_status = 'FAIL'
            exception_code   = '-1'
            exception_reason = 'Not a dictionary type'

        ret = {
            'doc_id'              : doc_id,
            'log_category'        : log_category,
            'filename'            : filename,
            'idx'                 : idx,

            'EXCEPTION_STATUS'    : exception_status,
            'EXCEPTION_CODE'      : exception_code,
            'EXCEPTION_REASON'    : exception_reason,
        }
        return ret


    def __toELK(self, distro_name, log_category='untitled', bulk_mode=True):
        start_time = time.perf_counter()
        success_cnt = 0
        error_cnt = 0
        last_fail_id = ''
        last_fail_row = None
        last_fail_desc = ''
        allow_data_ingression = self.config.get(f'{distro_name}.allow_data_ingression', False)
        verbose = self.config.get(f'{distro_name}.verbose', False)
        continue_on_error = self.config.get(f'{distro_name}.continue_on_error', False)
        max_thread_pool = self.config.get(f'{distro_name}.max_thread_pool', -1)
        # max_process_pool = self.config.get(f'{distro_name}.max_process_pool', -1)
        validate_result = True

        client = elk_connector.Elastic_Connector(distro_name=distro_name,
                                                config=self.config, debug=False)
        client._connect()

        idx_name = self.config.get(f'{distro_name}.{log_category}_index_name', 'lyve.log.untitled-v0')
        filehash = self.getFilehash().lower()
        filename = self.getFilename()
        num_workers = min(self.getSize(), os.cpu_count())

        if not bulk_mode:
            latestRecordFound = [
                {
                    'client'       : client,
                    'idx_name'     : idx_name,
                    'log_category' : log_category,
                    'filename'     : filehash,
                    'idx'          : idx,
                    'log'          : log,
                } for idx, log in enumerate(self.getLogs())
            ]

            with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
                futures = {executor.submit(self.parsing, **param_kwargs): idx for idx, param_kwargs in enumerate(latestRecordFound)}

                for future in concurrent.futures.as_completed(futures):
                    idx = futures[future]

                    try:
                        resp = future.result()

                        if resp.get('EXCEPTION_STATUS', 'FAIL') == 'PASS':
                            success_cnt = success_cnt + 1
                        else:
                            error_cnt = error_cnt + 1
                            last_fail_desc = resp.get('EXCEPTION_REASON')
                            last_fail_row  = resp.get('idx')
                            last_fail_id   = resp.get('doc_id')
                    except Exception as e:
                        error_cnt = error_cnt + 1
                        last_fail_desc = str(e)
                        last_fail_row  = idx
                        last_fail_id   = None
        else:
            data_dict = self.getParsedLogs(filename=filehash)
            if isinstance(data_dict, list):
                try:
                    result = client.es_helpers.parallel_bulk(client=client.es_client,
                        index=idx_name, # if it's not None, it will override the '_index' in each record.
                        actions=data_dict,
                        chunk_size=10000,
                        max_chunk_bytes=128*(1024*1024), # the maximum size of the request in bytes (default: 128MB)
                        thread_count=16,
                        queue_size=16,
                        #ignore_status=[400, 429],
                        raise_on_exception=False,
                        raise_on_error=False)
                    if validate_result:
                        for success, info in result:
                            if not success:
                                error_cnt      = error_cnt + 1
                                s_dict         = info.get('create', {})
                                last_fail_id   = s_dict.get('_id')
                                last_fail_row  = None

                                s_code         = s_dict.get('status', 'NA')
                                s_error_type   = s_dict.get('error', {}).get('type', 'NA')
                                s_error_reason = s_dict.get('error', {}).get('reason', 'NA')
                                last_fail_desc = f'{s_code}_{s_error_type}_{s_error_reason}'
                            else:
                               success_cnt = success_cnt + 1
                    else:
                        collections.deque(result, maxlen=0)
                except Exception as e:
                    last_fail_desc = str(e)
                    last_fail_row  = None
                    last_fail_id   = None


        ret = {
            'PROCESS_TIME'         : time.perf_counter() - start_time,
            'NUM_SAMPLES'          : self.getSize(),
            'ERROR_CNT'            : error_cnt,
            'SUCCESS_CNT'          : success_cnt,
            'INDEX_NAME'           : idx_name,
            'LAST_FAIL_DESC'       : last_fail_desc,
            'LAST_FAIL_ROW'        : last_fail_row,
            'LAST_FAIL_ID'         : last_fail_id,
            'SEND_TO_ELK'          : allow_data_ingression,
        }

        client._close()

        return ret


    def __toInfluxdb(self):
        pass
