# GET    _component_template/seagate.template.comp.generic_setting
# DELETE _component_template/seagate.template.comp.generic_setting
# PUT    _component_template/seagate.template.comp.generic_setting

payload = {
    "version": 1,
    "template": {
        "settings": {
            # ---- STATIC INDEX SETTINGS ----
            # Number of primary shards should be 2x number of data nodes
            "index.number_of_shards": 3,
            # "index.shard.check_on_startup": True,
            # "index.codec": "default",
            # "index.soft_deletes.retention_lease.period": "24h",
            # "index.hidden": "False",

            # ---- DYNAMIC INDEX SETTINGS ----
            "index.number_of_replicas": 1,
            # "index.auto_expand_replicas": False,
            # "index.refresh_interval": "1s",

            # for ELK
            # "index.lifecycle.name": "seagate-ilm-regular-retention-24-hours",
            # "index.lifecycle.rollover_alias": "mylog",

            # for Opensearch
            # "index.plugins.index_state_management.policy_id": "seagate-ilm-stream-retention-30d",
            # "index.plugins.index_state_management.rollover_alias": "mylog",
            # "index.plugins.index_state_management.rollover_skip": False,


            "index.default_pipeline": "validate_complex_data",
            "index.mapping.total_fields.limit": 10000,
            "index.mapping.depth.limit": 100,
            "index.mapping.nested_fields.limit": 1000,
            "index.mapping.nested_objects.limit": 10000,
            # "index.sort.field": ["EVENT_DATE", "EVENT_TYPE",],
            # "index.sort.order": ["desc", "asc",],
            # "index.priority": "1",
            # "index.query.default_field": ["EVENT.*"],
            # "index.routing.allocation.total_shards_per_node" : 1
        }
    },
    "_meta": {
        "description"    : "A general setting optimized for high data throughput.",
        "author"         : "508399",
        "department"     : "Korat Drive Operation",
        "company"        : "Seagate Technology",
        "confidentiality": "Seagate Confidential",
        "policy": {
            "11-9200": "Data Classification Policy",
            "07-600.07": "IT Classified Data Handling Standard"
        }
    }
}
