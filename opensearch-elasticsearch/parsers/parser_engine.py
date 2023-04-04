# Copyright (c) 2021 Seagate Technology LLC and/or its Affiliates
import gzip
import json
from helpers.utils import fatdict
from .enums import Action
from . import NEWLINE


class LogParser:
    __filename = ''
    __filehash = ''
    __logs = []


    def load(self, buffer, filename='', filehash=''):
        self.__filename = filename
        self.__filehash = filehash

        buffer.seek(0)

        with gzip.open(buffer, 'r') as f:
            content = f.read().decode('UTF-8')
            lines = content.split(NEWLINE)
            for line in lines:
                if line:
                    log = json.loads(line)
                    self.__logs.append(log)


    def getLogs(self):
        logs = []
        for l in self.__logs:
            logs.append(fatdict(l))
        return logs


    def getSize(self):
        return len(self.__logs)


    def getFilename(self):
        return self.__filename


    def getFilehash(self):
        if not self.__filehash:
            return self.__filename
        return self.__filehash
