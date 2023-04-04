# Copyright (c) 2021 Seagate Technology LLC and/or its Affiliates
import datetime
import time
import os
import concurrent.futures

from helpers.utils import makeID
from .parser_engine import LogParser
from .enums import Action
from destination import elk_connector


class ParserEngineStats():
    """ Parser Engine Statistic Log """

    def __init__(self, config, logs=[], debug=False):
        super().__init__()
        self.config = config
        self.logs = logs
        self.debug = debug


    def getLogs(self):
        return self.logs


    def getSize(self):
        return len(self.logs)


    def sendTo(self, datasource):
        ret = None

        if datasource == Action.toInflux.value:
            self.__toInfluxdb()
        if datasource == Action.toElasticSearch.value:
            ret = self.__toELK(distro_name='elasticsearch', log_category='parser')
        if datasource == Action.toOpenSearch.value:
            ret = self.__toELK(distro_name='opensearch', log_category='parser')

        return ret


    def __toInfluxdb(self):
        pass


    def __toELK(self, distro_name, log_category='untitled'):
        start_time = time.perf_counter()
        success_cnt = 0
        error_cnt = 0
        last_fail_id = ''
        last_fail_row = None
        last_fail_desc = ''
        lyve_parser_log_enable = self.config.get(f'{distro_name}.lyve_parser_log_enable', False)
        allow_data_ingression = self.config.get(f'{distro_name}.allow_data_ingression', False)
        verbose = self.config.get(f'{distro_name}.verbose', False)
        continue_on_error = self.config.get(f'{distro_name}.continue_on_error', False)

        if lyve_parser_log_enable:
            client = elk_connector.Elastic_Connector(distro_name=distro_name, config=self.config)
            client._connect()
            idx_name = self.config.get(f'{distro_name}.{log_category}_index_name', 'lyve.log.untitled-v0')
            filename = 'history'

            for idx, log in enumerate(self.getLogs()):
                doc_id = ''

                if isinstance(log, dict):
                    try:
                        client._write(idx_name=idx_name, dict_data=log, op_type='index')
                        success_cnt = success_cnt + 1
                    except Exception as e:
                        error_cnt = error_cnt + 1
                        last_fail_desc = str(e)
                        last_fail_row = idx
                        last_fail_id = ''

                        if verbose:
                            print(f'>ERR<|{log_category}|{filename}|{idx}|{doc_id}|{e}')

                        if continue_on_error:
                            continue
                        else:
                            break

        ret = {
            'PROCESS_TIME'         : time.perf_counter() - start_time,
            'NUM_SAMPLES'          : self.getSize(),
            'ERROR_CNT'            : error_cnt,
            'SUCCESS_CNT'          : success_cnt,
            'INDEX_NAME'           : idx_name,
            'LAST_FAIL_DESC'       : last_fail_desc,
            'LAST_FAIL_ROW'        : last_fail_row,
            'LAST_FAIL_ID'         : last_fail_id,
            'allow_data_ingression': allow_data_ingression,
            'lyve_parser_log_enable': lyve_parser_log_enable,
        }

        return ret
