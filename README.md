# Confluence Chunker
A python tool to create chunks of text out of a Confluence page.

* Free software: Apache-2.0

## Features
- Fetch wiki pages by id from a Confluence server using the [Atlassian REST API](https://developer.atlassian.com/cloud/confluence/rest/v1/intro/#about).
- Split the content of wiki pages into chunks using the open-source tool [LangChain](https://www.langchain.com/).

### Planned features
- Setup ingest and RAG pipelines in OpenSearch from the tool.

## Requirements
### Access token to Confluence
The tool assumes that authenticated to the Confluence server takes place via OAuth 2.0 access tokens. Users of this tool should therefore possess such a token (see https://developer.atlassian.com/cloud/confluence/security-overview/).

### Environment variables
The tool fetches a few mandatory configurations from the following environment variables:
- `CONFLUENCE_URL` - the base url of the Confluence server
- `CONFLUENCE_TOKEN` - the access token to make authenticated REST calls to the Confluence server.
- `OPENSEARCH_HOST` - the host of the OpenSearch server whereto index the chunks
- `OPENSEARCH_PORT` - the port of the OpenSearch server whereto index the chunks

Make sure that such environment variables are set before running the tool.

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
  --pageid TEXT  The id of the wiki page to process.
  --method TEXT  The method applied by the chunkenizer.
  --help         Show this message and exit.
```

To run the chunkenizer:
```
$ python3 confluence_chunker
```
