# WebScrappy

**Version:** 0.1.0

## Project Description

WebScrappy is a Python-based web scraping tool designed to extract content from a list of specified URLs. It utilizes the Scrapy framework for efficient web crawling and html2text for converting HTML content into clean Markdown format. The scraped content is then saved into individual Markdown files in the `scraped_content/` directory, making it easy to access and process textual data from websites.

## Features

*   **Web Crawling:** Leverages Scrapy to fetch web pages.
*   **HTML to Markdown Conversion:** Uses html2text to convert the main content of fetched pages into Markdown.
*   **Configurable URL Input:** Reads a list of target URLs from the `portal.txt` file.
*   **Organized Output:** Saves each scraped page as a separate `.md` file in the `scraped_content/` directory, using a sanitized version of the URL path as the filename.
*   **Dependency Management:** Project dependencies are managed using `pyproject.toml`.

## Setup and Installation

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/akyrgiazos/webscrappy.git
    cd webscrappy
    ```

2.  **Python Version:**
    Ensure you have Python 3.12 or higher installed. You can check your Python version using:
    ```bash
    python --version
    ```

3.  **Create a Virtual Environment (Recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

4.  **Install Dependencies:**
    The project uses `pyproject.toml` to manage dependencies. Install them using pip:
    ```bash
    pip install .
    ```
    This will install `scrapy` and `html2text` as specified in the `pyproject.toml` file.

## Usage

1.  **Prepare Input URLs:**
    Edit the [`portal.txt`](portal.txt:0) file in the root directory. Add each URL you want to scrape on a new line. For example:
    ```
    https://example.com/page1
    https://anotherexample.org/articleA
    ```

2.  **Run the Scraper:**
    Execute the main script from the root directory of the project:
    ```bash
    python main.py
    ```

3.  **Access Scraped Content:**
    The scraped content will be saved as Markdown files in the `scraped_content/` directory. Each file will be named based on the URL it was scraped from (e.g., `scraped_content/example_com_page1.md`).

## Command-Line Arguments

The script accepts several command-line arguments to customize its behavior:

*   `urls_file`: (Required) Path to the text file containing URLs to scrape (one URL per line).
*   `--output-dir <dir>` or `-o <dir>`: Specifies the directory where scraped markdown files will be saved.
    *   Default: `scraped_content`
*   `--delay <seconds>` or `-d <seconds>`: Sets the delay in seconds between requests to the same website.
    *   Default: `1.0`
*   `--concurrent <num>` or `-c <num>`: Defines the number of concurrent requests Scrapy will perform.
    *   Default: `5`
*   `--timeout <seconds>` or `-t <seconds>`: Sets the timeout in seconds for web requests.
    *   Default: `30`
*   `--user-agent <string>` or `-ua <string>`: Allows specifying a custom User-Agent string for requests.
    *   Default: `Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36` (defined in the spider)
*   `--ignore-robots-txt`: If present, the scraper will ignore `robots.txt` rules.
    *   Default: `False` (obeys `robots.txt`)
*   `--log-level <level>` or `-l <level>`: Sets the logging level for Scrapy.
    *   Choices: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`
    *   Default: `INFO`

**Example with arguments:**

```bash
python main.py portal.txt -o my_scrapes -d 2 -c 3 --log-level DEBUG
```

## Project Structure
```
webscrappy/
├── .gitignore
├── main.py             # Main script to run the scraper
├── portal.txt          # List of URLs to scrape
├── pyproject.toml      # Project metadata and dependencies
├── README.md           # This file
├── scraped_content/    # Directory where scraped markdown files are stored
└── ...                 # Other project files (e.g., .python-version, uv.lock)
```

## Contributing
(Details on how to contribute can be added here if the project is open to contributions.)

## License
(License information can be added here.)