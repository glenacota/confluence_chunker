from decouple import config
from atlassian import Confluence
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.text_splitter import HTMLHeaderTextSplitter

# Confluence client
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