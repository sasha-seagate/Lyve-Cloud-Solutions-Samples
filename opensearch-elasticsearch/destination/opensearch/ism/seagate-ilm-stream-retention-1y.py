# PUT _plugins/_ism/policies/seagate-ilm-stream-retention-1y
payload = {
    "policy": {
        "policy_id": "seagate-ilm-stream-retention-1y",
        "description": "Data stream index, 1y data retention. Optimized for streaming time-series, append-only data.",
        "last_updated_time": None,
        "schema_version": 1,
        "error_notification": None,
        "default_state": "hot",
        "states": [
            {
                "name": "hot",
                "actions": [
                    {
                        "timeout": "7d",
                        "retry": {
                            "count": 3,
                            "backoff": "exponential",
                            "delay": "10m"
                        },
                        "index_priority": {
                            "priority": 100
                        }
                    },
                    {
                        "timeout": "7d",
                        "retry": {
                            "count": 3,
                            "backoff": "exponential",
                            "delay": "10m"
                        },
                        "replica_count": {
                            "number_of_replicas": 1
                        }
                    },
                    {
                        "timeout": "7d",
                        "retry": {
                            "count": 3,
                            "backoff": "exponential",
                            "delay": "10m"
                        },
                        "rollover": {
                            "min_size": "50gb",
                            "min_doc_count": 10000000,
                            "min_index_age": "30d"
                        }
                    }
                ],
                "transitions": [
                    {
                        "state_name": "warm"
                    }
                ]
            },
            {
                "name": "warm",
                "actions": [
                    {
                        "timeout": "7d",
                        "retry": {
                            "count": 3,
                            "backoff": "exponential",
                            "delay": "10m"
                        },
                        "index_priority": {
                            "priority": 50
                        }
                    }
                ],
                "transitions": [
                    {
                        "state_name": "cold",
                        "conditions": {
                            "min_index_age": "92d"
                        }
                    }
                ]
            },
            {
                "name": "cold",
                "actions": [
                    {
                        "timeout": "7d",
                        "retry": {
                            "count": 3,
                            "backoff": "exponential",
                            "delay": "10m"
                        },
                        "index_priority": {
                            "priority": 1
                        }
                    },
                    {
                        "timeout": "7d",
                        "retry": {
                            "count": 3,
                            "backoff": "exponential",
                            "delay": "10m"
                        },
                        "replica_count": {
                            "number_of_replicas": 0
                        }
                    },
                    {
                        "timeout": "7d",
                        "retry": {
                            "count": 3,
                            "backoff": "exponential",
                            "delay": "10m"
                        },
                        "read_only": {}
                    }
                ],
                "transitions": [
                    {
                        "state_name": "close",
                        "conditions": {
                            "min_index_age": "183d"
                        }
                    }
                ]
            },
            {
                "name": "close",
                "actions": [
                    {
                        "timeout": "7d",
                        "retry": {
                            "count": 3,
                            "backoff": "exponential",
                            "delay": "10m"
                        },
                        "close": {}
                    }
                ],
                "transitions": [
                    {
                        "state_name": "awaiting_delete",
                        "conditions": {
                            "min_index_age": "365d"
                        }
                    }
                ]
            },
            {
                "name": "awaiting_delete",
                "actions": [],
                "transitions": [
                    {
                        "state_name": "delete",
                        "conditions": {
                            "min_index_age": "366d"
                        }
                    }
                ]
            },
            {
                "name": "delete",
                "actions": [
                    {
                        "timeout": "7d",
                        "retry": {
                            "count": 3,
                            "backoff": "exponential",
                            "delay": "10m"
                        },
                        "delete": {}
                    }
                ],
                "transitions": []
            }
        ],
        "ism_template": [
            {
                "index_patterns": [
                    "lyve.*"
                ],
                "priority": 2,
                "last_updated_time": None
            }
        ]
    }
}