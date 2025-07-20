# Wikipedia Crawler

A web crawler that extracts content from Wikipedia articles and stores them as text files. The crawler automatically follows links to discover and crawl additional pages while avoiding duplicates.

## Features

- Crawls Wikipedia articles and extracts structured content
- Follows links automatically to discover new pages
- Avoids duplicate crawling with URL tracking
- Progress visualization with tqdm
- Configurable via environment variables
- Docker support for easy deployment
- Numbered file output with UTF-8 encoding

## Usage

### Local Development

```bash
# Install dependencies
uv sync

# Run with default settings (50 files max)
python main.py

# Run with custom environment variables
MAX_FILES=100 START_URLS="https://en.wikipedia.org/wiki/Python" python main.py
```

### Docker

```bash
# Build the image
docker build -t wikipedia-crawler .

# Run with default settings
docker run -v $(pwd)/data:/app/data wikipedia-crawler

# Run with custom start URLs (single URL)
docker run -e START_URLS="https://en.wikipedia.org/wiki/Python" -v $(pwd)/data:/app/data wikipedia-crawler

# Run with multiple start URLs
docker run -e START_URLS="https://en.wikipedia.org/wiki/Python,https://en.wikipedia.org/wiki/Docker,https://en.wikipedia.org/wiki/Linux" -v $(pwd)/data:/app/data wikipedia-crawler

# Run with custom max files and start URLs
docker run -e START_URLS="https://en.wikipedia.org/wiki/Python" -e MAX_FILES=100 -v $(pwd)/data:/app/data wikipedia-crawler
```

## Environment Variables

- `MAX_FILES`: Maximum number of files to crawl (default: 50)
- `START_URLS`: Comma-separated list of starting URLs (default: Turkish Wikipedia page about Erdogan)

## Output

- Crawled content is saved to numbered files in the `/data` directory
- File naming format: `001_Page_Title.txt`, `002_Next_Page.txt`, etc.
- Progress tracking file: `data/visited_urls.json` (stores visited URLs and file count)

## Requirements

- Python 3.11+
- beautifulsoup4
- tqdm
- pytest (for testing)

