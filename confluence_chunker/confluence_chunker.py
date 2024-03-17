import os, sys
import logging
import click
import json
import markdownify

from config import confluence
from config import size_chunkenizer, html_chunkenizer, md_chunkenizer
from config import OSClient
from lxml import etree

# init logger
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

def chunkenize_fixed(text):
    text = ' '.join(etree.fromstring(text, parser=etree.HTMLParser()).itertext())
    return size_chunkenizer.split_text(text)

def chunkenize_html(text):
    document_chunks = html_chunkenizer.split_text(text)
    document_chunks = size_chunkenizer.split_documents(document_chunks)
    return [doc.dict()["page_content"] for doc in document_chunks]

def chunkenize_markdown(text):
    markdown_text = markdownify.markdownify(text)
    md_chunks = md_chunkenizer.split_text(markdown_text)
    md_chunks = size_chunkenizer.split_documents(md_chunks)
    return [chunk.dict()["page_content"] for chunk in md_chunks]

def chunkenize_by_method(method, text):
    match method:
        case 'fixed':
            return chunkenize_fixed(text)
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
        "chunk": chunk,
        "createdDate": confluence_rest_response['history']['createdDate'],
        "updatedDate": confluence_rest_response['history']['lastUpdated']['when']
    })

def get_chunks_from_page(pageid, method):
    response = confluence.get_page_by_id(pageid,expand="body.export_view,history.lastUpdated")
    html_body = parse_html_body(response['body']['export_view']['value'])
    
    chunks = chunkenize_by_method(method, html_body) if html_body else []
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
@click.option('--pageid', required=True, help='The id of the page to process along with all its descendants.')
@click.option('--ignore_descendants', is_flag=True, default=False, help='When set, process only the provided page ignoring its descendants.')
@click.option('--method', type=click.Choice(['none', 'fixed', 'html', 'markdown'], case_sensitive=False), 
              default='none', help='The chunking method to use. Default: none.')
@click.option('--index', help='The prefix of the OpenSearch index. Complete name: "<index_value>-<method_value>"')
@click.option('--verbose', '-v', is_flag=True, default=False, help='When set, print chunks also to stdout.')
def run(pageid, ignore_descendants, method, index, verbose):
    list_of_pageid = [pageid]
    if not ignore_descendants:
        list_of_pageid.extend(get_children_pageid_recursively(pageid))
    chunks = get_chunks_from_list_of_pages(list_of_pageid, method)

    osclient = OSClient("-".join([index, method]))
    for loop_index, chunk in enumerate(chunks):
        logger.info("Indexing' document %d/%d", (loop_index+1), len(chunks))
        osclient.index(chunk)

    if (verbose):
        [print(chunk) for chunk in chunks]
