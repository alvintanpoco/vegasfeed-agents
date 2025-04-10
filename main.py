import os
import json
import asyncio
from typing import AsyncGenerator
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, JSONResponse
from dotenv import load_dotenv
import openai
from concurrent.futures import ThreadPoolExecutor

# Load environment variables from .env file
load_dotenv()

# Set the API key for OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI()

# Use a thread pool for blocking IO (the OpenAI streaming call is synchronous)
executor = ThreadPoolExecutor(max_workers=1)

def openai_completion_generator(prompt: str):
    """
    This function calls the OpenAI ChatCompletion API in streaming mode.
    It is synchronous and returns a generator yielding chunks as they arrive.
    """
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "system", "content": prompt}],
        stream=True
    )
    # Iterate over the streaming response and yield each token part
    for chunk in response:
        # Each chunk is a dict; token text is in chunk.choices[0].delta.get("content", "")
        token = chunk.choices[0].delta.get("content", "")
        if token:
            yield token

async def async_openai_stream(prompt: str) -> AsyncGenerator[str, None]:
    """
    Wraps the synchronous openai_completion_generator in an asynchronous generator.
    Tokens are yielded as soon as they are available.
    """
    loop = asyncio.get_event_loop()

    def run_generator():
        return list(openai_completion_generator(prompt))
    
    # Run the synchronous generator in an executor so it doesn't block the event loop.
    tokens = await loop.run_in_executor(executor, run_generator)
    for token in tokens:
        # Optionally, yield token by token
        yield token

def vercel_format_stream(generator: AsyncGenerator[str, None]):
    """
    Wraps an async generator so that each chunk is JSON-escaped and formatted,
    then yields bytes in a StreamingResponse.
    """
    async def formatted_generator():
        async for chunk in generator:
            print("[Streaming Chunk]", chunk)  # Debug: print raw chunk
            # JSON-escape the chunk and strip surrounding quotes
            escaped = json.dumps(chunk)[1:-1]
            formatted = f'0:"{escaped}"\n'
            print("[Formatted Chunk]", formatted)
            yield formatted.encode("utf-8")
    return StreamingResponse(formatted_generator(), media_type="text/plain")

@app.post("/orchestrate")
async def orchestrate(request: Request):
    """
    Example endpoint that streams out a completion from OpenAI’s API.
    """
    try:
        data = await request.json()
        # Here we accept either "message" or "messages" (like your existing code)
        if "messages" in data and isinstance(data["messages"], list):
            message = data["messages"][-1].get("content")
        elif "message" in data:
            message = data["message"]
        else:
            return JSONResponse(content={"error": "No message provided"}, status_code=400)

        if not message:
            return JSONResponse(content={"error": "Empty message content"}, status_code=400)

        print("[Message Parsed]", message)

        # Use the message as a prompt (or customize your prompt as needed)
        prompt = f"You are a Vegas Concierge. User asks: {message}"

        # Create an asynchronous generator that yields tokens as they are produced.
        token_generator = async_openai_stream(prompt)

        return vercel_format_stream(token_generator)

    except Exception as e:
        print("[Error]", str(e))
        return JSONResponse(content={"error": "Internal server error", "details": str(e)},
                            status_code=500)
