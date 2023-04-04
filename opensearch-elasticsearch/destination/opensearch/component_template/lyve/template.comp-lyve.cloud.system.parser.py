#PUT /_component_template/template.comp-lyve.cloud.system.parser
payload = {
  "version": 1,
  "template": {
    "mappings": {
      "properties": {
        "@timestamp"                                                    : {"type": "date_nanos"            , "format": "strict_date_optional_time_nanos||epoch_millis||yyyy-MM-dd HH:mm:ss.n Z z"},
        # "SERIAL_NUM"                                                    : {"type": "keyword"               , "ignore_above": 1024},
        # "EVENT_DATE"                                                    : {"type": "date_nanos"            , "format": "strict_date_optional_time_nanos||epoch_millis||yyyy-MM-dd HH:mm:ss.n Z z"},
        "EVENT_TYPE"                                                    : {"type": "keyword"               , "ignore_above": 1024},
        "LAST_FAIL_ID"                                                  : {"type": "keyword"               , "ignore_above": 1024},
        "LAST_FAIL_ROW"                                                 : {"type": "long"},
        "LAST_FAIL_DESC"                                                : {"type": "keyword"               , "ignore_above": 1024},
        "EXCEPTION_STATUS"                                              : {"type": "keyword"               , "ignore_above": 1024},
        "EXCEPTION_CODE"                                                : {"type": "keyword"               , "ignore_above": 1024},
        "EXCEPTION_REASON"                                              : {"type": "keyword"               , "ignore_above": 1024},
        "PROCESS_TIME"                                                  : {"type": "float"                 , "meta": {"unit": "s", "metric_type": "gauge"}},
        "INDEX_NAME"                                                    : {"type": "keyword"               , "ignore_above": 1024},
        "FILE_NAME"                                                     : {"type": "keyword"               , "ignore_above": 1024},
        "FILE_SIZE_COMPRESSED"                                          : {"type": "long"                  , "meta": {"unit": "byte", "metric_type": "gauge"}},
        "FILE_SIZE_UNCOMPRESSED"                                        : {"type": "long"                  , "meta": {"unit": "byte", "metric_type": "gauge"}},
        "FILE_LAST_MODIFIED"                                            : {"type": "date_nanos"            , "format": "strict_date_optional_time_nanos||epoch_millis||yyyy-MM-dd HH:mm:ss.n Z z"},
        "FILE_HASH"                                                     : {"type": "keyword"               , "ignore_above": 1024},
        "NUM_SAMPLES"                                                   : {"type": "long"},
        "SUCCESS_CNT"                                                   : {"type": "long"},
        "ERROR_CNT"                                                     : {"type": "long"},
        "HOST_ADDR"                                                     : {"type": "ip"},
        "HOST_NAME"                                                     : {"type": "keyword"               , "ignore_above": 1024},
        "HOST_PORT"                                                     : {"type": "keyword"               , "ignore_above": 1024},
        "REMOTE_ADDR"                                                   : {"type": "ip"},
        "REMOTE_PORT"                                                   : {"type": "keyword"               , "ignore_above": 1024},
        "REQUEST_METHOD"                                                : {"type": "keyword"               , "ignore_above": 1024},
        "REQUEST_URI"                                                   : {"type": "keyword"               , "ignore_above": 1024},
        "REQUEST_URL_SCHEME"                                            : {"type": "keyword"               , "ignore_above": 1024},
        "USER_AGENT"                                                    : {"type": "keyword"               , "ignore_above": 1024},
        "SEND_TO_ELK"                                                   : {"type": "keyword"               , "ignore_above": 1024}
      }
    }
  }
}
