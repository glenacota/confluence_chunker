import os
import logging
import sys
import click

from atlassian import Confluence
from decouple import config
from bs4 import BeautifulSoup
from langchain.text_splitter import RecursiveCharacterTextSplitter

# initialise logger
log_level = os.environ.get("LOG_LEVEL", "INFO")
logger = logging.getLogger(__name__)
logger.setLevel(log_level)
# init confluence lib
confluence = Confluence(url=config('CONFLUENCE_URL'), token=config('CONFLUENCE_TOKEN'), timeout=300)

def parse_html_body(html_body_to_parse):
    soup = BeautifulSoup(html_body_to_parse, 'html.parser')
    for tag in soup.find_all(True):
        tag.attrs = {}
        for span in tag.find_all("span"):
            span.unwrap()
    encoded_body = soup.encode(formatter="html5")
    return str(encoded_body)

def chunkenize_none(text):
    return [text]

def chunkenize_nocontext(text):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=20)
    return text_splitter.split_text(text)

def chunkenize_by_method(method, text):
    match method:
        case 'none':
            return chunkenize_none(text)
        case 'nocontext':
            return chunkenize_nocontext(text)
        case _:
            return chunkenize_none(text)

def print_chunks(chunks):
    for chunk in chunks:
        print(chunk + '\n')

@click.command()
@click.option('--pageid', prompt='Page id', default='137729483', help='The id of the wiki page to process.')
@click.option('--method', prompt='Chunking method (none|nocontext)', default='none', help='The method applied by the chunkenizer.')  
def run(pageid, method):
    response = confluence.get_page_by_id(pageid,expand="body.export_view")
    html_body = parse_html_body(response['body']['export_view']['value'])

    chunks = chunkenize_by_method(method, html_body)
    logger.info('Number of chunks created for page id %s: %s', pageid, len(chunks))
    print(response['title'])
    print_chunks(chunks)
