# Standard library imports
import asyncio
import json
import os
import re
import time
import uuid

# Third-party imports
import streamlit as st
from langchain.retrievers import ContextualCompressionRetriever

# Language models and embeddings
from langchain_cohere import CohereEmbeddings

# Langchain imports
from langchain_core.documents import Document
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain_pinecone import PineconeVectorStore
from langchain_voyageai import VoyageAIEmbeddings, VoyageAIRerank

# Langgraph imports
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from PIL import Image
from pydantic import BaseModel
from typing_extensions import List, TypedDict

# Local imports
from sidebar_answers import show_questions_sidebar

embeddings = CohereEmbeddings(model="embed-multilingual-v3.0")

PINECONE_INDEX_NAME = "short-descriptions-cohere"
WELCOME_MESSAGE = "Comment puis-je vous aider ? | How can I help you ?"
MODEL_OPTIONS = {
    "GPT-4.1": "openai/gpt-4.1",
    "Gemini 2.5 Pro": "google/gemini-2.5-pro",
    "O3 Mini": "openai/o3-mini",
    "Claude 4 Sonnet": "anthropic/claude-sonnet-4",
    "Gemini 2.5 Flash": "google/gemini-2.5-flash",
}

# Set page configuration
st.set_page_config(
    page_title="Images Patrimoniales",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="auto",
)

# Initialize embeddings and retrieval system
embeddings = CohereEmbeddings(model="embed-multilingual-v3.0")

vector_store = PineconeVectorStore(
    index_name=PINECONE_INDEX_NAME,
    embedding=embeddings,
)
# Commented code for alternate configuration
# PINECONE_INDEX_NAME = "short-descriptions"
# embeddings = VoyageAIEmbeddings(
#     model="voyage-3"
# )
base_retriever = vector_store.as_retriever(
    search_type="similarity_score_threshold",
    search_kwargs={"k": 12, "score_threshold": 0.5},
)

compressor = VoyageAIRerank(model="rerank-2", top_k=6)

compression_retriever = ContextualCompressionRetriever(
    base_compressor=compressor, base_retriever=base_retriever
)

# Session state initialization
if "selected_model" not in st.session_state:
    st.session_state["selected_model"] = "Gemini 2.5 Flash"

if "thread_id" not in st.session_state:
    st.session_state["thread_id"] = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state["messages"] = [AIMessage(content=WELCOME_MESSAGE)]

# LLM initialization
llm = ChatOpenAI(
    openai_api_key=st.secrets["OPENROUTER_API_KEY"],
    openai_api_base=st.secrets["OPENROUTER_BASE_URL"],
    model_name=MODEL_OPTIONS[st.session_state["selected_model"]],
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


# UI Components
@st.fragment
def display_message_with_images(container, message_content):
    """
    Displays any JPG images at the top of the message, then shows the original content.

    Args:
        container: The Streamlit container to write into
        message_content (str): The message text that may contain image URLs
    """

    start = time.time()

    jpg_urls = re.findall(r"(https?://[^)\]]*?\.jpg)", message_content, re.IGNORECASE)

    seen = set()
    unique_urls = [url for url in jpg_urls if not (url in seen or seen.add(url))]

    if not unique_urls:
        container.markdown(message_content)
        return

    metadata_dict = load_metadata()
    figure_counter = 1

    for url in unique_urls:
        try:
            container.image(url, width=500)  # Resize images to 400px width
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


# Sidebar configuration
with st.sidebar:
    st.button(
        "Nouveau chat",
        on_click=reset_chat_history,
        icon=":material/edit_square:",
        use_container_width=True,
    )

    st.selectbox(
        "Sélectionner un modèle",
        options=list(MODEL_OPTIONS.keys()),
        key="selected_model",
    )

    show_questions_sidebar()

# Display chat history
display_chat_history()


# Tool definition
@tool(response_format="content_and_artifact")
def search_image_archive_tool(query: str):
    """
    Retrieve information related to a query from the image archive.
    
    Args:
        query (str): The search query to find relevant images
        
    Returns:
        Tuple: (serialized results, retrieved documents)
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


# Graph components
class State(MessagesState):
    context: List[Document]


def query_or_respond(state: State):
    system_message_content = """ 
    You are a specialized assistant for searching historical images in a digital archive. Your primary goal is to find relevant images and return their direct links.

**Instructions:**

1. **Search First, Ask Later**: For any user query, immediately use `search_image_archive_tool` with the best interpretation of their request. Don't ask for clarification upfront - try the search first even when the request is general or vague.

2. **Filter and Return Links**: From the search results, identify and return ONLY the direct image links (.jpg URLs) that are truly relevant to the user's query. Be selective - filter out images that don't match the specific request.

3. **Handle No Results**: Only if the search returns no relevant results, then inform the user and ask them to be more specific about what they're looking for.

4. **Response Format**: Simply include the relevant .jpg URLs in your response. The system will automatically display the images and their metadata to the user.

**Key Points:**
- Always use `search_image_archive_tool` for every query
- Prioritize action over clarification
- Filter results to show only relevant images
- Only ask for clarification if no relevant results are found
- Base responses ONLY on tool results - never invent links or information
    """
    
    # Create messages with system message first
    messages = [SystemMessage(content=system_message_content)] + state["messages"]
    
    llm_with_tools = llm.bind_tools([search_image_archive_tool])
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}


tools = ToolNode([search_image_archive_tool])


def generate(state: MessagesState):
    recent_tool_messages = []
    for message in reversed(state["messages"]):
        if message.type == "tool":
            recent_tool_messages.append(message)
        else:
            break
    tool_messages = recent_tool_messages[::-1]
    
    # Format tool results for context
    docs_content = ""
    for msg in tool_messages:
        if hasattr(msg, "content") and msg.content:
            docs_content += f"\n\nTool Result: {msg.content}"

    system_message_content = f"""
    You are a specialized assistant for searching historical images in a digital archive. 

**SEARCH RESULTS - Use these results from the archive to answer the user's query:**

{docs_content}

**Instructions:**
- Based on the search results above, provide relevant .jpg URLs that match the user's query
- Be selective - only include images that truly match the request
- Simply include the relevant URLs in your response
- Do not invent or create URLs that weren't in the search results
    """
    
    conversation_messages = [
        message
        for message in state["messages"]
        if message.type in ("human", "ai") and not getattr(message, "tool_calls", None)
    ]
    
    # Create proper message list with system message first
    messages = [SystemMessage(content=system_message_content)] + conversation_messages
    
    print(f"Generate - Messages being sent to LLM: {[msg.type for msg in messages]}")
    
    response = llm.invoke(messages)
    context = []
    for tool_message in tool_messages:
        if hasattr(tool_message, "artifact"):
            context.extend(tool_message.artifact)
    return {"messages": [response], "context": context}


# Graph setup
graph_builder = StateGraph(MessagesState)

graph_builder.add_node(query_or_respond)
graph_builder.add_node(tools)
graph_builder.add_node(generate)

graph_builder.set_entry_point("query_or_respond")
graph_builder.add_conditional_edges(
    "query_or_respond",
    tools_condition,
    {END: END, "tools": "tools"},
)
graph_builder.add_edge("tools", "generate")
graph_builder.add_edge("generate", END)

memory = cache_memory()
graph = graph_builder.compile(checkpointer=memory)


# Message processing
async def process_message(user_message):
    st.chat_message("user").write(user_message)
    st.session_state["messages"].append(HumanMessage(content=user_message))

    # First, create an empty container outside the chat message context
    # This ensures complete separation between spinner and final response
    spinner_container = st.empty()
    response_container = st.empty()

    # Use the spinner in its own isolated container
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

    # Completely remove the spinner before showing any response
    spinner_container.empty()

    # Now create the assistant message in a completely separate container
    if final_response:
        # Add to session state first
        st.session_state["messages"].append(AIMessage(content=final_response))

        # Then render in a completely fresh container
        with response_container.container():
            with st.chat_message("assistant"):
                display_message_with_images(st, final_response)


# Handle user input
user_message = st.chat_input("Message Patrimoine images...")
if user_message:
    asyncio.run(process_message(user_message))
