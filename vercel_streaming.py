import json
from typing import AsyncGenerator
from fastapi.responses import StreamingResponse


def vercel_format_stream(generator: AsyncGenerator[str, None]):
    async def formatted_generator():
        async for chunk in generator:
            escaped = json.dumps(chunk)[1:-1]  # escape and strip quotes
            formatted = f'0:"{escaped}"\n'
            yield formatted.encode("utf-8")
    return StreamingResponse(formatted_generator(), media_type="text/plain")
