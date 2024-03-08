import os, sys
import logging
import click
import json
import markdownify

from config import confluence
from config import size_chunkenizer, html_chunkenizer, md_chunkenizer
from config import opensearch_client, create_index_body
from lxml import etree

log_level = os.environ.get("LOG_LEVEL", "INFO")
logging.basicConfig(stream=sys.stdout, level=log_level)
logger = logging.getLogger(__name__)
logger.setLevel(log_level)

def parse_html_body(html_body_to_parse):
    if not html_body_to_parse:
        return "" 
    tree = etree.fromstring(html_body_to_parse, etree.HTMLParser())
    etree.strip_tags(tree, 'span', 'strong', 'a', 'div', 'thead', 'tbody')
    etree.strip_elements(tree, 'img')
    for element in tree.iter():
        element.attrib.clear()
    parsed_html = etree.tostring(tree, encoding='unicode', method='html').replace("\n","")
    return parsed_html

def chunkenize_html(text):
    document_chunks = html_chunkenizer.split_text(text)
    document_chunks = size_chunkenizer.split_documents(document_chunks)
    return [combine_html_doc_chunk(doc) for doc in document_chunks]

# this is to retain section context in chunks
def combine_html_doc_chunk(document):
    return " - ".join(document.dict()["metadata"].values()) + ' - ' + document.dict()["page_content"]

def chunkenize_markdown(text):
    markdown_text = markdownify.markdownify(text)
    md_chunks = md_chunkenizer.split_text(markdown_text)
    md_chunks = size_chunkenizer.split_documents(md_chunks)
    return [chunk.dict()["page_content"] for chunk in md_chunks]

def chunkenize_by_method(method, text):
    match method:
        case 'nocontext':
            return size_chunkenizer.split_text(text)
        case 'html':
            return chunkenize_html(text)
        case 'markdown':
            return chunkenize_markdown(text)
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

def index_into_opensearch(opensearch_index, chunks):
    opensearch_client.indices.delete(index=opensearch_index, ignore_unavailable=True)
    opensearch_client.indices.create(index=opensearch_index, body=create_index_body)
    for loop_index, chunk in enumerate(chunks):
        logger.info("Indexing '%s:' document %d/%d", opensearch_index, loop_index, len(chunks))
        opensearch_client.index(index=opensearch_index, body=chunk)

def get_chunks_from_page(pageid, method):
    response = confluence.get_page_by_id(pageid,expand="body.export_view")
    html_body = parse_html_body(response['body']['export_view']['value'])
    chunks = chunkenize_by_method(method, html_body)
    logger.info('Number of chunks created for page id %s: %s', pageid, len(chunks))
    return map_chunks_to_json(response, chunks)

def get_chunks_from_list_of_pages(list_of_pageid, method):
    chunks = []
    for pageid in list_of_pageid:
        chunks.extend(get_chunks_from_page(pageid, method))
    return chunks

def get_children_pageid_recursively(pageid):
    children = []
    for child in confluence.get_page_child_by_type(pageid):
        children.append(child['id'])
        grandchildren = get_children_pageid_recursively(child['id'])
        children.extend(grandchildren)
    return children

@click.command()
@click.option('--pageid', required=True, help='The id of the wiki page to process.')
@click.option('--recursive', is_flag=True, default=False, help='Process all children (recursively) of the provided wiki page.')
@click.option('--method', default='none', help='The method applied by the chunkenizer. Possible values: none|nocontext|html|markdown.')
@click.option('--opensearch_index', help='The OpenSearch index whereto ingest the chunk data.')
def run(pageid, recursive, method, opensearch_index):
    list_of_pageid = [pageid]
    if recursive:
        list_of_pageid.extend(get_children_pageid_recursively(pageid))
    chunks = get_chunks_from_list_of_pages(list_of_pageid, method)

    if (opensearch_index):
        index_into_opensearch(opensearch_index, chunks)
    
    [logger.info(chunk) for chunk in chunks]
