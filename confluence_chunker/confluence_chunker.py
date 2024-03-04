import os
import logging
import click
import json

from config import confluence
from config import size_chunkenizer, html_chunkenizer
from config import opensearch_client
from lxml import etree, html

# initialise logger
log_level = os.environ.get("LOG_LEVEL", "INFO")
logger = logging.getLogger(__name__)
logger.setLevel(log_level)

def parse_html_body(html_body_to_parse):
    tree = etree.fromstring(html_body_to_parse, etree.HTMLParser())
    etree.strip_tags(tree, 'span', 'strong')
    for element in tree.iter():
        element.attrib.clear()
    parsed_html = etree.tostring(tree, encoding='unicode', method='html').replace("\n","")
    return parsed_html

def chunkenize_html(text):
    document_chunks = html_chunkenizer.split_text(text)
    document_chunks = size_chunkenizer.split_documents(document_chunks)
    return [combine_html_doc_chunk(doc) for doc in document_chunks]

def combine_html_doc_chunk(document):
    return " - ".join(document.dict()["metadata"].values()) + ' - ' + document.dict()["page_content"]

def chunkenize_by_method(method, text):
    match method:
        case 'none':
            return [text]
        case 'nocontext':
            return size_chunkenizer.split_text(text)
        case 'html':
            return chunkenize_html(text)
        case _:
            return [text]

def map_chunks_to_json(confluence_rest_response, chunks):
    return [map_chunk_to_json(confluence_rest_response, chunk) for chunk in chunks]

def map_chunk_to_json(confluence_rest_response, chunk):
    return json.dumps({
        "title": confluence_rest_response['title'],
        "url": confluence_rest_response['_links']['base'] + confluence_rest_response['_links']['tinyui'],
        "chunk": chunk
    })

@click.command()
@click.option('--pageid', prompt='Page id', default='137729483', help='The id of the wiki page to process.')
@click.option('--method', prompt='Chunking method (none|nocontext|html)', default='none', help='The method applied by the chunkenizer.')  
@click.option('--opensearch_index', help='The OpenSearch index whereto ingest the chunk data.')
def run(pageid, method, opensearch_index):
    response = confluence.get_page_by_id(pageid,expand="body.export_view")
    html_body = parse_html_body(response['body']['export_view']['value'])
    chunks = chunkenize_by_method(method, html_body)
    logger.info('Number of chunks created for page id %s: %s', pageid, len(chunks))
    chunks_as_json = map_chunks_to_json(chunks)

    if (opensearch_index):
        [opensearch_client.index(index=opensearch_index, body=chunk) for chunk in chunks_as_json]
    
    # print chunks
    [print(chunk) for chunk in chunks_as_json]
