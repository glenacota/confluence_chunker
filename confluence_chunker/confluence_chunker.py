"""Main module."""
import os
import logging

from atlassian import Confluence
from decouple import config
from bs4 import BeautifulSoup

# initialise logger
log_level = os.environ.get("LOG_LEVEL", "INFO")
logger = logging.getLogger(__name__)
logger.setLevel(log_level)
# init confluence lib
confluence = Confluence(url="https://wiki.kreuzwerker.de/", token=config('CONFLUENCE_TOKEN'), timeout=300)

response = confluence.get_page_by_id('137729483',expand="body.export_view")
html_body = response['body']['export_view']['value']
soup = BeautifulSoup(html_body, 'html.parser')
for tag in soup.find_all(True):
    tag.attrs = {}
    for span in tag.find_all("span"):
        span.unwrap()

print(response['title'])
print(soup.encode(formatter="html5"))