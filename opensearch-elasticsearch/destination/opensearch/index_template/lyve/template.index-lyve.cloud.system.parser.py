# POST _index_template/template.index-lyve.cloud.system.parser
payload = {
    "version": 1,
    "priority": 2,
    "index_patterns": [
        "lyve.cloud.system.parser-*"
    ],
    "data_stream": {
        "timestamp_field": {
            "name": "@timestamp"
        }
    },
    "template": {},
    "composed_of": [
        "seagate.template.comp.generic_setting",
        "seagate.template.comp.generic_mappings",
        "template.comp-lyve.cloud.system.parser"
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