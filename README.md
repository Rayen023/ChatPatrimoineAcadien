# PatrimoineImages

## Overview

ChatPatrimoine is an LLM-powered conversational agent designed to provide information about historical Acadian archival images. The application helps users interact with Acadian visual history by generating descriptive metadata and contextual information for archive photographs.

Live demo: [https://chatpatrimoineacadien.ca/](https://chatpatrimoineacadien.ca/)

## Features

- Conversational interface for exploring Acadian historical images
- LLM-generated descriptions of archival photographs using Gemini 2.5 Flash
- Historical context retrieval for images in the collection
- Example queries in sidebar to guide user interaction

## Technical Implementation

- **LangGraph**: Orchestration framework for agent workflows
- **Streamlit**: Web interface and UI components
- **Pinecone**: Vector database for embeddings and metadata storage 
- **OpenRouter API**: Gateway for accessing various language models
- **Voyage AI**: Embeddings and Reranker for semantic similarity context retrieval
- **Cloudflare R2**: Cloud storage for archival images