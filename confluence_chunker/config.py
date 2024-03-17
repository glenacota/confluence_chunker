from decouple import config
from atlassian import Confluence
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.text_splitter import HTMLHeaderTextSplitter
from langchain.text_splitter import MarkdownHeaderTextSplitter
from opensearchpy import OpenSearch

### Confluence client
confluence = Confluence(url=config('CONFLUENCE_URL'), token=config('CONFLUENCE_TOKEN'), timeout=300)

### Chunkenizers
# Create chunks by number of characters and ignoring the text context
size_chunkenizer = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=12)

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

# Create chunks from markdown
_md_heeaders_to_split_on = [
    ("#", "Header 1"),
    ("##", "Header 2"),
    ("###", "Header 3"),
    ("####", "Header 4"),
    ("#####", "Header 5")
]
md_chunkenizer = MarkdownHeaderTextSplitter(headers_to_split_on=_md_heeaders_to_split_on,strip_headers=False)

### OpenSearch client - assume no auth
class OSClient:
    DEFAULT_INDEX_SETTINGS = {
        "settings": {
            "number_of_shards": 1,
            "number_of_replicas": 0,
            "refresh_interval": "30s"
        },
        "mappings": {
            "properties": {
                "chunk": {
                    "type": "text"
                },
                "title": {
                    "type": "keyword"
                },
                "url": {
                    "type": "object",
                    "enabled": False
                },
                "createdDate": {
                    "type": "date"
                },
                "updatedDate": {
                    "type": "date"
                }
            }
        }
    }

    def __init__(self, index_name):
        self.client = OpenSearch(
            hosts = [{'host': config('OPENSEARCH_HOST', default='localhost'), 'port': config('OPENSEARCH_PORT', default=9200)}],
            http_compress = True, # enables gzip compression for request bodies
            use_ssl = False,
            verify_certs = False,
            ssl_assert_hostname = False,
            ssl_show_warn = False
        )
        self.index_name = index_name
        self._init_index()

    def _init_index(self):
        if not self.client.indices.exists(index=self.index_name):
            self.client.indices.create(index=self.index_name, body=self.DEFAULT_INDEX_SETTINGS)

    def index(self, data):
        self.client.index(index=self.index_name, body=data)
