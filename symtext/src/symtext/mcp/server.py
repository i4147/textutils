from __future__ import annotations

import asyncio
import contextlib
import json
import sys
from collections.abc import Callable
from typing import Any

from loguru import logger

from symtext.mcp.handlers import _TOOLS
from symtext.mcp.state import ServerContext, ServerState
from symtext.mcp.tools_schema import _DEFAULT_LIMIT, TOOLS

__all__ = ["MCP_PROTOCOL_VERSION", "TOOLS", "_DEFAULT_LIMIT", "_dispatch", "serve"]

MCP_PROTOCOL_VERSION = "2025-03-26"


PromotionHook = Callable[[], None]


async def serve(
    db: Any,
    watcher: Any | None = None,
    *,
    ctx: ServerContext | None = None,
    promotion_hook: PromotionHook | None = None,
    swap_lock: asyncio.Lock | None = None,
) -> None:
    logger.info("MCP server starting (protocol {})", MCP_PROTOCOL_VERSION)

    tasks: list[asyncio.Task[None]] = []
    if watcher is not None:
        tasks.append(asyncio.create_task(watcher()))

    reader = asyncio.StreamReader()
    protocol = asyncio.StreamReaderProtocol(reader)
    await asyncio.get_running_loop().connect_read_pipe(lambda: protocol, sys.stdin)

    try:
        while True:
            line = await reader.readline()
            if not line:
                break
            line_str = line.decode("utf-8", errors="replace").strip()
            if not line_str:
                continue

            try:
                request = json.loads(line_str)
            except json.JSONDecodeError:
                _write_response(_make_error(None, -32700, "Parse error"))
                continue

            req_id = request.get("id")
            method = request.get("method", "")

            if method == "initialize":
                _write_response(_make_response(req_id, _initialize_result(db, ctx)))
            elif method == "notifications/initialized":
                pass
            elif method == "tools/list":
                _write_response(_make_response(req_id, {"tools": TOOLS}))
            elif method == "tools/call":
                if promotion_hook is not None:
                    promotion_hook()
                params = request.get("params", {})
                tool_name = params.get("name", "")
                arguments = params.get("arguments", {})
                if swap_lock is not None:
                    async with swap_lock:
                        result = _dispatch(db, tool_name, arguments, ctx=ctx)
                else:
                    result = _dispatch(db, tool_name, arguments, ctx=ctx)
                _write_response(_make_response(req_id, result))
            else:
                _write_response(_make_error(req_id, -32601, f"Unknown method: {method}"))
    finally:
        for t in tasks:
            t.cancel()
        for t in tasks:
            with contextlib.suppress(asyncio.CancelledError):
                await t


def _initialize_result(db: Any, ctx: ServerContext | None) -> dict[str, Any]:
    if ctx is not None and ctx.state is ServerState.ERROR:
        instructions = (
            f"symtext is inactive in this directory: {ctx.error_message}. "
            "Tool calls will return errors until the session restarts in a "
            "valid project directory."
        )
    elif ctx is not None and not ctx.is_ready():
        instructions = ctx.busy_message()
    else:
        try:
            stats = db.stats()
            instructions = (
                f"symtext — pre-indexed code graph for this project "
                f"({stats['total_nodes']} symbols, "
                f"{stats['total_edges']} relationships, "
                f"{stats['nodes'].get('File', 0)} files). "
                f"Use these tools INSTEAD of Grep/Glob for: "
                f"finding callers/callees, tracing imports, "
                f"class hierarchies. Start with shape() or summarize()."
            )
        except Exception as exc:
            logger.warning("stats() failed during initialize: {}", exc)
            instructions = "symtext — code graph (stats unavailable)."

    return {
        "protocolVersion": MCP_PROTOCOL_VERSION,
        "capabilities": {"tools": {}},
        "serverInfo": {"name": "symtext", "version": "0.1.0"},
        "instructions": instructions,
    }


_MAY_WRITE = frozenset({"describe_symbol"})


def _dispatch(
    db: Any,
    tool_name: str,
    args: dict[str, Any],
    *,
    ctx: ServerContext | None = None,
) -> dict[str, Any]:
    if ctx is not None:
        if ctx.state is ServerState.ERROR:
            return _structured_error(
                f"symtext is inactive in this directory: {ctx.error_message}",
                state=ctx.snapshot(),
            )
        if not ctx.is_ready():
            return _structured_busy(ctx)

    tool = _TOOLS.get(tool_name)
    if tool is None:
        available = ", ".join(sorted(_TOOLS))
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Unknown tool '{tool_name}'. Available tools: {available}",
                }
            ],
            "isError": True,
        }
    try:
        if tool_name in _MAY_WRITE:
            result = tool.handler(db, args)
        else:
            with db.read_transaction():
                result = tool.handler(db, args)
    except Exception as exc:
        logger.opt(exception=True).error("Tool {} failed: {}", tool_name, exc)
        recovery = tool.recovery_hint
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Error executing {tool_name}: {exc}. {recovery}",
                }
            ],
            "isError": True,
        }
    if isinstance(result, dict) and "isError" in result:
        return result
    return {
        "content": [{"type": "text", "text": json.dumps(result, default=str)}],
    }


def _structured_busy(ctx: ServerContext) -> dict[str, Any]:
    snap = ctx.snapshot()
    payload = {"status": snap["state"], "progress": snap, "message": ctx.busy_message()}
    return {
        "content": [{"type": "text", "text": json.dumps(payload)}],
        "isError": True,
    }


def _structured_error(message: str, *, state: dict[str, Any]) -> dict[str, Any]:
    payload = {"status": state["state"], "message": message, "state": state}
    return {
        "content": [{"type": "text", "text": json.dumps(payload)}],
        "isError": True,
    }


def _write_response(response_str: str) -> None:
    sys.stdout.write(response_str + "\n")
    sys.stdout.flush()


def _make_response(req_id: Any, result: Any) -> str:
    return json.dumps({"jsonrpc": "2.0", "id": req_id, "result": result})


def _make_error(req_id: Any, code: int, message: str) -> str:
    return json.dumps({"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}})
