import os
import logging
import click

from config import confluence, size_chunkenizer, html_chunkenizer
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

def print_chunks(chunks):
    for chunk in chunks:
        print(chunk + '\n')

@click.command()
@click.option('--pageid', prompt='Page id', default='137729483', help='The id of the wiki page to process.')
@click.option('--method', prompt='Chunking method (none|nocontext|html)', default='none', help='The method applied by the chunkenizer.')  
def run(pageid, method):
    response = confluence.get_page_by_id(pageid,expand="body.export_view")
    html_body = parse_html_body(response['body']['export_view']['value'])

    chunks = chunkenize_by_method(method, html_body)
    logger.info('Number of chunks created for page id %s: %s', pageid, len(chunks))
    print(response['title'])
    print_chunks(chunks)
