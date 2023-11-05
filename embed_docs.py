import logging
import os

from buster.docparser import get_all_documents
from buster.documents_manager import DeepLakeDocumentsManager
from buster.parser import SphinxParser

from rtd_scraper.scrape_rtd import sanitize_url, run_spider

# When using scrapy it seems to set logging for all apps at DEBUG, so simply shut it off here...
for name in logging.root.manager.loggerDict:
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)


def embed_documents(homepage_url, save_directory, target_version=None):
    # adds https:// and trailing slash
    homepage_url = sanitize_url(homepage_url)

    # Crawl the website using scrapy
    run_spider(
        homepage_url, save_directory=save_directory, target_version=target_version
    )

    # # Convert the .html pages into chunks using Buster's SphinxParser
    # root_dir is the folder containing the scraped content e.g. crawled_outputs/buster.readthedocs.io/
    root_dir = os.path.join(save_directory, homepage_url.split("https://")[1])
    df = get_all_documents(
        root_dir=root_dir,
        base_url=homepage_url,
        parser_cls=SphinxParser,
        min_section_length=100,
        max_section_length=1000,
    )
    df["source"] = "readthedocs"  # Add the source column

    #  Initialize the DeepLake vector store
    vector_store_path = os.path.join(save_directory, "deeplake_store")
    dm = DeepLakeDocumentsManager(
        vector_store_path=vector_store_path,
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
    target_version = "v0.2.7"
    save_directory = "outputs/"
    embed_documents(
        homepage_url=homepage_url,
        target_version=target_version,
        save_directory=save_directory,
    )
