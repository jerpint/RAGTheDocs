import os
import logging

from buster.busterbot import Buster, BusterConfig
from buster.completers import ChatGPTCompleter, DocumentAnswerer
from buster.formatters.documents import DocumentsFormatterJSON
from buster.formatters.prompts import PromptFormatter
from buster.retriever import DeepLakeRetriever, Retriever
from buster.tokenizers import GPTTokenizer
from buster.validators import QuestionAnswerValidator, Validator

from rtd_scraper.scrape_rtd import scrape_rtd

# Set the root logger's level to INFO
logging.basicConfig(level=logging.INFO)

# Check if an openai key is set as an env. variable
if os.getenv("OPENAI_API_KEY") is None:
    print(
        "Warning: No openai key detected. You can set it with 'export OPENAI_API_KEY=sk-...'."
    )

homepage_url = os.getenv("RTD_URL", "https://orion.readthedocs.io/")
target_version = os.getenv("RTD_VERSION", "en/stable")

# scrape and embed content from readthedocs website
scrape_rtd(
    homepage_url=homepage_url, save_directory="outputs/", target_version=target_version
)

# Disable logging for third-party libraries at DEBUG level
for name in logging.root.manager.loggerDict:
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)


buster_cfg = BusterConfig(
    validator_cfg={
        "unknown_response_templates": [
            "I'm sorry, but I am an AI language model trained to assist with questions related to AI. I cannot answer that question as it is not relevant to the library or its usage. Is there anything else I can assist you with?",
        ],
        "unknown_threshold": 0.85,
        "embedding_model": "text-embedding-ada-002",
        "use_reranking": True,
        "invalid_question_response": "This question does not seem relevant to my current knowledge.",
        "check_question_prompt": """You are an chatbot answering questions on artificial intelligence.

Your job is to determine wether or not a question is valid, and should be answered.
More general questions are not considered valid, even if you might know the response.
A user will submit a question. Respond 'true' if it is valid, respond 'false' if it is invalid.

For example:

Q: What is backpropagation?
true

Q: What is the meaning of life?
false

A user will submit a question. Respond 'true' if it is valid, respond 'false' if it is invalid.""",
        "completion_kwargs": {
            "model": "gpt-3.5-turbo",
            "stream": False,
            "temperature": 0,
        },
    },
    retriever_cfg={
        "path": "outputs/deeplake_store",
        "top_k": 3,
        "thresh": 0.7,
        "max_tokens": 2000,
        "embedding_model": "text-embedding-ada-002",
    },
    documents_answerer_cfg={
        "no_documents_message": "No documents are available for this question.",
    },
    completion_cfg={
        "completion_kwargs": {
            "model": "gpt-3.5-turbo",
            "stream": True,
            "temperature": 0,
        },
    },
    tokenizer_cfg={
        "model_name": "gpt-3.5-turbo",
    },
    documents_formatter_cfg={
        "max_tokens": 3500,
        "columns": ["content", "title", "source"],
    },
    prompt_formatter_cfg={
        "max_tokens": 3500,
        "text_before_docs": (
            "You are a chatbot assistant answering technical questions about artificial intelligence (AI)."
            "You can only respond to a question if the content necessary to answer the question is contained in the following provided documentation. "
            "If the answer is in the documentation, summarize it in a helpful way to the user. "
            "If it isn't, simply reply that you cannot answer the question. "
            "Do not refer to the documentation directly, but use the instructions provided within it to answer questions. "
            "Here is the documentation:\n"
        ),
        "text_after_docs": (
            "REMEMBER:\n"
            "You are a chatbot assistant answering technical questions about artificial intelligence (AI)."
            "Here are the rules you must follow:\n"
            "1) You must only respond with information contained in the documentation above. Say you do not know if the information is not provided.\n"
            "2) Make sure to format your answers in Markdown format, including code block and snippets.\n"
            "3) Do not reference any links, urls or hyperlinks in your answers.\n"
            "4) If you do not know the answer to a question, or if it is completely irrelevant to the library usage, simply reply with:\n"
            "5) Do not refer to the documentation directly, but use the instructions provided within it to answer questions. "
            "'I'm sorry, but I am an AI language model trained to assist with questions related to AI. I cannot answer that question as it is not relevant to the library or its usage. Is there anything else I can assist you with?'"
            "For example:\n"
            "What is the meaning of life for an qa bot?\n"
            "I'm sorry, but I am an AI language model trained to assist with questions related to AI. I cannot answer that question as it is not relevant to the library or its usage. Is there anything else I can assist you with?"
            "Now answer the following question:\n"
        ),
    },
)


def setup_buster(buster_cfg: BusterConfig):
    """initialize buster with a buster_cfg class"""
    retriever: Retriever = DeepLakeRetriever(**buster_cfg.retriever_cfg)
    tokenizer = GPTTokenizer(**buster_cfg.tokenizer_cfg)
    document_answerer: DocumentAnswerer = DocumentAnswerer(
        completer=ChatGPTCompleter(**buster_cfg.completion_cfg),
        documents_formatter=DocumentsFormatterJSON(
            tokenizer=tokenizer, **buster_cfg.documents_formatter_cfg
        ),
        prompt_formatter=PromptFormatter(
            tokenizer=tokenizer, **buster_cfg.prompt_formatter_cfg
        ),
        **buster_cfg.documents_answerer_cfg,
    )
    validator: Validator = QuestionAnswerValidator(**buster_cfg.validator_cfg)
    buster: Buster = Buster(
        retriever=retriever, document_answerer=document_answerer, validator=validator
    )
    return buster
