import json
from typing import AsyncGenerator
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, JSONResponse
from agents import Agent, Runner  # Ensure these are correctly imported from your agents module

def vercel_format_stream(generator: AsyncGenerator[str, None]):
    """
    This helper function wraps an asynchronous generator so that each chunk is JSON-escaped,
    formatted, and then yielded as bytes in a streaming HTTP response.
    """
    async def formatted_generator():
        async for chunk in generator:
            print("[Streaming Chunk]", chunk)  # Debug: print raw chunk
            # JSON-escape the chunk and strip the surrounding quotes
            escaped = json.dumps(chunk)[1:-1]
            formatted = f'0:"{escaped}"\n'
            print("[Formatted Chunk]", formatted)  # Debug: print formatted chunk
            yield formatted.encode("utf-8")
    return StreamingResponse(formatted_generator(), media_type="text/plain")

# Create an instance of the FastAPI app
app = FastAPI()

# Initialize the agent with appropriate instructions
agent = Agent(
    name="Vegas Concierge",
    instructions="You're a Vegas show guide. Recommend fun shows based on age and preferences.",
)

@app.post("/orchestrate")
async def orchestrate(request: Request):
    print("[Request] Incoming request")
    try:
        # Parse the incoming JSON payload
        data = await request.json()
        print("[Request JSON]", data)

        # Accepts either format: a messages list or a single message
        if "messages" in data and isinstance(data["messages"], list):
            message = data["messages"][-1].get("content")
        elif "message" in data:
            message = data["message"]
        else:
            return JSONResponse(content={"error": "No message provided"}, status_code=400)

        if not message:
            return JSONResponse(content={"error": "Empty message content"}, status_code=400)

        print("[Message Parsed]", message)

        # Run the agent with the provided message
        result = await Runner.run(agent, message)

        async def streamer():
            # If the result provides a streaming interface, iterate over it
            if hasattr(result, "stream"):
                async for chunk in result.stream:
                    print("[Streaming Chunk]", chunk)
                    yield chunk
            else:
                # Fallback: yield the complete content as a single chunk
                # It assumes that the complete result is stored in result.content.
                # Adjust this as necessary to match your RunResult object's attribute for full text.
                print("[Complete Result]", result.content)
                yield result.content

        return vercel_format_stream(streamer())

    except Exception as e:
        print("[Error]", str(e))
        return JSONResponse(
            content={"error": "Internal server error", "details": str(e)},
            status_code=500
        )
