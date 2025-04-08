import streamlit as st
from langchain_voyageai import VoyageAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_core.messages import HumanMessage
from PIL import Image
from pydantic import BaseModel
from langchain_google_genai import ChatGoogleGenerativeAI
import uuid
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph.message import add_messages
from langgraph.graph import END, START, MessagesState, StateGraph
from langchain_core.tools import tool
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.messages import SystemMessage
from langgraph.graph import END, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.documents import Document
from typing_extensions import List, TypedDict
import re
from sidebar_answers import show_questions_sidebar
from langchain_openai import ChatOpenAI

# Set page configuration
st.set_page_config(
    page_title="Images Patrimoniales",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="auto"
)

WELCOME_MESSAGE = "Comment puis-je vous aider ? | How can I help you ?"
PINECONE_INDEX_NAME = "short-descriptions"

# Define available model options
MODEL_OPTIONS = {
    "Gemini 2.5 Pro": "google/gemini-2.5-pro-preview-03-25",
    "O3 Mini": "openai/o3-mini",
    "Claude 3.7 Sonnet": "anthropic/claude-3.7-sonnet",
    "Gemini 2.0 Flash": "google/gemini-2.0-flash-001"
}

# Initialize model selection in session state if not present
if "selected_model" not in st.session_state:
    st.session_state["selected_model"] = "O3 Mini"

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

embeddings = VoyageAIEmbeddings(
    model="voyage-3"
)


if "thread_id" not in st.session_state:
    st.session_state["thread_id"] = str(uuid.uuid4())
# Initialize messages if not in session state
if "messages" not in st.session_state:
    st.session_state["messages"] = [AIMessage(content=WELCOME_MESSAGE)]

@st.cache_resource
def cache_memory():
    return MemorySaver()

def reset_chat_history():
    st.session_state["messages"] = [AIMessage(content=WELCOME_MESSAGE)]
    st.session_state["thread_id"] = str(uuid.uuid4())

with st.sidebar:
    st.button(
        "Nouveau chat",
        on_click=reset_chat_history,
        icon=":material/edit_square:",
        use_container_width=True,
    )
    
    # Add model selection dropdown
    st.selectbox(
        "Sélectionner un modèle",
        options=list(MODEL_OPTIONS.keys()),
        key="selected_model",
    )
    
    show_questions_sidebar()
    

# New function to display images at the top of a message
def display_message_with_images(container, message_content):
    """
    Displays any JPG images at the top of the message, then shows the original content.
    
    Args:
        container: The Streamlit container to write into
        message_content (str): The message text that may contain image URLs
    """
    # Use a non-greedy pattern to find URLs that end with .jpg
    # This will correctly parse URLs even in malformed Markdown links
    jpg_urls = re.findall(r'(https?://[^)\]]*?\.jpg)', message_content, re.IGNORECASE)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_urls = [url for url in jpg_urls if not (url in seen or seen.add(url))]
    
    # If images found, display them at the top
    if unique_urls:
        # Create an expander for images
        with container.expander("Images trouvées", expanded=True):
            for url in unique_urls:
                try:
                    st.image(url)
                    #st.caption(url)
                except Exception:
                    st.warning(f"Impossible de charger l'image: {url}")
    
    # Display the original message content unchanged
    container.markdown(message_content)

# Update message history display
for message in st.session_state["messages"]:
    if isinstance(message, AIMessage):
        with st.chat_message("assistant"):
            display_message_with_images(st, message.content)
    elif isinstance(message, HumanMessage):
        st.chat_message("user").write(message.content)

from langchain.retrievers import ContextualCompressionRetriever
from langchain_voyageai import VoyageAIRerank

# Create the base vector store
vector_store = PineconeVectorStore(
    #pinecone_api_key=PINECONE_API_KEY,
    index_name=PINECONE_INDEX_NAME,
    embedding=embeddings,
)

# Set up the base retriever
base_retriever = vector_store.as_retriever(
    search_type="similarity_score_threshold",
    search_kwargs={"k": 12, "score_threshold": 0.5},
)

# Create the reranker compressor
compressor = VoyageAIRerank(
    model="rerank-2", 
    top_k=6
)

# Create the compression retriever once (outside the function)
compression_retriever = ContextualCompressionRetriever(
    base_compressor=compressor, 
    base_retriever=base_retriever
)

@tool(response_format="content_and_artifact")
def search_image_archive_tool(query: str,
                              #year: str = None,
                              #locality: str = None
                              ):
    """Retrieve information related to a query."""
    # Prepare filter dictionary - only include non-None values
    # filter_dict = {}
    # # if year is not None:
    # #     filter_dict["year"] = year
    # # if locality is not None:
    # #     filter_dict["locality"] = locality
    
    # # Use filter only if we have filter criteria
    # if filter_dict:
    #     retrieved_docs = compression_retriever.invoke(query, filter=filter_dict)
    #     print(f"Filter applied: {filter_dict}")
    #else:
    retrieved_docs = compression_retriever.invoke(query)
    print("No filter applied")
    
    # Serialize the results for display
    serialized = "\n\n".join(
        (f"Source: {doc.metadata}\n" f"Content: {doc.page_content}")
        for doc in retrieved_docs
    )

    return serialized, retrieved_docs


class State(MessagesState):
    context: List[Document]


# Step 1: Generate an AIMessage that may include a tool-call to be sent.
def query_or_respond(state: State):
    """Generate tool call for retrieval or respond."""
    llm_with_tools = llm.bind_tools([search_image_archive_tool])
    response = llm_with_tools.invoke(state["messages"])
    # MessagesState appends messages to state instead of overwriting
    return {"messages": [response]}


# Step 2: Execute the retrieval.
tools = ToolNode([search_image_archive_tool])


# Step 3: Generate a response using the retrieved content.
def generate(state: MessagesState):
    """Generate answer."""
    # Get generated ToolMessages
    recent_tool_messages = []
    for message in reversed(state["messages"]):
        if message.type == "tool":
            recent_tool_messages.append(message)
        else:
            break
    tool_messages = recent_tool_messages[::-1]
    
    # Format into prompt - properly extract content from tool messages
    docs_content = ""
    for msg in tool_messages:
        if hasattr(msg, 'content') and msg.content:
            docs_content += f"\n\nTool Result: {msg.content}"
    
    # If no content was found in the standard way, try to access tool output differently
    if not docs_content and tool_messages:
        for msg in tool_messages:
            # Try different ways to access the content
            if hasattr(msg, 'content') and msg.content:
                docs_content += f"\n\nTool Result: {msg.content}"
            elif hasattr(msg, 'result') and msg.result:
                docs_content += f"\n\nTool Result: {msg.result}"
            # Access function_call result if available
            elif hasattr(msg, 'function_call') and msg.function_call:
                docs_content += f"\n\nTool Result: {msg.function_call}"
    
    # Add a clear indicator in the prompt to use the retrieved information
    system_message_content = (
        """Vous êtes un agent assistant spécialisé dans la recherche d'images historiques et de leurs descriptions au sein d'une archive numérique dédiée. Vous disposez d'un outil spécifique (`search_image_archive_tool`) pour effectuer ces recherches et accéder aux liens directs et aux métadonnées associées.

**Votre Mission :** Répondre aux demandes de l'utilisateur en trouvant et en fournissant les liens directs vers les images pertinentes et leurs descriptions, en utilisant **exclusivement** votre outil `search_image_archive_tool`.

**IMPORTANT: Voici les résultats de recherche que vous DEVEZ utiliser dans votre réponse. Ces informations proviennent des archives et contiennent des données essentielles pour répondre à la requête de l'utilisateur:**
"""
        "\n\n"
        f"{docs_content}"
        "\n\n"
        """
**Étapes à Suivre Impérativement :**

1.  **Comprendre la Demande :** Analysez précisément la requête de l'utilisateur pour extraire les critères de recherche clés (sujets, mots-clés, noms propres, dates spécifiques ou périodes, lieux géographiques, etc.). Clarifiez si nécessaire, mais privilégiez l'action.

2.  **Exécuter la Recherche :** Utilisez **obligatoirement** et **systématiquement** votre outil `search_image_archive_tool` avec la requête préparée pour chercher dans l'archive. Ne tentez jamais de répondre de mémoire ou sans avoir consulté l'outil pour cette demande spécifique.

3.  **Restituer les Résultats :**
    * **Succès :** Si l'outil `search_image_archive_tool` trouve des correspondances pertinentes :
        * Présentez les résultats de manière claire et organisée.
        * Pour chaque image trouvée, fournissez :
            * Le **lien direct** vers l'image (URL).
            * La **description** associée, telle que retournée par l'outil. S'il n'y a pas de description, mentionnez-le ou omettez simplement cette partie pour l'entrée concernée.
        * S'il y a de nombreux résultats, vous pouvez en présenter une sélection (par exemple, les 3-5 plus pertinents) et mentionner que d'autres existent.
    * **Échec :** Si l'outil `search_image_archive_tool` ne retourne aucun résultat pertinent ou signale une erreur lors de la recherche :
        * Informez l'utilisateur poliment et clairement que la recherche dans l'archive via l'outil n'a donné aucun résultat pour les critères spécifiés.
        * Ne suggérez pas d'autres sources externes à moins d'y être explicitement invité ou si cela fait partie de vos capacités étendues.

4.  **Intégrité et Focalisation :**
    * Votre réponse doit se baser **uniquement** sur les informations (liens, descriptions) retournées par l'outil `search_image_archive_tool`.
    * N'inventez pas d'informations, de liens ou de descriptions.
    * Restez concentré sur la tâche de recherche via l'outil ; évitez les conversations non pertinentes.
IMPORTANT : Si vous ne trouvez pas d'images pertinentes, ne vous inquiétez pas. Répondez simplement que vous n'avez trouvé aucune image correspondante dans l'archive numérique. Ne proposez pas d'autres suggestions ou alternatives, sauf si cela est explicitement demandé par l'utilisateur.
Ne jamais retourner des informations qui ne sont pas retournées par l'outil `search_image_archive_tool`. Informe l'utilisateur que vous n'avez trouvé aucune image correspondante dans l'archive numérique. Ne proposez pas d'autres suggestions ou alternatives.
Eviter toujours de retourner des informations qui ne sont pas retournées par l'outil `search_image_archive_tool`.
Filter extra images that are not relevant to the query.
    """
    )
    conversation_messages = [
        message
        for message in state["messages"]
        if message.type in ("human", "system")
        or (message.type == "ai" and not message.tool_calls)
    ]
    prompt = [SystemMessage(system_message_content)] + conversation_messages

    # Run
    response = llm.invoke(prompt)
    context = []
    for tool_message in tool_messages:
        # Try to access artifact if it exists
        if hasattr(tool_message, 'artifact'):
            context.extend(tool_message.artifact)
    return {"messages": [response], "context": context}

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


user_message = st.chat_input("Message Patrimoine images...")
if user_message:
    st.chat_message("user").write(user_message)
    st.session_state["messages"].append(HumanMessage(content=user_message))
    
    with st.chat_message("assistant"):
        # Create a container for tool calls that will persist
        tool_calls_container = st.container(border=True)
        response_placeholder = st.empty()
        response_container = st.container()
        
        # Add spinner to indicate processing
        with st.spinner("Recherche dans les archives en cours..."):
            # Process the message through the graph
            final_response = ""
            for step in graph.stream(
                {"messages": st.session_state["messages"]},
                stream_mode="values", 
                config={"configurable": {"thread_id": st.session_state["thread_id"]}}
            ):
                if "messages" in step and step["messages"]:
                    latest_message = step["messages"][-1]
                    
                    # Check if it's a tool message that should be displayed in the tool call container
                    #if latest_message.type == "tool":
                        #with tool_calls_container:
                            #st.write(f"🔍 Searching archives: {latest_message.name}")
                            # Display tool content for debugging
                            #if hasattr(latest_message, 'content'):
                                #st.write("Tool content:", latest_message.content + "..." if len(latest_message.content) > 100 else latest_message.content)
                    
                    # If it's an AI message, update the response
                    if latest_message.type == "ai":
                        final_response = latest_message.content
                        response_placeholder.empty()  # Clear previous content
                        display_message_with_images(response_container, final_response)
                
                # Debug the context
                # if "context" in step and step["context"]:
                #     with tool_calls_container:
                #         st.write("📄 Retrieved context (first document):", 
                #                  step["context"][0].page_content[:100] + "..." if step["context"] and len(step["context"]) > 0 and hasattr(step["context"][0], 'page_content') else "No page_content found")
            
            # After streaming completes, add the final message to session state
            if final_response:
                st.session_state["messages"].append(AIMessage(content=final_response))
