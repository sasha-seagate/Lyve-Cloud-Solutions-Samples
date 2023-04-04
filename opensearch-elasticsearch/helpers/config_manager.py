# Copyright (c) 2021 Seagate Technology LLC and/or its Affiliates

import yaml
import functools


class Config_Manager():
    def __init__(self, config_filename, *args, **kwargs):
        self.cfg = None

        with open(file=config_filename, mode="r") as f:
            self.cfg = yaml.load(f, Loader=yaml.FullLoader)


    def get(self, key, default=None):
        try:
            return functools.reduce(lambda c, k: c[k], key.split('.'), self.cfg)
        except:
            return default


cfg = Config_Manager(config_filename='config.yaml')


if __name__ == '__main__':
    cfg = Config_Manager(config_filename='config.yaml')

    c1   = cfg.get('password', 'not found')
    print(type(c1))
    print(c1)

    c2 = cfg.get('elasticsearch.api_key_value', None)
    print(c2)
