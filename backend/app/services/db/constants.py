AGGREGATIONS = [
    {
        "name": "ARTICLES_BY_SOURCE",
        "pipeline": [
            # This pipeline requires dynamic 'match_stage' built in db_service.py
            {"$match": "<MATCH_STAGE>"},
            {
                "$group": {
                    "_id": {
                        "country": "$sourceCountry",
                        "author": {
                            "$cond": {
                                "if": {
                                    "$or": [
                                        {"$eq": ["$pageAuthors", None]},
                                        {"$eq": ["$pageAuthors", ""]},
                                        {"$eq": ["$pageAuthors", []]},
                                        {"$eq": [{"$type": "$pageAuthors"}, "missing"]},
                                    ]
                                },
                                "then": "Unknown",
                                "else": "$pageAuthors",
                            }
                        },
                    },
                    "articleCount": {"$sum": 1},
                    "totalTone": {"$sum": {"$ifNull": ["$tones.overall", 0]}},
                    "lastArticleDate": {"$max": "$date.isoDate"},
                    "articles": {
                        "$push": {
                            "title": {"$ifNull": ["$pageTitle", "No Title"]},
                            "url": {"$ifNull": ["$pageUrl", "#"]},
                            "date": "$date.isoDate",
                            "tone": {"$ifNull": ["$tones.overall", 0]},
                        }
                    },
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "source": {
                        "$cond": {
                            "if": {
                                "$or": [
                                    {"$eq": ["$_id.author", None]},
                                    {"$eq": ["$_id.author", ""]},
                                    {"$eq": ["$_id.author", []]},
                                    {"$eq": ["$_id.author", "Unknown"]},
                                ]
                            },
                            "then": "Unknown",
                            "else": "$_id.author",
                        }
                    },
                    "country": {
                        "$cond": {
                            "if": {
                                "$or": [
                                    {"$eq": ["$_id.country", None]},
                                    {"$eq": ["$_id.country", ""]},
                                ]
                            },
                            "then": "Unknown",
                            "else": "$_id.country",
                        }
                    },
                    "articleCount": 1,
                    "averageTone": {"$divide": ["$totalTone", "$articleCount"]},
                    "lastArticleDate": 1,
                    "recentArticles": {"$slice": ["$articles", 5]},
                }
            },
            {"$sort": {"articleCount": -1}},
        ],
    },
    {
        "name": "GROUPED_ARTICLES",
        "pipeline": [
            # This pipeline requires dynamic 'group_field' and date filters
            {"$match": "<DATE_MATCH_STAGE>"},
            {"$limit": 10000},
            {
                "$set": {
                    "<GROUP_FIELD>": {
                        "$cond": {
                            "if": {
                                "$or": [
                                    {"$eq": ["$<GROUP_FIELD>", None]},
                                    {"$eq": ["$<GROUP_FIELD>", ""]},
                                    {"$eq": ["$<GROUP_FIELD>", []]},
                                ]
                            },
                            "then": "Unknown",
                            "else": "$<GROUP_FIELD>",
                        }
                    }
                }
            },
            # If group_field == 'pageAuthors', add:
            # {"$unwind": {"path": "$<GROUP_FIELD>", "preserveNullAndEmptyArrays": True}},
            # {"$set": {"<GROUP_FIELD>": {"$cond": { ... }}}},
            {
                "$group": {
                    "_id": "$<GROUP_FIELD>",
                    "articleCount": {"$sum": 1},
                    "totalTone": {"$sum": {"$ifNull": ["$tones.overall", 0]}},
                    "lastArticleDate": {"$max": "$date.isoDate"},
                    "articles": {
                        "$push": {
                            "title": {"$ifNull": ["$pageTitle", "No Title"]},
                            "url": {"$ifNull": ["$pageUrl", "#"]},
                            "date": "$date.isoDate",
                            "tone": {"$ifNull": ["$tones.overall", 0]},
                        }
                    },
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "name": {
                        "$cond": {
                            "if": {"$eq": ["$_id", None]},
                            "then": "Unknown",
                            "else": {"$toString": "$_id"},
                        }
                    },
                    "articleCount": 1,
                    "averageTone": {"$divide": ["$totalTone", "$articleCount"]},
                    "lastArticleDate": 1,
                    "recentArticles": {"$slice": ["$articles", 5]},
                }
            },
            {"$sort": {"articleCount": -1}},
        ],
    },
    {
        "name": "TOP_COUNTRIES_BY_ARTICLES",
        "pipeline": [
            {"$match": "<MATCH_STAGE>"},
            {"$match": {"sourceCountry": {"$exists": True, "$ne": None, "$ne": ""}}},
            {
                "$group": {
                    "_id": "$sourceCountry",
                    "value": {"$sum": 1},
                    "totalTone": {"$sum": {"$ifNull": ["$tones.overall", 0]}},
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "code": "$_id",
                    "value": 1,
                    "averageTone": {"$divide": ["$totalTone", "$value"]},
                }
            },
            {"$sort": {"value": -1}},
            {"$limit": "<LIMIT>"},
        ],
    },
    {
        "name": "GLOBAL_STATISTICS_TOTAL",
        "pipeline": [{"$group": {"_id": None, "total": {"$sum": 1}}}],
    },
    {
        "name": "GLOBAL_STATISTICS_COUNTRIES",
        "pipeline": [
            {"$match": {"sourceCountry": {"$exists": True, "$ne": None, "$ne": ""}}},
            {
                "$group": {
                    "_id": "$sourceCountry",
                    "value": {"$sum": 1},
                    "totalTone": {"$sum": {"$ifNull": ["$tones.overall", 0]}},
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "code": "$_id",
                    "value": 1,
                    "averageTone": {"$divide": ["$totalTone", "$value"]},
                    "iso2": "$_id",
                }
            },
            {"$sort": {"value": -1}},
        ],
    },
    {
        "name": "COUNTRY_DETAILS",
        "pipeline": [
            {"$match": {"sourceCountry": "<COUNTRY_CODE>"}},
            {
                "$group": {
                    "_id": "$sourceCountry",
                    "value": {"$sum": 1},
                    "totalTone": {"$sum": {"$ifNull": ["$tones.overall", 0]}},
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "code": "$_id",
                    "value": 1,
                    "averageTone": {"$divide": ["$totalTone", "$value"]},
                }
            },
        ],
    },
    {
        "name": "COUNTRY_TIME_STATS_TIMELINE",
        "pipeline": [
            {"$match": "<MATCH_STAGE>"},
            {
                "$group": {
                    "_id": {
                        "$dateToString": {
                            "format": "%Y-%m-%d",
                            "date": {
                                "$dateFromString": {
                                    "dateString": "$date.isoDate",
                                    "timezone": "UTC",
                                }
                            },
                            "timezone": "UTC",
                        }
                    },
                    "count": {"$sum": 1},
                    "total_tone": {"$sum": {"$ifNull": ["$tones.overall", 0]}},
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "date": "$_id",
                    "count": "$count",
                    "tone": {
                        "$cond": [{"$eq": ["$count", 0]}, 0, {"$divide": ["$total_tone", "$count"]}]
                    },
                }
            },
            {"$sort": {"date": 1}},
        ],
    },
    {
        "name": "COUNTRY_TIME_STATS_STATS",
        "pipeline": [
            {"$match": "<MATCH_STAGE>"},
            {
                "$facet": {
                    "stats": [
                        {
                            "$group": {
                                "_id": None,
                                "articleCount": {"$sum": 1},
                                "totalTone": {"$sum": {"$ifNull": ["$tones.overall", 0]}},
                            }
                        },
                        {
                            "$project": {
                                "_id": 0,
                                "articleCount": 1,
                                "averageTone": {
                                    "$cond": [
                                        {"$eq": ["$articleCount", 0]},
                                        0,
                                        {"$divide": ["$totalTone", "$articleCount"]},
                                    ]
                                },
                            }
                        },
                    ],
                    "articles": [
                        {"$sort": {"date.isoDate": -1}},
                        {"$limit": 10},
                        {
                            "$project": {
                                "_id": 0,
                                "title": {"$ifNull": ["$pageTitle", "No Title"]},
                                "url": {"$ifNull": ["$pageUrl", "#"]},
                                "date": "$date.isoDate",
                                "source": {"$ifNull": ["$pageAuthors", "Unknown Source"]},
                            }
                        },
                    ],
                }
            },
        ],
    },
    {
        "name": "COMPARE_TIME_PERIODS",
        "pipeline": [
            {"$match": {"date.isoDate": {"$gte": "<START_DATE>", "$lte": "<END_DATE>"}}},
            {
                "$group": {
                    "_id": {
                        "$dateToString": {
                            "format": "%Y-%m-%d",
                            "date": {
                                "$dateFromString": {
                                    "dateString": "$date.isoDate",
                                    "timezone": "UTC",
                                }
                            },
                        }
                    },
                    "articleCount": {"$sum": 1},
                    "totalTone": {"$sum": {"$ifNull": ["$tones.overall", 0]}},
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "date": "$_id",
                    "articleCount": 1,
                    "averageTone": {
                        "$cond": [
                            {"$eq": ["$articleCount", 0]},
                            0,
                            {"$divide": ["$totalTone", "$articleCount"]},
                        ]
                    },
                }
            },
            {"$sort": {"date": 1}},
        ],
    },
]

FILTERS = [
    {
        "name": "DATE_RANGE_FILTER",
        "filter": {"date.isoDate": {"$gte": "<START_DATE>", "$lte": "<END_DATE>"}},
    },
    {
        "name": "AUTHOR_FILTER",
        "filter": {
            "$expr": {
                "$cond": {
                    "if": {
                        "$or": [
                            {"$eq": ["$pageAuthors", None]},
                            {"$eq": ["$pageAuthors", ""]},
                            {"$eq": ["$pageAuthors", []]},
                        ]
                    },
                    "then": {"$eq": ["<AUTHOR>", "unknown"]},
                    "else": {
                        "$cond": {
                            "if": {"$isArray": "$pageAuthors"},
                            "then": {
                                "$in": [
                                    "<AUTHOR>",
                                    {
                                        "$map": {
                                            "input": "$pageAuthors",
                                            "as": "author",
                                            "in": {"$toLower": "$$author"},
                                        }
                                    },
                                ]
                            },
                            "else": {"$eq": [{"$toLower": "$pageAuthors"}, "<AUTHOR>"]},
                        }
                    },
                }
            }
        },
    },
    {"name": "COUNTRY_FILTER", "filter": {"sourceCountry": "<COUNTRY_CODE>"}},
    {"name": "DATE_ONLY_GTE_FILTER", "filter": {"date.isoDate": {"$gte": "<START_DATE>"}}},
    {"name": "DATE_ONLY_LTE_FILTER", "filter": {"date.isoDate": {"$lte": "<END_DATE>"}}},
]
