# Paperclip MCP on Vercel

This repository copy includes a Vercel-compatible wrapper for the Paperclip MCP
server. The wrapper exposes Paperclip as a Python ASGI app at `/mcp/`.

Current verified preview as of June 26, 2026:

```text
https://paperclip-vercel-eodr6v8gp-jlasters-projects.vercel.app/mcp/
```

## Files

- `api/index.py` exports the ASGI `app` Vercel deploys as a Python function.
- `vercel.json` rewrites `/mcp` and `/mcp/*` to `api/index.py`.
- `requirements.txt` is the upstream Paperclip dependency set Vercel installs.

The wrapper uses `server.mcp.http_app(..., stateless_http=True)`. Stateless
Streamable HTTP matters on Vercel because requests can hit different function
instances.

## Deploy

Deploy a preview to the personal Vercel scope:

```bash
vercel deploy /Users/jaylast/.codex/mcp/paperclip-vercel -y --scope jlasters-projects
```

Promote an existing preview only when you intentionally want production:

```bash
vercel deploy /Users/jaylast/.codex/mcp/paperclip-vercel --prod -y --scope jlasters-projects
```

Vercel currently auto-detects the Python function. Do not add a `functions`
entry for `app.py`; in this CLI/runtime path it fails because function settings
must match files Vercel recognizes under `api/`.

## Deployment Protection

The `paperclip-vercel` project currently has Vercel SSO protection configured as
`all_except_custom_domains`. A plain request to the preview URL redirects to
Vercel SSO instead of reaching the MCP server.

Check the current state:

```bash
vercel project protection paperclip-vercel --scope jlasters-projects --format json
```

For clients that can send custom headers, use Vercel's automation bypass header:

```text
x-vercel-protection-bypass: <VERCEL_AUTOMATION_BYPASS_SECRET>
```

Do not commit the bypass token. Keep it in a local password manager or an
environment variable.

For clients that cannot send arbitrary headers, use one of these options:

- Disable SSO protection for this project if public access is acceptable.
- Attach a custom domain, because this project protection mode excludes custom domains.
- Run a small local proxy that adds `x-vercel-protection-bypass` before forwarding to Vercel.

Disable SSO protection:

```bash
vercel project protection disable paperclip-vercel --sso --scope jlasters-projects
```

Re-enable SSO protection:

```bash
vercel project protection enable paperclip-vercel --sso --scope jlasters-projects
```

Official Vercel references:

- [Deployment protection automation bypass](https://vercel.com/docs/deployment-protection/automated-agent-access)
- [Vercel CLI `curl`](https://vercel.com/docs/cli/curl)
- [Vercel Python functions](https://vercel.com/docs/functions/runtimes/python)

## Test

Vercel-authenticated protocol probe:

```bash
vercel curl /mcp/ \
  --deployment paperclip-vercel-eodr6v8gp-jlasters-projects.vercel.app \
  --scope jlasters-projects \
  -- \
  --request POST \
  --header 'content-type: application/json' \
  --header 'accept: application/json, text/event-stream' \
  --data '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"paperclip-test","version":"0.0.0"}}}'
```

Expected result: an MCP `initialize` response with `serverInfo.name` set to
`Paperclip MCP Server`.

List tools through Vercel protection bypass:

```bash
curl -sS 'https://paperclip-vercel-eodr6v8gp-jlasters-projects.vercel.app/mcp/' \
  -H "x-vercel-protection-bypass: $VERCEL_AUTOMATION_BYPASS_SECRET" \
  -H 'content-type: application/json' \
  -H 'accept: application/json, text/event-stream' \
  --data '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}'
```

Expected tools:

- `tools_list_providers`
- `tools_search_papers`
- `tools_get_paper_by_id`
- `tools_get_paper_metadata_by_id`
- `tools_get_paper_content_by_url`

Full Python MCP client smoke test:

```bash
/Users/jaylast/.codex/mcp/paperclip/.venv/bin/python - <<'PY'
import asyncio
import os
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

URL = "https://paperclip-vercel-eodr6v8gp-jlasters-projects.vercel.app/mcp/"
HEADERS = {
    "x-vercel-protection-bypass": os.environ["VERCEL_AUTOMATION_BYPASS_SECRET"],
}

async def main():
    async with streamablehttp_client(URL, headers=HEADERS) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            print([tool.name for tool in tools.tools])

            result = await session.call_tool(
                "tools_search_papers",
                {"query": "triple negative breast cancer", "provider": "arxiv"},
            )
            print("isError:", result.isError)
            print("blocks:", len(result.content))

asyncio.run(main())
PY
```

Expected result: all five tools are listed and the arXiv search returns
`isError: False`.

## Client Configuration

Cursor-style MCP configuration with protected preview access:

```json
{
  "mcpServers": {
    "paperclip-vercel": {
      "url": "https://paperclip-vercel-eodr6v8gp-jlasters-projects.vercel.app/mcp/",
      "headers": {
        "x-vercel-protection-bypass": "<VERCEL_AUTOMATION_BYPASS_SECRET>"
      }
    }
  }
}
```

Codex's `codex mcp add --url` path supports URL-based MCP servers and bearer
token env vars, but not arbitrary custom headers. For Codex, use an unprotected
Paperclip URL, a custom domain excluded from SSO protection, or a local proxy
that adds the Vercel bypass header.

```bash
codex mcp add paperclip-vercel \
  --url https://<public-paperclip-domain>/mcp/
```
