from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.service import Service
from app.models.user import User

# This is a bit tricky, as WebSocket dependencies don't have access to request scope
# We will need a custom dependency to get the user from a token passed in the query
async def get_current_user_from_query(token: str, db: Session = Depends(get_db)) -> User:
    # In a real app, this token would be a short-lived JWT, not a session cookie.
    # For now, we'll simulate this by trusting the user_id from the query.
    # This is INSECURE and for demonstration purposes only.
    # A proper implementation would involve generating a temporary auth token.
    from app.api.deps import get_current_user
    from starlette.requests import Request

    # Fake a request object to reuse the dependency
    fake_request = Request(scope={"type": "http", "session": {"user_id": int(token)}})
    return get_current_user(fake_request, db)


router = APIRouter()

@router.websocket("/ws/services/{service_id}/console")
async def websocket_console(
    websocket: WebSocket,
    service_id: int,
    token: str, # Token will be passed as a query parameter
    db: Session = Depends(get_db)
):
    try:
        user = await get_current_user_from_query(token, db)
        service = db.query(Service).filter(Service.id == service_id, Service.owner_id == user.id).first()

        if not service:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        if not service.docker_container_id:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Service is not a Docker container")
            return

        await websocket.accept()
        await websocket.send_text("Connection established. Attaching to console...")

        # Attach to the container's log stream and stdin
        from app.core.docker_manager import get_docker_client
        import asyncio

        d_client = get_docker_client()
        container = d_client.containers.get(service.docker_container_id)

        async def stream_logs():
            try:
                for line in container.logs(stream=True, follow=True):
                    await websocket.send_text(line.decode('utf-8'))
            except WebSocketDisconnect:
                pass # Client disconnected, stop streaming

        async def receive_commands():
            try:
                while True:
                    data = await websocket.receive_text()
                    # Attaching to stdin is more complex and requires `attach_socket`
                    # For now, we'll just log the command
                    print(f"Command received for {service.id}: {data}")
            except WebSocketDisconnect:
                pass # Client disconnected

        log_task = asyncio.create_task(stream_logs())
        cmd_task = asyncio.create_task(receive_commands())

        await asyncio.gather(log_task, cmd_task)

    except WebSocketDisconnect:
        print(f"Client for service {service_id} disconnected")
    except Exception as e:
        print(f"An error occurred: {e}")
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)