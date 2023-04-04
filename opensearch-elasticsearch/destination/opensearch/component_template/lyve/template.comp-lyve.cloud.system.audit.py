#PUT /_component_template/template.comp-lyve.cloud.system.audit
payload = {
  "version": 1,
  "template": {
    "mappings": {
      "properties": {
        "@timestamp": {
            "type": "date_nanos",
            "format": "strict_date_optional_time_nanos||epoch_millis||yyyy/MM/dd HH:mm:ss Z||yyyy/MM/dd Z||yyyy-MM-dd HH:mm:ss.n Z z||E, dd MMM yyyy HH:mm:ss z"
        },
        "auditEntry": {
          "properties": {
            "api": {
              "properties": {
                "bucket": {
                  "type": "keyword"
                },
                "name": {
                  "type": "keyword"
                },
                "object": {
                  "type": "text"
                },
                "status": {
                  "type": "keyword"
                },
                "statusCode": {
                  "type": "keyword"
                },
                "timeToFirstByte": {
                  "type": "long",
                  #"meta": {"unit": "nanos", "metric_type": "gauge"}
                },
                "timeToResponse": {
                  "type": "long",
                  #"meta": {"unit": "nanos", "metric_type": "gauge"}
                }
              }
            },
            "deploymentid": {
              "type": "keyword"
            },
            "remotehost": {
              "type": "keyword"
            },
            "requestHeader": {
              "properties": {
                "Accept": {
                  "type": "keyword"
                },
                "Accept-Encoding": {
                  "type": "keyword"
                },
                "Accept-Language": {
                  "type": "keyword"
                },
                "Amz-Sdk-Invocation-Id": {
                  "type": "keyword"
                },
                "Amz-Sdk-Request": {
                  "type": "text"
                },
                "Amz-Sdk-Retry": {
                  "type": "text"
                },
                "Authorization": {
                  "type": "text"
                },
                "Content-Length": {
                  "type": "long",
                  #"meta": {"unit": "byte", "metric_type": "gauge"}
                },
                "Content-Md5": {
                  "type": "text"
                },
                "Content-Type": {
                  "type": "keyword"
                },
                "Cookie": {
                  "type": "text"
                },
                "Date": {
                  "type": "date_nanos",
                  "format": "strict_date_optional_time||E, dd MMM yyyy HH:mm:ss z"
                },
                "Delimiter": {
                  "type": "keyword"
                },
                "Dnt": {
                  "type": "integer"
                },
                "If-Match": {
                  "type": "text"
                },
                "Postman-Token": {
                  "type": "text"
                },
                "Prefix": {
                  "type": "keyword"
                },
                "Range": {
                  "type": "text"
                },
                "Referer": {
                  "type": "keyword"
                },
                "Sec-Ch-Ua": {
                  "type": "text"
                },
                "Sec-Ch-Ua-Mobile": {
                  "type": "keyword"
                },
                "Sec-Ch-Ua-Platform": {
                  "type": "keyword"
                },
                "Sec-Fetch-Dest": {
                  "type": "keyword"
                },
                "Sec-Fetch-Mode": {
                  "type": "keyword"
                },
                "Sec-Fetch-Site": {
                  "type": "keyword"
                },
                "Sec-Fetch-User": {
                  "type": "keyword"
                },
                "Upgrade-Insecure-Requests": {
                  "type": "long"
                },
                "User-Agent": {
                  "type": "keyword"
                },
                "X-Amz-Acl": {
                  "type": "keyword"
                },
                "X-Amz-Bucket-Object-Lock-Enabled": {
                  "type": "boolean"
                },
                "X-Amz-Content-Sha256": {
                  "type": "keyword"
                },
                "X-Amz-Date": {
                  "type": "date_nanos",
                  "format": "basic_date_time_no_millis||strict_date_optional_time||E, dd MMM yyyy HH:mm:ss z"
                },
                "X-Amz-Meta-Cvsizeinfo": {
                  "type": "keyword"
                },
                "X-Amz-Meta-Cvsubfileinfo": {
                  "type": "long"
                },
                "X-Amz-Meta-Fl-Original-Last-Modified": {
                  "type": "date_nanos",
                  "format": "strict_date_optional_time_nanos||strict_date_optional_time||epoch_millis"
                },
                "X-Amz-Meta-Keyname1": {
                  "type": "keyword"
                },
                "X-Amz-Meta-Keyname2": {
                  "type": "keyword"
                },
                "X-Amz-Meta-Mtime": {
                  "type": "date_nanos",
                  "format": "strict_date_optional_time_nanos||epoch_millis"
                },
                "X-Amz-Meta-S3b-Last-Modified": {
                  "type": "date_nanos",
                  "format": "basic_date_time_no_millis||strict_date_optional_time||E, dd MMM yyyy HH:mm:ss z"
                },
                "X-Amz-Meta-Sha256": {
                  "type": "text"
                },
                "X-Amz-Replication-Status": {
                  "type": "keyword"
                },
                "X-Amz-Server-Side-Encryption": {
                  "type": "keyword"
                },
                "X-Amz-Storage-Class": {
                  "type": "keyword"
                },
                "X-Forwarded-For": {
                  "type": "text",
                  "fielddata": True
                },
                "X-Forwarded-Host": {
                  "type": "keyword"
                },
                "X-Forwarded-Port": {
                  "type": "integer"
                },
                "X-Forwarded-Proto": {
                  "type": "keyword"
                },
                "X-Minio-Source-Etag": {
                  "type": "text"
                },
                "X-Minio-Source-Mtime": {
                  "type": "date_nanos",
                  "format": "strict_date_optional_time_nanos||strict_date_optional_time||epoch_millis"
                },
                "X-Real-Ip": {
                  "type": "keyword"
                },
                "X-Time": {
                  "type": "date_nanos",
                  "format": "strict_date_optional_time_nanos||epoch_millis"
                }
              }
            },
            "requestID": {
              "type": "keyword"
            },
            "requestQuery": {
              "properties": {
                "Range": {
                  "type": "text"
                },
                "Range:bytes": {
                  "type": "text"
                },
                "X-Amz-Algorithm": {
                  "type": "keyword"
                },
                "X-Amz-Credential": {
                  "type": "keyword"
                },
                "X-Amz-Date": {
                  "type": "date_nanos",
                  "format": "basic_date_time_no_millis||strict_date_optional_time||E, dd MMM yyyy HH:mm:ss z"
                },
                "X-Amz-Expires": {
                  "type": "long"
                },
                "X-Amz-Signature": {
                  "type": "keyword"
                },
                "X-Amz-SignedHeaders": {
                  "type": "keyword"
                },
                "accessKey": {
                  "type": "keyword"
                },
                "acl": {
                  "type": "keyword"
                },
                "arn": {
                  "type": "keyword"
                },
                "bucket": {
                  "type": "keyword"
                },
                "continuation-token": {
                  "type": "keyword"
                },
                "count": {
                  "type": "integer"
                },
                "delete": {
                  "type": "keyword"
                },
                "delimiter": {
                  "type": "keyword"
                },
                "encoding-type": {
                  "type": "keyword"
                },
                "encryption": {
                  "type": "keyword"
                },
                "fetch-owner": {
                  "type": "boolean"
                },
                "isGroup": {
                  "type": "boolean"
                },
                "lifecycle": {
                  "type": "keyword"
                },
                "list-type": {
                  "type": "keyword"
                },
                "location": {
                  "type": "keyword"
                },
                "logging": {
                  "type": "keyword"
                },
                "marker": {
                  "type": "keyword"
                },
                "max-keys": {
                  "type": "integer"
                },
                "name": {
                  "type": "keyword"
                },
                "notification": {
                  "type": "keyword"
                },
                "object-lock": {
                  "type": "keyword"
                },
                "partNumber": {
                  "type": "keyword"
                },
                "policy": {
                  "type": "keyword"
                },
                "policyName": {
                  "type": "keyword"
                },
                "prefix": {
                  "type": "keyword"
                },
                "replication": {
                  "type": "keyword"
                },
                "requestPayment": {
                  "type": "keyword"
                },
                "retention": {
                  "type": "keyword"
                },
                "select": {
                  "type": "keyword"
                },
                "select-type": {
                  "type": "keyword"
                },
                "stale": {
                  "type": "boolean"
                },
                "status": {
                  "type": "keyword"
                },
                "tagging": {
                  "type": "keyword"
                },
                "type": {
                  "type": "keyword"
                },
                "uploadId": {
                  "type": "keyword"
                },
                "uploads": {
                  "type": "keyword"
                },
                "userOrGroup": {
                  "type": "keyword"
                },
                "versionId": {
                  "type": "keyword"
                },
                "versioning": {
                  "type": "keyword"
                },
                "versions": {
                  "type": "keyword"
                }
              }
            },
            "responseHeader": {
              "properties": {
                "Accept-Ranges": {
                  "type": "keyword"
                },
                "Cache-Control": {
                  "type": "keyword"
                },
                "Content-Length": {
                  "type": "long",
                  #"meta": {"unit": "byte", "metric_type": "gauge"}
                },
                "Content-Range": {
                  "type": "keyword"
                },
                "Content-Security-Policy": {
                  "type": "keyword"
                },
                "Content-Type": {
                  "type": "keyword"
                },
                "Date": {
                  "type": "date_nanos",
                  "format": "strict_date_optional_time||E, dd MMM yyyy HH:mm:ss z"
                },
                "ETag": {
                  "type": "keyword"
                },
                "Last-Modified": {
                  "type": "date_nanos",
                  "format": "strict_date_optional_time||E, dd MMM yyyy HH:mm:ss z"
                },
                "Location": {
                  "type": "text"
                },
                "Server": {
                  "type": "text"
                },
                "Vary": {
                  "type": "keyword"
                },
                "X-Accel-Buffering": {
                  "type": "keyword"
                },
                "X-Amz-Bucket-Region": {
                  "type": "keyword"
                },
                "X-Amz-Object-Lock-Mode": {
                  "type": "keyword"
                },
                "X-Amz-Object-Lock-Retain-Until-Date": {
                  "type": "date_nanos",
                  "format": "strict_date_optional_time_nanos||strict_date_optional_time||epoch_millis"
                },
                "X-Amz-Replication-Status": {
                  "type": "keyword"
                },
                "X-Amz-Request-Id": {
                  "type": "keyword"
                },
                "X-Amz-Server-Side-Encryption": {
                  "type": "keyword"
                },
                "X-Xss-Protection": {
                  "type": "keyword"
                },
                "x-amz-delete-marker": {
                  "type": "boolean"
                },
                "x-amz-meta-cvsizeinfo": {
                  "type": "keyword"
                },
                "x-amz-meta-cvsubfileinfo": {
                  "type": "long"
                },
                "x-amz-meta-fl-original-last-modified": {
                  "type": "date_nanos",
                  "format": "strict_date_optional_time_nanos||strict_date_optional_time||epoch_millis"
                },
                "x-amz-meta-mtime": {
                  "type": "date_nanos",
                  "format": "strict_date_optional_time_nanos||epoch_millis"
                },
                "x-amz-meta-s3b-last-modified": {
                  "type": "date_nanos",
                  "format": "basic_date_time_no_millis||strict_date_optional_time||E, dd MMM yyyy HH:mm:ss z"
                },
                "x-amz-meta-sha256": {
                  "type": "keyword"
                },
                "x-amz-version-id": {
                  "type": "keyword"
                }
              }
            },
            "time": {
              "type": "date_nanos",
              "format": "strict_date_optional_time_nanos||epoch_millis"
            },
            "userAgent": {
              "type": "text",
              "fields": {
                "keyword": {
                  "type": "keyword",
                  "ignore_above": 1024
                }
              }
            },
            "version": {
              "type": "keyword"
            }
          }
        },
        "serviceAccountCreatorId": {
          "type": "keyword"
        },
        "serviceAccountName": {
          "type": "keyword"
        },
        "HTTP_STATUS_CODE_MSG": {
            "type": "keyword"
        }
      }
    }
  }
}
