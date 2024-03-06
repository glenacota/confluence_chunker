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
size_chunkenizer = RecursiveCharacterTextSplitter(chunk_size=480, chunk_overlap=10)

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
opensearch_client = OpenSearch(
    hosts = [{'host': config('OPENSEARCH_HOST', default='localhost'), 'port': config('OPENSEARCH_PORT', default=9200)}],
    http_compress = True, # enables gzip compression for request bodies
    use_ssl = False,
    verify_certs = False,
    ssl_assert_hostname = False,
    ssl_show_warn = False
)

create_index_body = {
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
            }
        }
    }
}
