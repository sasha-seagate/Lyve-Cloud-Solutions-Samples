#PUT /_component_template/template.comp-lyve.cloud.system.console
payload = {
  "version": 1,
  "template": {
    "mappings": {
      "properties": {
        "@timestamp": {
            "type": "date_nanos",
            "format": "strict_date_optional_time_nanos||epoch_millis||yyyy/MM/dd HH:mm:ss Z||yyyy/MM/dd Z||yyyy-MM-dd HH:mm:ss.n Z z||E, dd MMM yyyy HH:mm:ss z"
        },
        "AccountID": {
          "type": "keyword"
        },
        "ConsoleEvent": {
          "properties": {
            "EventResponse": {
              "type": "text"
            },
            "EventTime": {
              "type": "date_nanos",
              "format": "strict_date_optional_time_nanos||epoch_millis||yyyy-MM-dd HH:mm:ss.n Z z"
            },
            "Eventname": {
              "type": "keyword"
            },
            "Status": {
              "type": "text",
              "fields": {
                "keyword": {
                  "type": "keyword",
                  "ignore_above": 1024
                }
              }
            },
            "StatusCode": {
              "type": "keyword"
            }
          }
        },
        "ConsoleVersion": {
          "type": "text",
          "fields": {
            "keyword": {
              "type": "keyword",
              "ignore_above": 1024
            }
          }
        },
        "LoginTime": {
          "type": "date_nanos",
          "format": "strict_date_optional_time_nanos||epoch_millis||yyyy-MM-dd HH:mm:ss.n Z z"
        },
        "UserIdentity": {
          "properties": {
            "EventSource": {
              "type": "text",
              "fields": {
                "keyword": {
                  "type": "keyword",
                  "ignore_above": 1024
                }
              }
            },
            "Role": {
              "type": "keyword"
            },
            "UserName": {
              "type": "keyword"
            }
          }
        }
      }
    }
  }
}
