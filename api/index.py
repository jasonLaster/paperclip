import sys
from contextlib import asynccontextmanager
from pathlib import Path

src_dir = Path(__file__).parents[1] / "src"
sys.path.insert(0, str(src_dir))

import server

app = server.mcp.http_app(
    path="/mcp/",
    stateless_http=True,
    transport="http",
)

_fastmcp_lifespan = app.router.lifespan_context
_paperclip_setup_complete = False


@asynccontextmanager
async def paperclip_lifespan(asgi_app):
    global _paperclip_setup_complete

    if not _paperclip_setup_complete:
        await server.setup()
        _paperclip_setup_complete = True

    async with _fastmcp_lifespan(asgi_app) as state:
        yield state


app.router.lifespan_context = paperclip_lifespan
