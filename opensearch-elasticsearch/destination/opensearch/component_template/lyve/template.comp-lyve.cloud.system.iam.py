#PUT /_component_template/template.comp-lyve.cloud.system.iam
payload = {
  "version": 1,
  "template": {
    "mappings": {
      "properties": {
        "@timestamp": {
            "type": "date_nanos",
            "format": "strict_date_optional_time_nanos||epoch_millis||yyyy/MM/dd HH:mm:ss Z||yyyy/MM/dd Z||yyyy-MM-dd HH:mm:ss.n Z z||E, dd MMM yyyy HH:mm:ss z"
        },
        "client_id": {
          "type": "keyword"
        },
        "client_name": {
          "type": "keyword"
        },
        "connection": {
          "type": "keyword"
        },
        "connection_id": {
          "type": "keyword"
        },
        "date": {
          "type": "date_nanos",
          "format": "strict_date_optional_time_nanos||epoch_millis"
        },
        "description": {
          "type": "text"
        },
        "details": {
          "properties": {
            "allowed_logout_url": {
              "type": "text"
            },
            "body": {
              "properties": {
                "_csrf": {
                  "type": "text"
                },
                "client_id": {
                  "type": "keyword"
                },
                "confirmNewPassword": {
                  "type": "text"
                },
                "connection": {
                  "type": "keyword"
                },
                "debug": {
                  "type": "boolean"
                },
                "email": {
                  "type": "keyword"
                },
                "email_verified": {
                  "type": "boolean"
                },
                "family_name": {
                  "type": "keyword"
                },
                "given_name": {
                  "type": "keyword"
                },
                "markEmailAsVerified": {
                  "type": "boolean"
                },
                "name": {
                  "type": "text"
                },
                "newPassword": {
                  "type": "text"
                },
                "password": {
                  "type": "text"
                },
                "resultUrl": {
                  "type": "text"
                },
                "tenant": {
                  "type": "keyword"
                },
                "ticket": {
                  "type": "keyword"
                },
                "ttl_sec": {
                  "type": "long"
                },
                "verify": {
                  "type": "boolean"
                }
              }
            },
            "completedAt": {
              "type": "date_nanos",
              "format": "strict_date_optional_time_nanos||epoch_millis"
            },
            "elapsedTime": {
              "type": "long"
            },
            "error": {
              "properties": {
                "message": {
                  "type": "text"
                }
              }
            },
            "initiatedAt": {
              "type": "date_nanos",
              "format": "strict_date_optional_time_nanos||epoch_millis"
            },
            "prompts": {
              "properties": {
                "completedAt": {
                  "type": "date_nanos",
                  "format": "strict_date_optional_time_nanos||epoch_millis"
                },
                "connection": {
                  "type": "keyword"
                },
                "connection_id": {
                  "type": "keyword"
                },
                "elapsedTime": {
                  "type": "long",
                  "meta": {"unit": "nanos", "metric_type": "gauge"}
                },
                "flow": {
                  "type": "keyword"
                },
                "identity": {
                  "type": "keyword"
                },
                "initiatedAt": {
                  "type": "date_nanos",
                  "format": "strict_date_optional_time_nanos||epoch_millis"
                },
                "name": {
                  "type": "keyword"
                },
                "performed_acr": {
                  "type": "keyword"
                },
                "performed_amr": {
                  "type": "keyword"
                },
                "provider": {
                  "type": "keyword"
                },
                "session_user": {
                  "type": "keyword"
                },
                "stats.loginsCount": {
                  "type": "integer",
                  "meta": {"metric_type": "counter"}
                },
                "strategy": {
                  "type": "keyword"
                },
                "timers.rules": {
                  "type": "integer"
                },
                "user_id": {
                  "type": "text"
                },
                "user_name": {
                  "type": "keyword"
                }
              }
            },
            "query": {
              "properties": {
                "client_id": {
                  "type": "keyword"
                },
                "connection": {
                  "type": "keyword"
                },
                "email": {
                  "type": "keyword"
                },
                "includeEmailInRedirect": {
                  "type": "boolean"
                },
                "markEmailAsVerified": {
                  "type": "boolean"
                },
                "newPassword": {
                  "type": "text"
                },
                "resultUrl": {
                  "type": "text"
                },
                "tenant": {
                  "type": "keyword"
                },
                "user_id": {
                  "type": "keyword"
                },
                "username": {
                  "type": "keyword"
                }
              }
            },
            "resetUrl": {
              "type": "text"
            },
            "return_to": {
              "type": "text"
            },
            "session_id": {
              "type": "keyword"
            },
            "stats": {
              "properties": {
                "loginsCount": {
                  "type": "integer"
                }
              }
            }
          }
        },
        "hostname": {
          "type": "keyword"
        },
        "id": {
          "type": "text"
        },
        "ip": {
          "type": "ip"
        },
        "isMobile": {
          "type": "boolean"
        },
        "log_id": {
          "type": "text"
        },
        "strategy": {
          "type": "keyword"
        },
        "strategy_type": {
          "type": "keyword"
        },
        "type": {
          "type": "keyword"
        },
        "user_agent": {
          "type": "keyword"
        },
        "user_id": {
          "type": "text"
        },
        "user_name": {
          "type": "keyword"
        }
      }
    }
  }
}
