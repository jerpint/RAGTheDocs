---
title: RAGTheDocs
emoji: 👀
colorFrom: gray
colorTo: yellow
sdk: gradio
sdk_version: 3.50.2
app_file: app.py
pinned: false
license: mit
---

# RAGtheDocs

## Introduction 📚

RAGTheDocs is an open-source library that allows you to **one-click deploy** retrieval augmented generation (RAG) on any readthedocs documentation on [huggingface 🤗 spaces](https://huggingface.co/spaces/jerpint/RAGTheDocs)!

## Usage 👉

1) Go to the [example space](https://huggingface.co/spaces/jerpint/RAGTheDocs)
2) Duplicate the space:

![image](https://github.com/jerpint/buster/assets/18450628/0c89038c-c3af-4c1f-9d3b-9b4d83db4910)

3) Set your environment variables:
* `OPENAI_API_KEY` (required): Needed for the app to work, e.g. `sk-...`
* `READTHEDOCS_URL` (required): The url of the website you are interested in scraping (must be built with
sphinx/readthedocs). e.g. `https://orion.readthedocs.io`
* `READTHEDOCS_VERSION` (optional): This is important if there exist multiple versions of the docs (e.g. `en/v0.2.7` or `en/latest`). If left empty, it will scrape all available versions (there can be many for open-source projects!).

## Features 🚀

- **Web Scraping and embeddings:** RAGtheDocs automatically scrapes and embeds documentation from any website generated by ReadTheDocs/Sphinx using OpenAI embeddings

- **RAG Interface:** It comes built-in with a gradio UI for users to interact with [Buster 🤖](https://github.com/jerpint/buste) our RAG agent.

- **Customization Options:** Tailor RAGtheDocs prompts and settings with customizable settings and options.

## Disclaimers ❗

* This is a quickly hacked together side-project. This code should be considered experimental at best.

* This library will automatically call OpenAI APIs for you (for embeddings and chatGPT).

* Use at your own risk! ⚠️

