from enum import Enum

class Action(Enum):
    toDF            = 'dataframe'
    toInflux        = 'influxdb'
    toElasticSearch = 'elasticsearch'
    toOpenSearch    = 'opensearch'
