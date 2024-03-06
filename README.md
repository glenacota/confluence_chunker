# Confluence Chunker
A python tool to create chunks of text out of a Confluence page.

* Free software: Apache-2.0



## Features
- Fetch wiki pages by id from a Confluence server using the [Atlassian REST API](https://developer.atlassian.com/cloud/confluence/rest/v1/intro/#about).
- Split the content of wiki pages into chunks using the open-source tool [LangChain](https://www.langchain.com/).
- Support indexing of chunks information to [OpenSearch](https://opensearch.org/).

Information about the chunk is formatted as JSON, with the following schema:
```
{
  "chunk": "the chunked text",
  "title": "the title of the source wiki page",
  "url": "the url of the source wiki page" 
}
```

### Planned features
- Support authenticated requests to an OpenSearch cluster with security features enabled.

## Requirements
### Access token to Confluence
The tool assumes that authenticated to the Confluence server takes place via OAuth 2.0 access tokens. Users of this tool should therefore possess such a token (see https://developer.atlassian.com/cloud/confluence/security-overview/).

### Environment variables
The tool fetches a few mandatory configurations from the following environment variables:
- `CONFLUENCE_URL` - the base url of the Confluence server
- `CONFLUENCE_TOKEN` - the access token to make authenticated REST calls to the Confluence server.

Make sure that such environment variables are set before running the tool.

### OpenSearch configuration
If you plan to index the chunks into OpenSearch, here are the requirements:
- Disable the cluster security features - notably, no authentication or fine-grained access control.
- Set the environment variables `OPENSEARCH_HOST` and `OPENSEARCH_PORT` with the actual values.

## Usage
We use Python 3.12 for this application, so it must be installed in your system. For MacOS users, `brew install python@3.12` should suffice.

To manage the local environments, we recommend using `virtualenv` (installation details [here](https://virtualenv.pypa.io/en/latest/installation.html)).

```
$ cd /path/to/confluence_chunker
$ virtualenv .env
$ source .venv/bin/activate
```

For dependency management, we used `Poetry` (installation details [here](https://python-poetry.org/docs/#installation)). To install the dependencies:
```
$ poetry install
```

The tool expects some parameters, to see which ones:
```
$ python3 confluence_chunker --help
Usage: confluence_chunker [OPTIONS]

Options:
  --pageid TEXT            The id of the wiki page to process.  [required]
  --recursive              Process all children (recursively) of the provided
                           wiki page.
  --method TEXT            The method applied by the chunkenizer. Possible
                           values: none|nocontext|html|markdown.
  --opensearch_index TEXT  The OpenSearch index whereto ingest the chunk data.
  --help                   Show this message and exit.
```

To run the chunkenizer, e.g.:
```
$ python3 confluence_chunker --pageid 226200355 --recursive --opensearch_index destination-index --method markdown≈
```
