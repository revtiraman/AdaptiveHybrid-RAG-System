"""WebSocket endpoint for streaming query responses."""

from __future__ import annotations

import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from .routes.query import QueryBody

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/query")
async def ws_query(websocket: WebSocket):
	await websocket.accept()
	try:
		while True:
			payload = await websocket.receive_text()
			data = json.loads(payload)
			if data.get("type") == "cancel":
				await websocket.send_json({"type": "status", "message": "cancelled"})
				continue
			body = QueryBody.model_validate(data)
			await websocket.send_json({"type": "status", "message": "retrieving"})
			await websocket.send_json({"type": "chunk", "text": body.query})
			await websocket.send_json({"type": "complete", "response": {"query": body.query}})
	except WebSocketDisconnect:
		return


__all__ = ["router"]
