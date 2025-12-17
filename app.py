import asyncio
import json
import os
import re
import time
import uuid

import streamlit as st
from langchain.retrievers import ContextualCompressionRetriever

# from langchain_cohere import CohereEmbeddings

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_pinecone import PineconeVectorStore
from langchain_voyageai import VoyageAIEmbeddings, VoyageAIRerank

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, MessagesState, StateGraph

from sidebar_answers import show_questions_sidebar

from dotenv import load_dotenv
load_dotenv()

## embeddings = CohereEmbeddings(model="embed-multilingual-v3.0")

#PINECONE_INDEX_NAME = "short-descriptions-cohere"
PINECONE_INDEX_NAME = "short-descriptions"
WELCOME_MESSAGE = "Comment puis-je vous aider ? | How can I help you ?"
MODEL_OPTIONS = {
    "Claude 4.5 Haiku": "anthropic/claude-haiku-4.5",
    "Gemini 2.5 Flash": "google/gemini-2.5-flash-preview-09-2025",
    "Claude 4.5 Sonnet": "anthropic/claude-sonnet-4.5",
    "Gemini 2.5 Pro": "google/gemini-2.5-pro",
    "GPT-5 Mini": "openai/gpt-5-mini",
    "GPT-5": "openai/gpt-5",
}

st.set_page_config(
    page_title="Images Patrimoniales",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="auto",
)

## Initialize embeddings and retrieval system
# embeddings = CohereEmbeddings(model="embed-multilingual-v3.0")
embeddings = VoyageAIEmbeddings(model="voyage-3")
vector_store = PineconeVectorStore(
    index_name=PINECONE_INDEX_NAME,
    embedding=embeddings,
)
base_retriever = vector_store.as_retriever(
    search_type="similarity_score_threshold",
    search_kwargs={"k": 40, "score_threshold": 0.4},
)
compressor = VoyageAIRerank(model="rerank-2", top_k=20)
compression_retriever = ContextualCompressionRetriever(
    base_compressor=compressor, base_retriever=base_retriever
)

if "selected_model" not in st.session_state:
    st.session_state["selected_model"] = "Claude 4.5 Haiku"

if "thread_id" not in st.session_state:
    st.session_state["thread_id"] = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state["messages"] = [AIMessage(content=WELCOME_MESSAGE)]

llm = ChatOpenAI(
    openai_api_key=os.environ["OPENROUTER_API_KEY"],
    openai_api_base=os.environ["OPENROUTER_BASE_URL"],
    # model_name=MODEL_OPTIONS[st.session_state["selected_model"]],
    model_name="google/gemini-3-flash-preview",
    temperature=0,
    max_tokens=8096,
    timeout=None,
    max_retries=2,
    streaming=False,
)


@st.cache_resource
def cache_memory():
    return MemorySaver()


def reset_chat_history():
    st.session_state["messages"] = [AIMessage(content=WELCOME_MESSAGE)]
    st.session_state["thread_id"] = str(uuid.uuid4())


@st.cache_data
def load_metadata():
    """Load metadata from JSON file and return a dictionary mapping cloud_link to item data."""
    json_path = os.path.join(
        os.path.dirname(__file__), "items_with_short_descriptions.json"
    )

    metadata_dict = {}
    if os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as file:
                items_data = json.load(file)
                for item in items_data:
                    if "cloud_link" in item:
                        metadata_dict[item["cloud_link"]] = item
        except Exception as e:
            print(f"Error loading metadata file: {e}")

    return metadata_dict


@st.fragment
def display_message_with_images(container, message_content):
    start = time.time()

    jpg_urls = re.findall(r"(https?://[^)\]]*?\.jpg)", message_content, re.IGNORECASE)

    seen = set()
    unique_urls = [url for url in jpg_urls if not (url in seen or seen.add(url))]

    # Remove image URLs from the message content to display only the text
    cleaned_message = message_content
    for url in unique_urls:
        cleaned_message = cleaned_message.replace(url, "")
    
    # Clean up any extra whitespace or empty lines
    cleaned_message = re.sub(r'\n\s*\n', '\n\n', cleaned_message.strip())

    if cleaned_message:
        container.markdown(cleaned_message)

    if not unique_urls:
        return

    metadata_dict = load_metadata()
    figure_counter = 1

    for url in unique_urls:
        try:
            container.image(url, width=500) 
            if url in metadata_dict:
                item = metadata_dict[url]
                item_id = item.get("ID", "N/A")
                year = item.get("year", "N/A")
                content = item.get("content", "N/A")
                locality = item.get("locality", "N/A")
                description = item.get("description", "N/A")

                container.markdown(
                    f"**Figure {figure_counter}:** [{content} ({year}) - {locality}]({url}) "
                )
                container.markdown(f"{description}")
                figure_counter += 1
        except Exception:
            container.warning(f"Impossible de charger l'image: {url}")

    end = time.time()
    print(f"Image loading time: {end - start:.2f} seconds")


@st.fragment
def display_chat_history():
    for message in st.session_state["messages"]:
        if isinstance(message, AIMessage):
            with st.chat_message("assistant"):
                display_message_with_images(st, message.content)
        elif isinstance(message, HumanMessage):
            st.chat_message("user").write(message.content)


with st.sidebar:
    st.button(
        "Nouveau chat",
        on_click=reset_chat_history,
        icon=":material/edit_square:",
        use_container_width=True,
    )
    
    if os.environ.get("DEBUGGING", None) :
        st.selectbox(
            "Sélectionner un modèle",
            options=list(MODEL_OPTIONS.keys()),
            key="selected_model",
    )
    

    show_questions_sidebar()
    
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: gray; font-size: 0.8em;'>"
        "© R. Ghali et S. A. Selouani 2025, Ce projet a été développé dans le cadre d'un partenariat du CFRIA avec le Centre Anselme Chiasson de la bibliothèque Champlain de l'Université de Moncton et Assomption Vie."
        "</div>",
        unsafe_allow_html=True
    )

display_chat_history()


@tool(response_format="content_and_artifact")
def search_image_archive_tool(query: str):
    """
    Récupère des informations liées à une requête dans l'archive d'images.
    
    Args:
        query (str): La requête de recherche pour trouver des images pertinentes
        
    Returns:
        Tuple: (résultats sérialisés, documents récupérés)
    """
    # Previous filter implementation kept as comment for reference
    # filter_dict = {}
    # if year is not None:
    #     filter_dict["year"] = year
    # if locality is not None:
    #     filter_dict["locality"] = locality
    # if filter_dict:
    #     retrieved_docs = compression_retriever.invoke(query, filter=filter_dict)
    #     print(f"Filter applied: {filter_dict}")
    # else:
    
    retrieved_docs = compression_retriever.invoke(query)
    print("No filter applied")

    # Serialize the results for display
    serialized = "\n\n".join(
        (f"Source: {doc.metadata}\n" f"Content: {doc.page_content}")
        for doc in retrieved_docs
    )

    return serialized, retrieved_docs


tools = [search_image_archive_tool]
tools_by_name = {tool.name: tool for tool in tools}
llm_with_tools = llm.bind_tools(tools)


def llm_call(state: MessagesState):
    """L'agent LLM décide d'appeler un outil ou de répondre directement"""
    
    system_message_content = """ 
Vous êtes un assistant spécialisé dans la recherche d'images historiques. Votre rôle est de trouver et retourner des liens d'images pertinentes depuis l'archive du CEAAC (Centre d'études acadiennes Anselme-Chiasson).

**UTILISATION DE L'OUTIL:**
- Pour chaque demande d'images, utilisez `search_image_archive_tool` avec une requête descriptive
- Si les résultats ne correspondent pas, réessayez avec une formulation différente (plus/moins de détails, mots-clés alternatifs)
- Vous pouvez appeler l'outil plusieurs fois pour affiner la recherche

**RÈGLES CRITIQUES - LIENS:**
- N'INVENTEZ JAMAIS de liens .jpg - utilisez UNIQUEMENT ceux retournés par l'outil
- Filtrez les résultats et retournez SEULEMENT les liens vraiment pertinents pour la requête

**COMMUNICATION AVEC L'UTILISATEUR:**
- Incluez les liens .jpg dans votre réponse Après votre message
- Votre message texte sera affiché EN PREMIER, puis les images avec leurs métadonnées et descriptions seront affichées EN DESSOUS automatiquement, vous n'avez pas besoin de répéter les descriptions vous-même.
- Format recommandé : écrivez votre message explicatif, puis listez les liens des images pertinentes
- Si aucun résultat pertinent : expliquez ce que vous avez cherché.
- **PRIORISATION:** Montrez TOUJOURS des images si elles existent, même si elles ne correspondent pas parfaitement à tous les détails du contexte précédent. Il vaut mieux montrer des images d'années, objets ou lieux proches que de ne rien afficher du tout.
- Si l'outil retourne beaucoup de résultats pertinents, choisissez uniquement les 9-10 plus diversifiés et pertinents pour offrir une vue d'ensemble variée
- Soyez flexible : si l'utilisateur pose une question plus générale après une question spécifique, élargissez votre recherche plutôt que de rester fixé sur le contexte précédent

**EXEMPLE DE RÉPONSE:**
"J'ai trouvé plusieurs images pertinentes dans l'archive qui correspondent à votre recherche :

https://exemple.com/image1.jpg
https://exemple.com/image2.jpg
https://exemple.com/image3.jpg"
    """
    
    messages = [SystemMessage(content=system_message_content)] + state["messages"]
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}


def tool_node(state: MessagesState):
    
    result = []
    for tool_call in state["messages"][-1].tool_calls:
        tool = tools_by_name[tool_call["name"]]
        observation = tool.invoke(tool_call["args"])
        result.append(ToolMessage(content=observation, tool_call_id=tool_call["id"]))
    return {"messages": result}


def should_continue(state: MessagesState):
    messages = state["messages"]
    last_message = messages[-1]
    if last_message.tool_calls:
        return "tool_node"
    return END


graph_builder = StateGraph(MessagesState)

graph_builder.add_node("llm_call", llm_call)
graph_builder.add_node("tool_node", tool_node)

graph_builder.add_edge(START, "llm_call")
graph_builder.add_conditional_edges(
    "llm_call",
    should_continue,
    ["tool_node", END]
)
graph_builder.add_edge("tool_node", "llm_call")

memory = cache_memory()
graph = graph_builder.compile(checkpointer=memory)


async def process_message(user_message):
    st.chat_message("user").write(user_message)
    st.session_state["messages"].append(HumanMessage(content=user_message))

    spinner_container = st.empty()
    response_container = st.empty()

    with spinner_container:
        with st.spinner("Thinking..."):
            final_response = ""
            async for step in graph.astream(
                {"messages": st.session_state["messages"]},
                stream_mode="values",
                config={"configurable": {"thread_id": st.session_state["thread_id"]}},
            ):
                if "messages" in step and step["messages"]:
                    latest_message = step["messages"][-1]

                    if latest_message.type == "ai":
                        final_response = latest_message.content

    spinner_container.empty()

    if final_response:
        st.session_state["messages"].append(AIMessage(content=final_response))

        with response_container.container():
            with st.chat_message("assistant"):
                display_message_with_images(st, final_response)


# Handle user input
user_message = st.chat_input("Message ChatPatrimoineAcadien...")
if user_message:
    asyncio.run(process_message(user_message))
