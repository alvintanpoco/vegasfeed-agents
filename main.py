from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, JSONResponse
from agents import Agent, Runner

app = FastAPI()

agent = Agent(
    name="Vegas Concierge",
    instructions="You're a Vegas show guide. Recommend fun shows based on age and preferences.",
)

@app.post("/orchestrate")
async def orchestrate(request: Request):
    try:
        data = await request.json()
        messages = data.get("messages", [])

        if not isinstance(messages, list) or len(messages) == 0:
            return JSONResponse(content={"error": "No messages array provided"}, status_code=400)

        # Log the raw payload for debugging
        print("📩 Received messages:", messages)

        last_message = messages[-1]
        message = last_message.get("content") if isinstance(last_message, dict) else None

        if not message:
            return JSONResponse(content={"error": "No message provided"}, status_code=400)

        # Run the agent
        result = await Runner.run(agent, message)

        async def streamer():
            yield result.final_output

        return StreamingResponse(streamer(), media_type="text/plain")

    except Exception as e:
        print("❌ Error in /orchestrate:", str(e))
        return JSONResponse(content={"error": "Internal server error", "details": str(e)}, status_code=500)
