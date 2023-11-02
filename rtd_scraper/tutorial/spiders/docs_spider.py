import logging
from pathlib import Path
from urllib.parse import urlparse

import scrapy

logging.basicConfig(format="%(levelname)s: %(message)s", level=logging.ERROR)

from urllib.parse import urlparse


def extract_domain(url):
    """
    Extract the domain (including subdomains) from a given URL.

    Args:
    - url (str): The URL from which the domain needs to be extracted.

    Returns:
    - str: The domain (with subdomains) extracted from the URL.
           For example, 'www.example.com' for the URL 'https://www.example.com/path/to/something'.

    """
    parsed_uri = urlparse(url)
    # The netloc attribute will contain the domain name
    domain = parsed_uri.netloc
    return domain


class DocsSpider(scrapy.Spider):
    name = "docs"

    def __init__(
        self,
        homepage_url: str,
        save_dir="crawled_pages",
        target_version=None,
        *args,
        **kwargs,
    ):
        super(DocsSpider, self).__init__(*args, **kwargs)

        if not homepage_url.startswith("https://"):
            homepage_url = "https://" + homepage_url

        self.allowed_domains = [extract_domain(homepage_url)]
        self.start_urls = [homepage_url]
        self.base_dir = Path(save_dir)
        self.target_version = target_version

    def parse(self, response):
        parsed_uri = urlparse(response.url)
        # Create a Path from the parsed URL. If it ends with '/', we add 'index.html' as the filename.
        if parsed_uri.path.endswith("/"):
            filepath = (
                self.base_dir
                / parsed_uri.netloc
                / parsed_uri.path.strip("/")
                / "index.html"
            )
        else:
            filepath = self.base_dir / parsed_uri.netloc / parsed_uri.path.strip("/")
        filepath.parent.mkdir(parents=True, exist_ok=True)

        print(f"{filepath=}")
        with open(filepath, "wb") as f:
            f.write(response.body)

        # Follow links to other documentation pages only if they contain the target version in the full URL
        for href in response.css("a::attr(href)").getall():
            if self.target_version:
                # A version was specified, check to see if it's the correct version from url
                full_url = response.urljoin(href)  # Expand href to a full URL
                if self.target_version in full_url:
                    yield response.follow(href, self.parse)
            else:
                # no version specified, follow all links
                yield response.follow(href, self.parse)
