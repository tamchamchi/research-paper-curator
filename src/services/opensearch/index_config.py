ARXIV_PAPERS_INDEX = "arxiv-papers"

# Index mapping configuration for arXiv papers in OpenSearch
ARXIV_PAPERS_INDEX_MAPPING = {
    "settings": {
        "index.number_of_shards": 1,  # The number of primary shards in the index
        "index.number_of_replicas": 0,  # The number of replica shards
        "analysis": {
            "analyzer": {
                "standard_analyzer": {"type": "standard", "stopwords": "_english_"},
                "text_analyzer": {
                    "type": "custom",
                    "tokenizer": "standard",
                    "filter": ["lowercase", "stop", "snowball"],
                },
            }
        },
    },
    "mappings": {
        "dynamic": "strict",  # Disallow fields not defined in the mapping
        "properties": {
            "arxiv_id": {"type": "keyword"},  # Unique identifier for the paper
            "title": {
                "type": "text",
                "analyzer": "text_analyzer",
                "fields": {"keyword": {"type": "keyword", "ignore_above": 256}},
            },  # Title of the paper
            "authors": {
                "type": "text",
                "analyzer": "standard_analyzer",
                "fields": {"keyword": {"type": "keyword", "ignore_above": 256}},
            },  # Authors of the paper
            "abstract": {
                "type": "text",
                "analyzer": "text_analyzer",
            },  # Abstract of the paper
            "categories": {
                "type": "keyword"
            },  # Categories assigned to the paper (e.g., cs.AI, cs.LG)
            "raw_text": {
                "type": "text",
                "analyzer": "text_analyzer",
            },  # Full text of the paper
            "pdf_url": {"type": "keyword"},  # URL to the PDF version of the paper
            "published_date": {"type": "date"},  # Publication date of the paper
            "created_at": {"type": "date"},  # Timestamp when the document was indexed
            "updated_at": {
                "type": "date"
            },  # Timestamp when the document was last updated
        },
    },
}
