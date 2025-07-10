from qdrant_client import QdrantClient
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from opik import track, opik_context
from opik.integrations.openai import track_openai
from opik.integrations.langchain import OpikTracer
from langchain.prompts import PromptTemplate, ChatPromptTemplate
from core.config import config
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
import opik
import os

if config.COMET_API_KEY:
    os.environ["OPIK_API_KEY"] = config.COMET_API_KEY
os.environ["OPIK_PROJECT_NAME"] = config.COMET_PROJECT


@opik.track(name="Embedding")
def get_embedding(text):
    embeddings_model = OpenAIEmbeddings(model=config.EMBEDDING_MODEL)
    response = embeddings_model.embed_documents([text])
    return response[0]


@opik.track(name="Retrieve top k")
def retrieve_context(query, qdrant_client, top_k=5):
    query_embedding = get_embedding(query)
    print(f"Using collection name: {config.QDRANT_COLLECTION_NAME}")
    results = qdrant_client.query_points(
        collection_name=config.QDRANT_COLLECTION_NAME,
        query=query_embedding,
        limit=top_k,
    )

    retrieved_context_ids = []
    retrieved_context = []
    similarity_scores = []

    # Handle different result structures from qdrant_client.query_points()
    points = results.points if hasattr(results, 'points') else results
    
    for result in points:
        retrieved_context_ids.append(result.id)
        retrieved_context.append(result.payload['text'])
        similarity_scores.append(result.score)

    return {
        "retrieved_context_ids": retrieved_context_ids,
        "retrieved_context": retrieved_context,
        "similarity_scores": similarity_scores
    }



@opik.track(name="Format context")
def process_context(context):
    opik_context.update_current_span(
        input={"context": context},
    )
    formatted_context = ""
    for chunk in context["retrieved_context"]:
        formatted_context = formatted_context + f"-{chunk}\n"
    opik_context.update_current_span(
        output={"formatted_context": formatted_context}
    )
    return formatted_context

@opik.track(name="Build Prompt")
def build_prompt(context, question):
    opik_context.update_current_span(
        input={"context": context, "question": question},
    )
    processed_context = process_context(context)
    message = f"""
You are shopping assistant that can answer questions about product in stock.

You will be give list of questions and context.

Instructions:
- You need to answer question based on provided context only.
- Never use word context and refer to it as available product.

Context:
{processed_context}

Question:
{question}

    """
    final_prompt = ChatPromptTemplate.from_messages([('human',message)])
    opik_context.update_current_span(
        output={"prompt": message, "final_prompt": str(final_prompt)}
    )
    return final_prompt
    

def generate_answer(prompt_template):
    opik_tracer = OpikTracer(tags=["Generate answer"])
    model = ChatOpenAI(model = config.GENERATION_MODEL)
    
    # Debug: Print the prompt being sent
    
    try:
        prompt_value = prompt_template.invoke({})
        print(f"Prompt being sent to OpenAI: {prompt_value}")
    except Exception as e:
        print(f"Error formatting prompt: {e}")
    
    
    chain = prompt_template | model
    chain = chain.with_config({"callbacks": [opik_tracer]})
    response = chain.invoke({})
    
   # print(f"OpenAI response type: {type(response)}")
   # print(f"OpenAI response: {response}")
    
    # Extract the actual text content from the LLM response
    if hasattr(response, 'content'):
        return response.content
    elif isinstance(response, str):
        return response
    else:
        # For LLMResult objects, extract the text from generations
        return response.generations[0][0].text if response.generations else ""

    
    
@opik.track(name="RAG Pipeline")
def rag_pipeline(question, qdrant_client,top_k=5):
    retrieved_context = retrieve_context(question, qdrant_client, top_k)
    prompt = build_prompt(retrieved_context, question)
    answer = generate_answer(prompt)
    final_result = {
        'answer': answer,
        'question': question,
        "retrieved_context_ids": retrieved_context["retrieved_context_ids"],
        "retrieved_context": retrieved_context["retrieved_context"],
        "similarity_scores": retrieved_context["similarity_scores"]
    }
    return final_result



