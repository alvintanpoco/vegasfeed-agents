from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.responses import JSONResponse
from agents import Agent, Runner
from vercel_streaming import vercel_format_stream  # must format according to Vercel's streaming protocol

app = FastAPI()

agent = Agent(
    name="Vegas Concierge",
    instructions="You're a Vegas show guide. Recommend fun shows based on age and preferences.",
)

@app.post("/orchestrate")
async def orchestrate(request: Request):
    data = await request.json()

    # Extract message safely
    if "messages" in data and isinstance(data["messages"], list):
        message = data["messages"][-1].get("content")
    elif "message" in data:
        message = data["message"]
    else:
        return JSONResponse(content={"error": "No message provided"}, status_code=400)

    if not message:
        return JSONResponse(content={"error": "Empty message."}, status_code=400)

    result = await Runner.run(agent, message)

    # Apply Vercel AI SDK format
    async def streamer():
        async for chunk in vercel_format_stream(result.final_output):
            yield chunk

    return StreamingResponse(streamer(), media_type="text/plain")
