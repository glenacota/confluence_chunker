import os
import logging
import sys

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

def chunkenize_no_context(text):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
    return text_splitter.split_text(text)

# entry point    
def main():
    print("Hi!")
    parent_page_id = sys.argv[1]
    response = confluence.get_page_by_id(parent_page_id,expand="body.export_view")
    html_body = parse_html_body(response['body']['export_view']['value'])

    print(response['title'])
    chunks = chunkenize_no_context(html_body)
    for chunk in chunks:
        print(chunk + '\n')


main()