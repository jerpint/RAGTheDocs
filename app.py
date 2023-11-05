import os
from typing import Optional, Tuple

import gradio as gr
import pandas as pd
from buster.completers import Completion

# from embed_docs import embed_rtd_website
# from rtd_scraper.scrape_rtd import scrape_rtd
from embed_docs import embed_documents
import cfg
from cfg import setup_buster

# Typehint for chatbot history
ChatHistory = list[list[Optional[str], Optional[str]]]


# Because this is a one-click deploy app, we will be relying on env. variables being set
openai_api_key = os.getenv("OPENAI_API_KEY")  # Mandatory for app to work
readthedocs_url = os.getenv("READTHEDOCS_URL")  # Mandatory for app to work as intended
readthedocs_version = os.getenv("READTHEDOCS_VERSION")

if openai_api_key is None:
    print(
        "Warning: No OPENAI_API_KEY detected. Set it with 'export OPENAI_API_KEY=sk-...'."
    )

if readthedocs_url is None:
    raise ValueError(
        "No READTHEDOCS_URL detected. Set it with e.g. 'export READTHEDOCS_URL=https://orion.readthedocs.io/'"
    )

if readthedocs_version is None:
    print(
        """
    Warning: No READTHEDOCS_VERSION detected. If multiple versions of the docs exist, they will all be scraped.
    Set it with e.g. 'export READTHEDOCS_VERSION=en/stable'
    """
    )


# Override to put it anywhere
save_directory = "outputs/"

# scrape and embed content from readthedocs website
# You only need to embed the first time the app runs, comment it out to skip
embed_documents(
    homepage_url=readthedocs_url,
    save_directory=save_directory,
    target_version=readthedocs_version,
)

# Setup RAG agent
buster = setup_buster(cfg.buster_cfg)


# Setup Gradio app
def add_user_question(
    user_question: str, chat_history: Optional[ChatHistory] = None
) -> ChatHistory:
    """Adds a user's question to the chat history.

    If no history is provided, the first element of the history will be the user conversation.
    """
    if chat_history is None:
        chat_history = []
    chat_history.append([user_question, None])
    return chat_history


def format_sources(matched_documents: pd.DataFrame) -> str:
    if len(matched_documents) == 0:
        return ""

    matched_documents.similarity_to_answer = (
        matched_documents.similarity_to_answer * 100
    )

    # drop duplicate pages (by title), keep highest ranking ones
    matched_documents = matched_documents.sort_values(
        "similarity_to_answer", ascending=False
    ).drop_duplicates("title", keep="first")

    documents_answer_template: str = "📝 Here are the sources I used to answer your question:\n\n{documents}\n\n{footnote}"
    document_template: str = "[🔗 {document.title}]({document.url}), relevance: {document.similarity_to_answer:2.1f} %"

    documents = "\n".join(
        [
            document_template.format(document=document)
            for _, document in matched_documents.iterrows()
        ]
    )
    footnote: str = "I'm a bot 🤖 and not always perfect."

    return documents_answer_template.format(documents=documents, footnote=footnote)


def add_sources(history, completion):
    if completion.answer_relevant:
        formatted_sources = format_sources(completion.matched_documents)
        history.append([None, formatted_sources])

    return history


def chat(chat_history: ChatHistory) -> Tuple[ChatHistory, Completion]:
    """Answer a user's question using retrieval augmented generation."""

    # We assume that the question is the user's last interaction
    user_input = chat_history[-1][0]

    # Do retrieval + augmented generation with buster
    completion = buster.process_input(user_input)

    # Stream tokens one at a time to the user
    chat_history[-1][1] = ""
    for token in completion.answer_generator:
        chat_history[-1][1] += token

        yield chat_history, completion


demo = gr.Blocks()
with demo:
    with gr.Row():
        gr.Markdown("<h1><center>RAGTheDocs</center></h1>")

    gr.Markdown(
        """
        ## About
        [RAGTheDocs](https://github.com/jerpint/RAGTheDocs) allows you to ask questions about any documentation hosted on readthedocs.
        Simply clone this space and set the environment variables:

        * `OPENAI_API_KEY` (required): Needed for the app to work, e.g. `sk-...`
        * `READTHEDOCS_URL` (required): The url of the website you are interested in scraping (must be built with
        sphinx/readthedocs)
        * `READTHEDOCS_VERSION` (optional): This is important **only** if there exist multiple versions of the docs (e.g. "en/v0.2.7" or "en/latest"). If left empty, it will scrape all available versions (there can be many for open-source projects!).

        Try it out by asking a question below 👇 about [orion](https://orion.readthedocs.io/), an open-source hyperparameter optimization library.

        ## How it works
        This app uses [Buster 🤖](https://github.com/jerpint/buster) and ChatGPT to search the docs for relevant info and
        answer questions.
        View the code on the [project homepage](https://github.com/jerpint/RAGTheDocs)
        """
    )

    chatbot = gr.Chatbot()

    with gr.Row():
        question = gr.Textbox(
            label="What's your question?",
            placeholder="Type your question here...",
            lines=1,
        )
        submit = gr.Button(value="Send", variant="secondary")

    examples = gr.Examples(
        examples=[
            "How can I install the library?",
            "What dependencies are required?",
            "Give a brief overview of the library.",
        ],
        inputs=question,
    )

    response = gr.State()

    # fmt: off
    gr.on(
        triggers=[submit.click, question.submit],
        fn=add_user_question,
        inputs=[question],
        outputs=[chatbot]
    ).then(
        chat,
        inputs=[chatbot],
        outputs=[chatbot, response]
    ).then(
        add_sources,
        inputs=[chatbot, response],
        outputs=[chatbot]
    )


demo.queue(concurrency_count=8)
demo.launch(share=False)
