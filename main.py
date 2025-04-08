from dotenv import load_dotenv; load_dotenv()

# agents-backend/main.py

from fastapi import FastAPI, Request
from agents import Agent, Runner
import asyncio

app = FastAPI()

# Define your orchestrator agent
orchestrator_agent = Agent(
    name="Orchestrator Agent",
    instructions="You are a Vegas entertainment expert. Provide recommendations, answer questions, and reason intelligently about the user's needs.",
)

@app.post("/orchestrate")
async def orchestrate(request: Request):
    body = await request.json()
    message = body.get("message", "")

    result = await Runner.run(orchestrator_agent, input=message)

    return {"reply": result.final_output}
