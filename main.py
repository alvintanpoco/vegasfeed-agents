from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from agents import Agent, Runner
from fastapi.responses import JSONResponse


app = FastAPI()

agent = Agent(
    name="Vegas Concierge",
    instructions="You're a Vegas show guide. Recommend fun shows based on age and preferences.",
)

@app.post("/orchestrate")
async def orchestrate(request: Request):
    data = await request.json()

    # Accepts either format
    if "messages" in data and isinstance(data["messages"], list):
        message = data["messages"][-1]["content"]
    elif "message" in data:
        message = data["message"]
    else:
        return JSONResponse(content={"error": "No message provided"}, status_code=400)

    result = await Runner.run(agent, message)

    async def streamer():
        yield result.final_output

    return StreamingResponse(streamer(), media_type="text/plain")
