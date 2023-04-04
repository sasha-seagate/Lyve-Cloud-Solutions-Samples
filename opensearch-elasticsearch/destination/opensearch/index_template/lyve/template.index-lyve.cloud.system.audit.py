# POST _index_template/template.index-lyve.cloud.system.audit
payload = {
    "version": 1,
    "priority": 2,
    "index_patterns": [
        "lyve.cloud.system.audit-*"
    ],
    "data_stream": {
        "timestamp_field": {
            "name": "@timestamp"
            #"name": "auditEntry.time"
        }
    },
    "template": {},
    "composed_of": [
        "seagate.template.comp.generic_setting",
        "seagate.template.comp.generic_mappings",
        "template.comp-lyve.cloud.system.audit"
    ],
    "_meta": {
        "description": "This data streams index template is optimized for factory time-series data.",
        "author": "508399",
        "department": "Korat Drive Operation",
        "company": "Seagate Technology",
        "confidentiality": "Seagate Confidential",
        "policy": {
            "11-9200": "Data Classification Policy",
            "07-600.07": "IT Classified Data Handling Standard"
        }
    }
}