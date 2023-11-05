import logging
import os

from buster.docparser import get_all_documents
from buster.documents_manager import DeepLakeDocumentsManager
from buster.parser import SphinxParser
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from rtd_scraper.tutorial.spiders.docs_spider import DocsSpider, sanitize_url

# from tutorial.spiders.docs_spider import DocsSpider

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


def scrape_rtd(homepage_url, save_directory, target_version=None):

    # adds https:// and trailing backslash
    homepage_url = sanitize_url(homepage_url)

    # Crawl the website using scrapy
    run_spider(
        homepage_url, save_directory=save_directory, target_version=target_version
    )

    # # Convert the .html pages into chunks using Buster's SphinxParser
    root_dir = os.path.join(save_directory, homepage_url.split("https://")[1])

    # root_dir is the folder containing the scraped content e.g. crawled_outputs/buster.readthedocs.io/
    df = get_all_documents(
        root_dir=root_dir,
        base_url=homepage_url,
        parser_cls=SphinxParser,
        min_section_length=100,
        max_section_length=1000,
    )

    # Add the source column
    df["source"] = "readthedocs"

    #  Initialize the DeepLake vector store
    dm = DeepLakeDocumentsManager(
        vector_store_path=os.path.join(save_directory, "deeplake_store"),
        overwrite=True,
        required_columns=["url", "content", "source", "title"],
    )

    # Add all embeddings to the vector store
    dm.batch_add(
        df=df,
        batch_size=3000,
        min_time_interval=60,
        num_workers=32,
    )


if __name__ == "__main__":
    homepage_url = "https://orion.readthedocs.io/"
    scrape_rtd(
        homepage_url=homepage_url, target_version="v0.2.7", save_directory="outputs/"
    )
