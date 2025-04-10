from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from agents import Agent, Runner

app = FastAPI()

agent = Agent(
    name="Vegas Concierge",
    instructions="You're a Vegas show guide. Recommend fun shows based on age and preferences.",
)

@app.post("/orchestrate")
async def orchestrate(request: Request):
    data = await request.json()
    message = data.get("message")

    if not message:
        return {"error": "No message provided"}

    result = await Runner.run(agent, message)
    
    async def streamer():
        yield result.final_output

    return StreamingResponse(streamer(), media_type="text/plain")
