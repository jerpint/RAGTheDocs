import logging
from pathlib import Path
from urllib.parse import urlparse

import scrapy

logging.basicConfig(format="%(levelname)s: %(message)s", level=logging.ERROR)


class DocsSpider(scrapy.Spider):
    name = "docs"

    def __init__(self, homepage_url: str, save_dir="crawled_pages", *args, **kwargs):
        super(DocsSpider, self).__init__(*args, **kwargs)

        if not homepage_url.startswith("https://"):
            homepage_url = "https://" + homepage_url

        project: str = homepage_url.split(".")[0].split("https://")[1]
        self.allowed_domains = [f"{project}.readthedocs.io"]
        self.start_urls = [homepage_url]
        self.base_dir = Path(save_dir)

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

        # Follow links to other documentation pages
        for href in response.css("a::attr(href)").getall():
            yield response.follow(href, self.parse)
