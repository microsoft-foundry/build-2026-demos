import os
import uuid
import json
import logging
from typing import AsyncGenerator

import httpx
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logging.getLogger("fibey").setLevel(logging.INFO)

logger = logging.getLogger(__name__)

app = FastAPI(title="Fibey Agent Gateway")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory session store
sessions: dict[str, dict] = {}

AGENT_MODE = os.getenv("AGENT_MODE", "local")

# Hosted agent config
HOSTED_AGENT_ENDPOINT = os.getenv("HOSTED_AGENT_ENDPOINT", "")
HOSTED_AGENT_NAME = os.getenv("HOSTED_AGENT_NAME", "fibey-agent")

# Container App agent service config
CONTAINERAPP_AGENT_URL = os.getenv("CONTAINERAPP_AGENT_URL", "")

# Session-to-agent-session mapping for hosted mode conversation continuity
_hosted_sessions: dict[str, str] = {}


def _sse(event: str, data: dict | str) -> str:
    """Format a server-sent event."""
    payload = json.dumps(data) if isinstance(data, dict) else data
    return f"event: {event}\ndata: {payload}\n\n"


async def _run_local(message: str, session_id: str) -> AsyncGenerator[str, None]:
    """Run the agent locally and stream SSE events."""
    from fibey.agent.agent import run_agent

    session = sessions.setdefault(session_id, {})

    try:
        async for event in run_agent(message, session):
            if event["type"] == "delta":
                yield _sse("delta", {"content": event["content"]})
            elif event["type"] == "activity":
                yield _sse("activity", {
                    "tool": event.get("tool", ""),
                    "call_id": event.get("call_id", ""),
                    "status": event.get("status", ""),
                    "detail": event.get("detail", ""),
                    "args": event.get("args", ""),
                    "result": event.get("result", ""),
                    "results": event.get("results", []),
                })
            elif event["type"] == "citation":
                yield _sse("citation", {
                    "source": event.get("source", ""),
                    "url": event.get("url", ""),
                })
    except Exception as e:
        logger.exception("Agent error")
        yield _sse("error", {"message": str(e)})

    yield _sse("done", "[DONE]")


def _get_hosted_token() -> str:
    """Get a bearer token for the Foundry hosted agent endpoint."""
    from azure.identity import (
        ChainedTokenCredential,
        ManagedIdentityCredential,
        AzureDeveloperCliCredential,
    )
    cred = ChainedTokenCredential(
        ManagedIdentityCredential(),
        AzureDeveloperCliCredential(
            tenant_id=os.getenv("AZURE_TENANT_ID"), process_timeout=30
        ),
    )
    return cred.get_token("https://ai.azure.com/.default").token


async def _run_hosted(message: str, session_id: str) -> AsyncGenerator[str, None]:
    """Proxy to the Foundry-hosted agent and translate Responses API streaming
    into the gateway SSE format expected by the UI."""
    endpoint = HOSTED_AGENT_ENDPOINT
    if not endpoint:
        yield _sse("error", {"message": "HOSTED_AGENT_ENDPOINT not configured"})
        yield _sse("done", "[DONE]")
        return

    try:
        token = _get_hosted_token()
    except Exception as exc:
        yield _sse("error", {"message": f"Auth failed: {exc}"})
        yield _sse("done", "[DONE]")
        return

    url = (
        f"{endpoint.rstrip('/')}/agents/{HOSTED_AGENT_NAME}/endpoint"
        f"/protocols/openai/responses?api-version=2025-11-15-preview"
    )

    body: dict = {"input": message, "stream": True}

    # Attach agent_session_id for conversation continuity
    agent_session_id = _hosted_sessions.get(session_id)
    if agent_session_id:
        body["previous_response_id"] = agent_session_id

    seen_call_ids: set[str] = set()

    debug_events = os.getenv("HOSTED_DEBUG_EVENTS", "0") == "1"
    timeout_s = float(os.getenv("HOSTED_TIMEOUT_SECONDS", "600"))

    try:
        async with httpx.AsyncClient(timeout=timeout_s) as client:
            async with client.stream(
                "POST",
                url,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                content=json.dumps(body),
            ) as resp:
                if resp.status_code != 200:
                    error_body = await resp.aread()
                    logger.error("Hosted agent %s: %s", resp.status_code, error_body.decode()[:500])
                    yield _sse("error", {"message": f"Hosted agent error {resp.status_code}: {error_body.decode()[:300]}"})
                    yield _sse("done", "[DONE]")
                    return

                buffer = ""
                stream_done = False
                async for chunk in resp.aiter_text():
                    if stream_done:
                        break
                    buffer += chunk
                    while "\n" in buffer:
                        line, buffer = buffer.split("\n", 1)
                        line = line.strip()

                        if not line.startswith("data: "):
                            continue

                        raw = line[6:]
                        if raw == "[DONE]":
                            stream_done = True
                            break

                        try:
                            event = json.loads(raw)
                        except json.JSONDecodeError:
                            continue

                        event_type = event.get("type", "")

                        if debug_events:
                            logger.info("HOSTED_EVT %s keys=%s", event_type, list(event.keys()))

                        # Text deltas
                        if event_type == "response.output_text.delta":
                            delta = event.get("delta", "")
                            if delta:
                                yield _sse("delta", {"content": delta})

                        # MCP / function call started (item added)
                        elif event_type == "response.output_item.added":
                            item = event.get("item", {})
                            item_type = item.get("type", "")
                            call_id = item.get("call_id", "") or item.get("id", "")

                            if item_type in ("mcp_call", "function_call") and call_id not in seen_call_ids:
                                seen_call_ids.add(call_id)
                                tool_name = item.get("name", "tool")
                                args = item.get("arguments", "")
                                yield _sse("activity", {
                                    "tool": tool_name,
                                    "call_id": call_id,
                                    "status": "running",
                                    "detail": f"Calling {tool_name}",
                                    "args": args,
                                    "result": "",
                                })

                        # MCP / function call finished (item done) — output is embedded in the item
                        elif event_type == "response.output_item.done":
                            item = event.get("item", {})
                            item_type = item.get("type", "")
                            call_id = item.get("call_id", "") or item.get("id", "")

                            if item_type == "mcp_call":
                                # MCP call output is on the mcp_call item itself
                                output = item.get("output", "") or item.get("result", "")
                                error = item.get("error")
                                if error:
                                    yield _sse("activity", {
                                        "tool": item.get("name", ""),
                                        "call_id": call_id,
                                        "status": "error",
                                        "detail": f"Error: {error}"[:200],
                                        "args": "",
                                        "result": str(error)[:2000],
                                    })
                                else:
                                    out_str = output if isinstance(output, str) else json.dumps(output)
                                    yield _sse("activity", {
                                        "tool": item.get("name", ""),
                                        "call_id": call_id,
                                        "status": "complete",
                                        "detail": "Done",
                                        "args": item.get("arguments", ""),
                                        "result": out_str[:2000],
                                    })
                            elif item_type in ("mcp_call_output", "function_call_output"):
                                output = item.get("output", "")
                                yield _sse("activity", {
                                    "tool": "",
                                    "call_id": call_id,
                                    "status": "complete",
                                    "detail": "Done",
                                    "args": "",
                                    "result": output[:2000] if isinstance(output, str) else json.dumps(output)[:2000],
                                })

                        # Dedicated MCP-call lifecycle events (newer Responses API)
                        elif event_type in ("response.mcp_call.completed", "response.mcp_call_completed"):
                            call_id = event.get("call_id", "") or event.get("item_id", "")
                            output = event.get("output", "") or event.get("result", "")
                            out_str = output if isinstance(output, str) else json.dumps(output)
                            yield _sse("activity", {
                                "tool": event.get("name", ""),
                                "call_id": call_id,
                                "status": "complete",
                                "detail": "Done",
                                "args": "",
                                "result": out_str[:2000],
                            })
                        elif event_type in ("response.mcp_call.failed", "response.mcp_call_failed"):
                            call_id = event.get("call_id", "") or event.get("item_id", "")
                            err = event.get("error", "MCP call failed")
                            yield _sse("activity", {
                                "tool": event.get("name", ""),
                                "call_id": call_id,
                                "status": "error",
                                "detail": str(err)[:200],
                                "args": "",
                                "result": str(err)[:2000],
                            })

                        # Capture agent_session_id and response_id for continuity
                        elif event_type == "response.completed":
                            response_obj = event.get("response", {})
                            resp_id = response_obj.get("id", "")
                            if resp_id:
                                _hosted_sessions[session_id] = resp_id

                        # Surface errors at the response level
                        elif event_type in ("response.failed", "error"):
                            err = event.get("error") or event.get("message") or event
                            logger.error("Hosted agent response error: %s", err)
                            yield _sse("error", {"message": f"Agent error: {str(err)[:300]}"})

    except httpx.TimeoutException:
        yield _sse("error", {"message": "Hosted agent request timed out"})
    except Exception as exc:
        logger.exception("Hosted agent proxy error")
        yield _sse("error", {"message": f"Proxy error: {exc}"})

    yield _sse("done", "[DONE]")


async def _run_containerapp(message: str, session_id: str) -> AsyncGenerator[str, None]:
    """Proxy to the Container App agent service and relay SSE events."""
    agent_url = CONTAINERAPP_AGENT_URL
    if not agent_url:
        yield _sse("error", {"message": "CONTAINERAPP_AGENT_URL not configured"})
        yield _sse("done", "[DONE]")
        return
    
    url = f"{agent_url.rstrip('/')}/api/chat"
    body = {"message": message, "session_id": session_id}
    
    try:
        async with httpx.AsyncClient(timeout=600.0) as client:
            async with client.stream(
                "POST", url,
                json=body,
                headers={"Content-Type": "application/json"},
            ) as resp:
                if resp.status_code != 200:
                    error_body = await resp.aread()
                    logger.error("Agent service %s: %s", resp.status_code, error_body.decode()[:500])
                    yield _sse("error", {"message": f"Agent service error {resp.status_code}: {error_body.decode()[:300]}"})
                    yield _sse("done", "[DONE]")
                    return
                
                # Relay SSE events from agent service to client
                async for line in resp.aiter_lines():
                    if line:
                        yield line + "\n"
    
    except httpx.TimeoutException:
        yield _sse("error", {"message": "Agent service request timed out"})
    except Exception as exc:
        logger.exception("Container app agent proxy error")
        yield _sse("error", {"message": f"Proxy error: {exc}"})
    
    yield _sse("done", "[DONE]")


@app.post("/api/chat")
async def chat(request: Request):
    body = await request.json()
    message = body.get("message", "")
    session_id = body.get("session_id", str(uuid.uuid4()))

    logger.info("Gateway mode: %s, message: %s, session: %s", AGENT_MODE, message[:50], session_id)
    
    if AGENT_MODE == "hosted":
        logger.info("Using hosted agent mode")
        generator = _run_hosted(message, session_id)
    elif AGENT_MODE == "containerapp":
        logger.info("Using containerapp mode, URL: %s", CONTAINERAPP_AGENT_URL)
        generator = _run_containerapp(message, session_id)
    else:
        logger.info("Using local agent mode")
        generator = _run_local(message, session_id)

    return StreamingResponse(
        generator,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Session-Id": session_id,
        },
    )


@app.post("/api/sessions/reset")
async def reset_session(request: Request):
    body = await request.json()
    session_id = body.get("session_id", "")
    sessions.pop(session_id, None)
    return {"status": "ok"}


@app.get("/api/health")
async def health():
    return {"status": "healthy", "mode": AGENT_MODE}
