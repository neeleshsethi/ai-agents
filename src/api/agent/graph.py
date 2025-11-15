from pydantic import BaseModel
from typing import List, Dict, Any, Annotated
from operator import add
from api.agent.agents import agent_node, intent_router_node, ToolCall, RAGUsedContext
from api.agent.utils.utils import get_tool_descriptions
from api.agent.tools import get_formatted_context
from langgraph.graph import START, END, StateGraph
from langgraph.prebuilt import ToolNode
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue
import numpy as np
from langgraph.checkpoint.postgres import PostgresSaver
from api.core.config import config as app_config
import logging

logger = logging.getLogger(__name__)


class State(BaseModel):
    messages: Annotated[List[Any], add] = []
    question_relevant: bool = False
    iteration: int = 0
    answer: str = ""
    available_tools: List[Dict[str, Any]] = []
    tool_calls: List[ToolCall] = []
    final_answer: bool = False
    references: Annotated[List[RAGUsedContext], add] = []


    #### Routers

def tool_router(state: State) -> str:
    """Decide whether to continue or end"""
    
    if state.final_answer:
        return "end"
    elif state.iteration > 2:
        return "end"
    elif len(state.tool_calls) > 0:
        return "tools"
    else:
        return "end"


def intent_router_conditional_edges(state: State):

    if state.question_relevant:
        return "agent_node"
    else:
        return "end"
    

workflow = StateGraph(State)

tools = [get_formatted_context]
tool_node = ToolNode(tools)
tool_descriptions = get_tool_descriptions(tools)

workflow.add_node("agent_node", agent_node)
workflow.add_node("tool_node", tool_node)
workflow.add_node("intent_router_node", intent_router_node)

workflow.add_edge(START, "intent_router_node")

workflow.add_conditional_edges(
    "intent_router_node",
    intent_router_conditional_edges,
    {
        "agent_node": "agent_node",
        "end": END
    }
)

workflow.add_conditional_edges(
    "agent_node",
    tool_router,
    {
        "tools": "tool_node",
        "end": END
    }
)

workflow.add_edge("tool_node", "agent_node")



def run_agent(question: str, thread_id: str) -> str:
    logger.info(f"run_agent called with thread_id: {thread_id}")
    logger.info(f"Question: {question}")

    langgraph_config = {"configurable":{"thread_id": thread_id}}
    logger.info(f"LangGraph config: {langgraph_config}")

    with PostgresSaver.from_conn_string(app_config.SUPABASE_DB_URL) as checkpointer:
        graph = workflow.compile(checkpointer=checkpointer)

        # Check existing state
        try:
            current_state = graph.get_state(langgraph_config)
            logger.info(f"Current checkpoint state exists: {bool(current_state.values)}")
            if current_state.values:
                logger.info(f"Existing state keys: {current_state.values.keys()}")
                logger.info(f"Existing messages count: {len(current_state.values.get('messages', []))}")
        except Exception as e:
            logger.error(f"Error getting state: {e}")

        initial_state = {
            'messages': [
                {
                    'role': 'user',
                    'content': question
                }
            ],
            'iteration': 0,
            'available_tools': tool_descriptions
        }

        logger.info(f"Invoking graph with initial_state containing {len(initial_state['messages'])} messages")
        result = graph.invoke(initial_state, config=langgraph_config)
        logger.info(f"Graph execution completed. Result keys: {result.keys()}")
        logger.info(f"Result messages count: {len(result.get('messages', []))}")

    return result


def run_agent_wrapper(question: str, thread_id: str):
    qdrant_client = QdrantClient(
    url="https://511b707b-5120-4c5e-8f7f-cb3a72cb82f4.us-west-2-0.aws.cloud.qdrant.io:6333", 
    api_key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.9BuL_6z6hC7gHfXmMOB2SvlWtM3t6wchSuocbm-6MHE",
)
    result = run_agent(question, thread_id)
    used_context = []
    dummy_vector = np.zeros(1536).tolist()

    for item in result.get("references", []):
        payload = qdrant_client.query_points(
            collection_name="Amazon-items-collection-02-hybrid-search",
            query=dummy_vector,
            using="text-embedding-3-small",
            limit=1,
            with_payload=True,
            query_filter=Filter(
                must=[
                    FieldCondition(
                        key="parent_asin", 
                        match=MatchValue(value=item.id))
                ]
            )
        ).points[0].payload
        image_url = payload.get("image")
        price = payload.get("price")
        if image_url:
            used_context.append({"image_url": image_url, "price": price, "description": item.description})

    return {
        "answer": result.get("answer"),
        "used_context": used_context
    }




