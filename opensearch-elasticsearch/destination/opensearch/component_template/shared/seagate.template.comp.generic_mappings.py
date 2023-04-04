# GET    _component_template/seagate.template.comp.generic_mappings
# DELETE _component_template/seagate.template.comp.generic_mappings
# PUT    _component_template/seagate.template.comp.generic_mappings
# Ref: https://logz.io/blog/elasticsearch-mapping/

payload = {
    "version": 1,
    "template": {
        "mappings": {
            "numeric_detection": True,
            "date_detection": True,
            "dynamic_date_formats": [
                "strict_date_optional_time",
                "strict_date_optional_time_nanos",
                "yyyy/MM/dd HH:mm:ss Z||yyyy/MM/dd Z",
                "yyyy-MM-dd HH:mm:ss.n Z z",
                "E, dd MMM yyyy HH:mm:ss z"
            ],
            "dynamic": True,
            "dynamic_templates": [
                {
                  "spc_as_numeric" : {
                    "match_mapping_type" : "*",
                    "match"              : "*.SPC.*",
                    "mapping"            : {"type" : "float", "norms": False,}
                  }
                },
                {
                  "strings_as_keywords": {
                    "match_mapping_type" : "string",
                    "mapping"            : {"type" : "keyword", "ignore_above": 1024}
                  }
                },
                #{
                #  "strings_as_fulltext": {
                #    "match_mapping_type" : "string",
                #    "mapping"            : {"type" : "text", "fields": {"raw": {"type":  "keyword", "ignore_above": 1024}}}
                #  }
                #}
            ],
            "_meta": {
                "description"    : "Enforcing constraints to ensure data reliability. It's similar to the ACID (atomicity, consistency, isolation, and durability) concept in RDBMS.",
                "author"         : "508399",
                "department"     : "Korat Drive Operation",
                "company"        : "Seagate Technology",
                "confidentiality": "Seagate Confidential",
                "policy": {
                    "11-9200"  : "Data Classification Policy",
                    "07-600.07": "IT Classified Data Handling Standard"
                }
            },
            "_routing": {"required": False},
            "_source": {
                "excludes": [],
                "includes": [],
                "enabled": True
            },

            # Runtime fields are not indexed or stored but will be searchable, sortable, aggregable and filterable.
            #"runtime": {
            #    "@timestamp": {
            #        "type": "date_nanos",
            #        "script": {
            #            "lang": "painless",
            #            "source": "ctx._source['EVENT.START_TIME']"
            #        }
            #    }
            #},

            # Data Type Mapping. Shall be defined individually.
            "properties": {}
        }
    }
}
