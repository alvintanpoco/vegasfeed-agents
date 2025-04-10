import json
from typing import AsyncGenerator
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, JSONResponse
from agents import Agent, Runner


def vercel_format_stream(generator: AsyncGenerator[str, None]):
    async def formatted_generator():
        async for chunk in generator:
            print("[Streaming Chunk]", chunk)  # Debugging line
            escaped = json.dumps(chunk)[1:-1]  # escape and strip quotes
            formatted = f'0:"{escaped}"\n'
            print("[Formatted Chunk]", formatted)  # Debugging line
            yield formatted.encode("utf-8")
    return StreamingResponse(formatted_generator(), media_type="text/plain")


app = FastAPI()

agent = Agent(
    name="Vegas Concierge",
    instructions="You're a Vegas show guide. Recommend fun shows based on age and preferences.",
)


@app.post("/orchestrate")
async def orchestrate(request: Request):
    print("[Request] Incoming request")  # Debug
    try:
        data = await request.json()
        print("[Request JSON]", data)  # Debug

        # Accepts either format
        if "messages" in data and isinstance(data["messages"], list):
            message = data["messages"][-1].get("content")
        elif "message" in data:
            message = data["message"]
        else:
            return JSONResponse(content={"error": "No message provided"}, status_code=400)

        if not message:
            return JSONResponse(content={"error": "Empty message content"}, status_code=400)

        print("[Message Parsed]", message)  # Debug
        result = await Runner.run(agent, message)
        print("[Agent Result]", result.final_output)  # Debug

        async def streamer():
            yield result.final_output

        return vercel_format_stream(streamer())

    except Exception as e:
        print("[Error]", str(e))
        return JSONResponse(content={"error": "Internal server error", "details": str(e)}, status_code=500)
