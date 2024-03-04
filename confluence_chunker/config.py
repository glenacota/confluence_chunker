from decouple import config
from atlassian import Confluence
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.text_splitter import HTMLHeaderTextSplitter
from opensearchpy import OpenSearch

### Confluence client
confluence = Confluence(url=config('CONFLUENCE_URL'), token=config('CONFLUENCE_TOKEN'), timeout=300)

### Chunkenizers
# Create chunks by number of characters and ignoring the text context
size_chunkenizer = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=20)

# Create chunks by html tags
_html_heeaders_to_split_on = [
    ("h1", "Header 1"),
    ("h2", "Header 2"),
    ("h3", "Header 3"),
    ("h4", "Header 4"),
    ("h5", "Header 5"),
    ("table", "Table")
]
html_chunkenizer = HTMLHeaderTextSplitter(headers_to_split_on=_html_heeaders_to_split_on)

### OpenSearch client - assume no auth
opensearch_client = OpenSearch(
    hosts = [{'host': config('OPENSEARCH_HOST'), 'port': config('OPENSEARCH_PORT')}],
    http_compress = True, # enables gzip compression for request bodies
    use_ssl = False,
    verify_certs = False,
    ssl_assert_hostname = False,
    ssl_show_warn = False
)

create_index_body = {
    "settings": {
        "index": {
            "search.default_pipeline": config('OPENSEARCH_SEARCH_PIPELINE_NAME'),
            "knn": True,
            "default_pipeline": config('OPENSEARCH_INGEST_PIPELINE_NAME')
        }
    },
    "mappings": {
        "properties": {
            "chunk": {
                "type": "text"
            },
            "title": {
                "type": "text",
                "fields": {
                    "keyword": {
                        "type": "keyword"
                    }
                }
            },
            "url": {
                "type": "keyword"
            },
            "passage_embedding": {
                "type": "knn_vector",
                "dimension": 768,
                "method": {
                    "engine": "lucene",
                    "space_type": "l2",
                    "name": "hnsw",
                    "parameters": {}
                }
            }
        }
    }
    }