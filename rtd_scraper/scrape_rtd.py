import logging
import os

from buster.docparser import get_all_documents
from buster.documents_manager import DeepLakeDocumentsManager
from buster.parser import SphinxParser
from scrapy.crawler import CrawlerProcess
from scrapy.exceptions import CloseSpider
from scrapy.utils.project import get_project_settings

from rtd_scraper.tutorial.spiders.docs_spider import DocsSpider

# When using scrapy it seems to set logging for all apps at DEBUG, so simply shut it off here...
for name in logging.root.manager.loggerDict:
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)


def run_spider(homepage_url, save_directory):
    #  settings_file_path = 'rtd_scraper.tutorial.settings' # The path seen from top-level, ie. from cfg.py
    #  os.environ.setdefault('SCRAPY_SETTINGS_MODULE', settings_file_path)

    process = CrawlerProcess(settings=get_project_settings())
    process.crawl(DocsSpider, homepage_url=homepage_url, save_dir=save_directory)

    # Start the crawling process
    process.start()

    # To stop the crawling process gracefully
    process.stop()


def scrape_rtd(homepage_url, save_directory):
    # Crawl the website using scrapy
    run_spider(homepage_url, save_directory=save_directory)

    # Convert the .html pages into chunks using Buster's SphinxParser
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

    #  #  Initialize the DeepLake vector store
    #  dm = DeepLakeDocumentsManager(
    #      vector_store_path=os.path.join(save_directory, "deeplake_store"),
    #      overwrite=True,
    #      required_columns=["url", "content", "source", "title"],
    #  )
    #
    #  # Add all embeddings to the vector store
    #  dm.batch_add(
    #      df=df,
    #      batch_size=3000,
    #      min_time_interval=60,
    #      num_workers=32,
    #  )
    #


if __name__ == "__main__":
    homepage_url = "https://buster.readthedocs.io/"
    scrape_rtd(homepage_url=homepage_url, save_directory="outputs/")
