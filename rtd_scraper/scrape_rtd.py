import logging
import os

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from rtd_scraper.tutorial.spiders.docs_spider import DocsSpider, sanitize_url

# When using scrapy it seems to set logging for all apps at DEBUG, so simply shut it off here...
for name in logging.root.manager.loggerDict:
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)


def run_spider(homepage_url, save_directory, target_version=None):
    process = CrawlerProcess(settings=get_project_settings())
    process.crawl(
        DocsSpider,
        homepage_url=homepage_url,
        save_dir=save_directory,
        target_version=target_version,
    )

    # Start the crawling process
    process.start()

    # To stop the crawling process gracefully
    process.stop()
