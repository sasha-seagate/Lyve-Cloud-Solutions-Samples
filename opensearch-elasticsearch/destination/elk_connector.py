# Copyright (c) 2021 Seagate Technology LLC and/or its Affiliates

import ast
import asteval
import time
import datetime
import json
import os
import requests
import ssl
import importlib
import numpy as np


class Elastic_Connector():
    def __init__(self, distro_name, config, *args, **kwargs):
        if distro_name not in ['elasticsearch', 'opensearch']:
            raise Exception('NOT SUPPORTED ELASTICSEARCH/OPENSEARCH DISTRIBUTION')

        self.debug = kwargs.get('debug', False)
        self.distro_name = distro_name
        self.credentials = {
            'username': None,
            'password': None,
            'api_key_id': None,
            'api_key_id': None,
        }
        self.config_credentials = config.get(f'{self.distro_name}.credentials', [])
        if len(self.config_credentials):
            for c in self.config_credentials:
                for key, value in c.items():
                    self.credentials[key] = value

        self.stack_version       = int(config.get(f'{self.distro_name}.stack_version', '8.x.x').split('.')[0])
        self.es_client           = None
        self.server_url          = config.get(f'{self.distro_name}.server_url', 'https://localhost:9200')
        self.tenant              = config.get(f'{self.distro_name}.tenant', 'global')
        self.authentication_mode = config.get(f'{self.distro_name}.authentication_mode', None)
        self.server_username     = self.credentials['username']
        self.server_password     = self.credentials['password']
        self.api_key_id          = self.credentials['api_key_id']
        self.api_key_value       = self.credentials['api_key_value']
        self.use_ssl_certs       = config.get(f'{self.distro_name}.use_ssl', False)
        self.verify_certs        = config.get(f'{self.distro_name}.verify_certs', None)
        self.ca_certs_path       = config.get(f'{self.distro_name}.ca_certs', None)
        self.client_cert_path    = config.get(f'{self.distro_name}.client_cert', None)
        self.client_key_path     = config.get(f'{self.distro_name}.client_key', None)
        self.timeout             = config.get(f'{self.distro_name}.timeout', 30)
        self.max_retries         = config.get(f'{self.distro_name}.max_retries', 3)
        self.retry_on_timeout    = config.get(f'{self.distro_name}.retry_on_timeout', True)
        self.api_compatibility_header = config.get(f'{self.distro_name}.api_compatibility_header', {"accept": "application/vnd.elasticsearch+json; compatible-with=7"})
        self.allow_data_ingression    = config.get(f'{self.distro_name}.allow_data_ingression', False)

        self.min_sleep             = config.get(f'{self.distro_name}.min_sleep', 0.001)
        self.max_sleep             = config.get(f'{self.distro_name}.max_sleep', 0.1)

        if self.debug: print('  >> Elastic_Connector :: initializing variables ...')

        self.use_ssl = self.server_url.startswith('https')
        if self.use_ssl:
            if self.use_ssl_certs:
                self.ssl_context = None
            else:
                self.ssl_context = ssl.create_default_context()
                self.ssl_context.check_hostname = False
                self.ssl_context.verify_mode = ssl.CERT_NONE

                self.verify_certs = False
                self.ca_certs_path = None
                self.client_cert_path = None
                self.client_key_path = None
        else:
            self.ssl_context = None
            self.verify_certs = False
            self.ca_certs_path = None
            self.client_cert_path = None
            self.client_key_path = None

        if self.distro_name == 'elasticsearch' and self.stack_version <= 7:
            self.Elasticsearch = importlib.import_module(name='elasticsearch.client', package=None).Elasticsearch
            self.es_helpers    = importlib.import_module(name='elasticsearch.helpers', package='elasticsearch')
        elif self.distro_name == 'elasticsearch' and self.stack_version >= 8:
            self.Elasticsearch = importlib.import_module(name='elasticsearch', package=None).Elasticsearch
            self.es_helpers    = importlib.import_module(name='elasticsearch.helpers', package='elasticsearch')
        elif self.distro_name == 'opensearch':
            if self.debug: print('  >> Elastic_Connector :: importing opensearch library ...')
            self.Elasticsearch = importlib.import_module(name='opensearchpy', package=None).OpenSearch
            self.es_helpers    = importlib.import_module(name='opensearchpy.helpers', package='opensearchpy')
            self.es            = importlib.import_module(name='opensearchpy', package=None)
            if self.debug: print('  >> Elastic_Connector :: imported opensearch library ...')
        else:
            raise Exception('NOT SUPPORTED ELASTICSEARCH/OPENSEARCH VERSION')

        if self.debug: print('  >> Elastic_Connector :: initialized variables ...')


    def _connect(self):
        if self.debug: print(f'  >> Elastic_Connector :: connecting...')

        if self.distro_name == 'elasticsearch':
            if self.authentication_mode == 'basic':
                self.es_client = self.Elasticsearch(
                    hosts=self.server_url,
                    basic_auth=(self.server_username, self.server_password),
                    http_compress=True,
                    verify_certs=self.verify_certs,
                    ssl_context=self.ssl_context,
                    #ssl_assert_hostname=False,
                    ssl_assert_fingerprint=False,
                    ssl_show_warn=False,

                    ca_certs=self.ca_certs_path,
                    client_cert=self.client_cert_path,
                    client_key=self.client_key_path,

                    # Multi threaded, allow up to 25 connections to each node (default=10)
                    #connections_per_node=25,
                    request_timeout=self.timeout,
                    max_retries=self.max_retries,
                    retry_on_timeout=self.retry_on_timeout,
                    headers=self.api_compatibility_header
                )
            elif self.authentication_mode == 'api_key':
                self.es_client = self.Elasticsearch(
                    hosts=self.server_url,
                    api_key=(self.api_key_id, self.api_key_value),
                    http_compress=True,
                    verify_certs=self.verify_certs,

                    ca_certs=self.ca_certs_path,
                    client_cert=self.client_cert_path,
                    client_key=self.client_key_path,

                    # Multi threaded, allow up to 25 connections to each node (default=10)
                    #connections_per_node=25,
                    request_timeout=self.timeout,
                    max_retries=self.max_retries,
                    retry_on_timeout=self.retry_on_timeout,
                    headers=self.api_compatibility_header
                )
            elif self.authentication_mode == 'cloud_id':
                self.es_client = self.Elasticsearch(
                    cloud_id=self.server_url,
                    api_key=self.api_key_value
                )
        elif self.distro_name == 'opensearch':
            if self.authentication_mode == 'basic':
                if self.debug: print(f'  >> Elastic_Connector :: connecting to server: {self.server_url}')
                self.es_client = self.Elasticsearch(
                    hosts=self.server_url,
                    http_auth=(self.server_username, self.server_password),
                    http_compress=True,
                    verify_certs=self.verify_certs,
                    ssl_context=self.ssl_context,
                    #ssl_assert_hostname=False,
                    ssl_assert_fingerprint=False,
                    ssl_show_warn=False,

                    ca_certs=self.ca_certs_path,
                    client_cert=self.client_cert_path,
                    client_key=self.client_key_path,

                    # Multi threaded, allow up to 25 connections to each node (default=10)
                    timeout=self.timeout,
                    maxsize=100,
                    pool_maxsize=100,
                    connections_per_node=100,
                )
                if self.debug: print(f'  >> Elastic_Connector :: connecting status: {self.es_client.info()}')
            elif self.authentication_mode == 'api_key':
                raise Exception('NOT IMPLEMENTED OR NOT SUPPORTED.')
            elif self.authentication_mode == 'cloud_id':
                raise Exception('NOT IMPLEMENTED OR NOT SUPPORTED.')

        if self.debug: print(f'  >> Elastic_Connector :: connected.')
        return self.es_client


    def _close(self):
        if self.distro_name == 'elasticsearch':
            try:
                self.es_client.close()
            except Exception as e:
                print(f'[{self.distro_name}.close_connection] error', e)
        elif self.distro_name == 'opensearch':
            try:
                self.es_client.close()
            except Exception as e:
                print(f'[{self.distro_name}.close_connection] error', e)


    def _info(self):
        return self.es_client.info()


    def _write(self, idx_name, dict_data, id=None, op_type='index'):
        if self.allow_data_ingression:
            try:
                if isinstance(dict_data, dict):
                    resp = {}
                    if self.debug: print(f'  >> writing to idx_name: {idx_name}, op_type: {op_type}, doc_id: {id}, data: -')

                    if op_type == 'index':
                        resp = self.es_client.index(body=dict_data, index=idx_name, id=id)
                    elif op_type == 'create':
                        resp = self.es_client.create(body=dict_data, index=idx_name, id=id)

                    resp_message = resp.get('result', '')
                    if self.debug: print(f'  >> writing resp: {resp_message}')

                    if resp_message not in ['created', 'updated']:
                        raise Exception(f'UNABLE TO INGEST DATA. resp_message: {resp_message}')
                else:
                    raise Exception(f'NOT SUPPORTED DATA FORMAT, REQUIRED A DICTIONARY TYPE BUT GOT {type(dict_data)}')
            # except self.es.RequestError as e:
            #     pass
            # except self.es.ConflictError as e:
            #     pass
            except Exception as e:
                raise Exception(e)
        time.sleep(np.random.uniform(self.min_sleep, self.max_sleep))


    def api_requests(self, url, run_mode, cookies, headers, payload, *args, **kwargs):
        debug = kwargs.get('debug', False)

        start_time = time.perf_counter()

        ret = {}
        exception_status  = ''
        exception_code    = ''
        exception_reason  = ''
        resp = None

        # Endpoint URL
        api_url              = url

        # TLS/SSL (set use_ssl_certs=null, if you don't want to use HTTPs with CA certificate)
        use_ssl_certs        = self.use_ssl_certs
        verify_certs         = self.verify_certs

        # SSL Cert Verification
        ca_certs             = self.ca_certs_path

        # Client Side Certificate
        client_cert          = self.client_cert_path
        client_key           = self.client_key_path

        credentials          = requests.auth.HTTPBasicAuth(username=self.server_username, password=self.server_password)
        timeout              = self.timeout

        if headers is None:
            headers = {
                "osd-xsrf"           : 'true',
                "Content-Type"       : 'application/json' ,
                'security_tenant'    : self.tenant,
            }

        if debug:
            print('api_requests -->', run_mode, '-- URL:', api_url)

        with requests.Session() as session:
            try:
                if run_mode == 'GET':
                    resp = session.get(url=api_url,
                                        auth=credentials,
                                        verify=verify_certs,
                                        cert=(client_cert, client_key),
                                        headers=headers,
                                        #cookies=cookies,
                                        #data=payload,
                                        timeout=timeout
                                        )
                elif run_mode == 'CREATE':
                    resp = session.post(url=api_url,
                                        auth=credentials,
                                        verify=verify_certs,
                                        cert=(client_cert, client_key),
                                        headers=headers,
                                        #cookies=cookies,
                                        data=payload,
                                        timeout=timeout
                                        )
                elif run_mode == 'UPDATE':
                    resp = session.put(url=api_url,
                                        auth=credentials,
                                        verify=verify_certs,
                                        cert=(client_cert, client_key),
                                        headers=headers,
                                        #cookies=cookies,
                                        data=payload,
                                        timeout=timeout
                                        )
                elif run_mode == 'DELETE':
                    resp = session.delete(url=api_url,
                                        auth=credentials,
                                        verify=verify_certs,
                                        cert=(client_cert, client_key),
                                        headers=headers,
                                        #cookies=cookies,
                                        #data=payload,
                                        timeout=timeout
                                        )

                #resp.raise_for_status()
                if resp.status_code in [200, 201]:
                    exception_status  = 'PASS'
                    exception_code    = ''
                    exception_reason  = 'PASS'
                else:
                    exception_status  = 'FAIL'
                    exception_code    = ''
                    exception_reason  = resp.json().get('status')
            except Exception as e:
                exception_status  = 'FAIL'
                exception_code    = ''
                exception_reason  = 'Exception: ' + str(e)

        ret.update(
            {
                'resp'              : resp,
                'EXCEPTION_STATUS'  : exception_status,
                'EXCEPTION_CODE'    : exception_code,
                'EXCEPTION_REASON'  : exception_reason,
                'PROCESS_TIME'      : time.perf_counter() - start_time,
            })


        if debug:
            print('EXCEPTION_STATUS :', exception_status)
            print('PROCESS_TIME     :', ret['PROCESS_TIME'])

            if isinstance(resp, requests.models.Response):
                if exception_status == 'PASS':
                    pass
                else:
                    print('resp status      :' , resp.json().get('status'))
                    print('resp error       :' , resp.json().get('error'))
                    print('-' * 80)
                    print('resp json        :' , resp.json())

            print()
        return ret


    def manage_ism(self, run_mode='GET', *args, **kwargs):
        debug = kwargs.get('debug', False)

        end_point       = '_plugins/_ism/policies'
        api_url         = self.server_url + '/' + end_point
        config_filepath = os.path.join('destination', 'opensearch', 'ism', 'seagate-ilm-stream-retention-1y.py')
        unique_id       = 'seagate-ilm-stream-retention-1y'
        query_params    = None

        if unique_id:
            api_url = self.server_url + '/' + end_point + '/' + unique_id

        if run_mode in ['CREATE', 'UPDATE']:
            result = self.api_requests(url=api_url, run_mode='GET', cookies=None, headers=None, payload={}, debug=debug)
            resp = result.get('resp')
            query_params = None

            if resp.status_code != 200:
                print('not found existing policy! creating a new policy config...')
            else:
                print('found existing policy! perform updating the policy config...')
                x = resp.json()
                seq_no       = x.get('_seq_no')
                primary_term = x.get('_primary_term')
                query_params = '?if_seq_no={policy_seq_no}&if_primary_term={policy_primary_term}'.format(policy_seq_no=seq_no, policy_primary_term=primary_term)

            if unique_id and query_params:
                api_url = self.server_url + '/' + end_point + '/' + unique_id + query_params

            try:
                with open(file=config_filepath, mode='r') as f:
                    tree = ast.parse(f.read())
                    aeval = asteval.Interpreter()
                    aeval(expr=tree)
                    payload = aeval.symtable.get('payload')
                    if not isinstance(payload, dict):
                        raise Exception("Not found a valid file.")

                    # ---- Start: Payload ----
                    payload = json.dumps(payload)
                    # ---- End: Payload ----

                    result = self.api_requests(url=api_url, run_mode=run_mode, cookies=None, headers=None, payload=payload, debug=debug)
            except Exception as e:
                print('***Critical Error ***:', str(e))
        else:
            result = self.api_requests(url=api_url, run_mode=run_mode, cookies=None, headers=None, payload={}, debug=debug)


    def manage_template(self, run_mode='GET', *args, **kwargs):
        debug = kwargs.get('debug', False)
        config_matrix = [
            {'config_type': '_component_template', 'path': os.path.join('destination', 'opensearch', 'component_template', 'shared', 'seagate.template.comp.generic_setting.py')},
            {'config_type': '_component_template', 'path': os.path.join('destination', 'opensearch', 'component_template', 'shared', 'seagate.template.comp.generic_mappings.py')},

            {'config_type': '_component_template', 'path': os.path.join('destination', 'opensearch', 'component_template', 'lyve', 'template.comp-lyve.cloud.system.audit.py')},
            {'config_type': '_component_template', 'path': os.path.join('destination', 'opensearch', 'component_template', 'lyve', 'template.comp-lyve.cloud.system.console.py')},
            {'config_type': '_component_template', 'path': os.path.join('destination', 'opensearch', 'component_template', 'lyve', 'template.comp-lyve.cloud.system.iam.py')},
            {'config_type': '_component_template', 'path': os.path.join('destination', 'opensearch', 'component_template', 'lyve', 'template.comp-lyve.cloud.system.parser.py')},

            {'config_type': '_index_template',     'path': os.path.join('destination', 'opensearch', 'index_template', 'lyve', 'template.index-lyve.cloud.system.audit.py')},
            {'config_type': '_index_template',     'path': os.path.join('destination', 'opensearch', 'index_template', 'lyve', 'template.index-lyve.cloud.system.console.py')},
            {'config_type': '_index_template',     'path': os.path.join('destination', 'opensearch', 'index_template', 'lyve', 'template.index-lyve.cloud.system.iam.py')},
            {'config_type': '_index_template',     'path': os.path.join('destination', 'opensearch', 'index_template', 'lyve', 'template.index-lyve.cloud.system.parser.py')},
        ]

        for item in config_matrix:
            end_point       = item['config_type']
            config_filepath = item['path']
            api_url         = self.server_url + '/' + end_point
            unique_id       = config_filepath.split('\\')[-1].replace('.py', '')
            query_params    = None

            if unique_id:
                api_url = self.server_url + '/' + end_point + '/' + unique_id

            if unique_id and query_params:
                api_url = self.server_url + '/' + end_point + '/' + unique_id + query_params

            try:
                with open(file=config_filepath, mode='r') as f:
                    tree = ast.parse(f.read())
                    aeval = asteval.Interpreter()
                    aeval(expr=tree)
                    payload = aeval.symtable.get('payload')
                    if not isinstance(payload, dict):
                        raise Exception("Not found a valid file.")

                    # ---- Start: Payload ----
                    payload = json.dumps(payload)
                    # ---- End: Payload ----

                    result = self.api_requests(url=api_url, run_mode=run_mode, cookies=None, headers=None, payload=payload, debug=debug)
            except Exception as e:
                print('***Critical Error ***:', str(e))


if __name__ == '__main__':
    pass
