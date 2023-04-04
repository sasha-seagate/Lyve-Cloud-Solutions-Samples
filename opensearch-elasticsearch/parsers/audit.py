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


class ParserAudit(LogParser):
    """ extract api audit log from .gz to dict """

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
            ret = self.__toELK(distro_name='elasticsearch', log_category='api_audit')
        if datasource == Action.toOpenSearch.value:
            ret = self.__toELK(distro_name='opensearch', log_category='api_audit')

        return ret


    def getParsedLogs(self, filename):
        my_bulk_logs = []
        for idx, log in enumerate(self.getLogs()):
            doc_id = makeID(paintext='{}_{}'.format(filename, idx))
            if isinstance(log, dict):
                # Add doc_id
                log['_id'] = doc_id
                log['_op_type'] = 'create'

                if 'auditEntry.api.timeToResponse' in log:
                    log.update(
                        {
                            'auditEntry.api.timeToResponse':  int(log['auditEntry.api.timeToResponse'].replace('ns', ''))
                        }
                    )
                if 'auditEntry.api.timeToFirstByte' in log:
                    log.update(
                        {
                            'auditEntry.api.timeToFirstByte':  int(log['auditEntry.api.timeToFirstByte'].replace('ns', ''))
                        }
                    )

                # Add user defined metric here
                if 'auditEntry.api.statusCode' in log and 'auditEntry.api.status' in log:
                    if (len(str(log['auditEntry.api.statusCode'])) > 0) and (len(str(log['auditEntry.api.status'])) > 0):
                        log.update(
                            {
                                'HTTP_STATUS_CODE_MSG':  '{status_code}_{status_msg}'.format(status_code=log['auditEntry.api.statusCode'], status_msg=log['auditEntry.api.status']),
                            }
                        )

                # Add @timestamp
                if 'auditEntry.time' in log:
                    value = log['auditEntry.time']

                    if value != '':
                        log.update(
                            {
                                '@timestamp':  log['auditEntry.time']
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

            if 'auditEntry.api.timeToResponse' in log:
                log.update(
                    {
                        'auditEntry.api.timeToResponse':  int(log['auditEntry.api.timeToResponse'].replace('ns', ''))
                    }
                )
            if 'auditEntry.api.timeToFirstByte' in log:
                log.update(
                    {
                        'auditEntry.api.timeToFirstByte':  int(log['auditEntry.api.timeToFirstByte'].replace('ns', ''))
                    }
                )

            # Add user defined metric here
            if 'auditEntry.api.statusCode' in log and 'auditEntry.api.status' in log:
                if (len(str(log['auditEntry.api.statusCode'])) > 0) and (len(str(log['auditEntry.api.status'])) > 0):
                    log.update(
                        {
                            'HTTP_STATUS_CODE_MSG':  '{status_code}_{status_msg}'.format(status_code=log['auditEntry.api.statusCode'], status_msg=log['auditEntry.api.status']),
                        }
                    )

            # Add @timestamp
            if 'auditEntry.time' in log:
                value = log['auditEntry.time']

                if value != '':
                    is_valid_data = True
                    log.update(
                        {
                            '@timestamp':  log['auditEntry.time']
                        }
                    )

            if is_valid_data:
                try:
                    client._write(id=doc_id, idx_name=idx_name, dict_data=log, op_type='create')

                    exception_status = 'PASS'
                    exception_code   = '0'
                    exception_reason = 'PASS'
                except Exception as e:
                    # print('Exception client._write: ', e)
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

        if self.debug: print('  > preparing OpenSearch object  ...')
        client = elk_connector.Elastic_Connector(distro_name=distro_name,
                                                config=self.config, debug=False)
        if self.debug: print('  > connecting to Opensearch ...')
        client._connect()
        if self.debug: print('  > Opensearch Server Status: ', client._info())

        idx_name = self.config.get(f'{distro_name}.{log_category}_index_name', 'lyve.log.untitled-v0')
        filehash = self.getFilehash().lower()
        filename = self.getFilename()
        # num_workers = min(self.getSize(), os.cpu_count())
        num_workers = min(self.getSize(), os.cpu_count()) if max_thread_pool <= 0 else min(self.getSize(), os.cpu_count(), max_thread_pool)

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
                        if self.debug: print(f'job-executor, seq_no: {idx}, resp: {resp}')

                        if resp.get('EXCEPTION_STATUS', 'FAIL') == 'PASS':
                            success_cnt = success_cnt + 1
                        else:
                            error_cnt = error_cnt + 1
                            last_fail_desc = resp.get('EXCEPTION_REASON')
                            last_fail_row  = resp.get('idx')
                            last_fail_id   = resp.get('doc_id')
                    except Exception as e:
                        if self.debug: print(f'Exception!, job-thread-executor, seq_no: {idx}, error: {e}')
                        error_cnt = error_cnt + 1
                        last_fail_desc = str(e)
                        last_fail_row  = idx
                        last_fail_id   = None
        else:
            # print('transfering in parallel_bulk mode.')
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
                                # print(f'success: {success}, failed --:', info)
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

        if self.debug: print('  > closed opensearch ...')
        client._close()

        if self.debug: print('  > returning: ', ret)
        return ret


    def __toInfluxdb(self):
        pass
