"""
WebSocket Router for Real-time Notifications
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from loguru import logger

from ..services.notification_center import notification_center

router = APIRouter(tags=["WebSocket"])


@router.websocket("/ws/notifications")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time notifications

    Clients connect here to receive real-time updates about:
    - New inquiries
    - Response status changes
    - System alerts
    - Automation events
    """
    await websocket.accept()
    await notification_center.connect(websocket)

    try:
        # Keep connection alive and listen for client messages
        while True:
            data = await websocket.receive_text()

            # Handle client messages (e.g., mark as read)
            import json
            try:
                message = json.loads(data)

                if message.get('action') == 'mark_read':
                    notification_id = message.get('notification_id')
                    notification_center.mark_as_read(notification_id)

                elif message.get('action') == 'mark_all_read':
                    notification_center.mark_all_as_read()

            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON from WebSocket: {data}")

    except WebSocketDisconnect:
        await notification_center.disconnect(websocket)
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        await notification_center.disconnect(websocket)


@router.get("/notifications")
async def get_notifications(
    limit: int = 50,
    unread_only: bool = False,
    type: str = None
):
    """
    Get notification history

    Args:
        limit: Maximum notifications to return
        unread_only: Return only unread notifications
        type: Filter by notification type

    Returns:
        List of notifications
    """
    notifications = notification_center.get_notifications(
        limit=limit,
        unread_only=unread_only,
        type_filter=type
    )

    return {
        "notifications": [n.dict() for n in notifications],
        "unread_count": notification_center.get_unread_count(),
        "total": len(notifications)
    }


@router.post("/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: str):
    """Mark a notification as read"""
    success = notification_center.mark_as_read(notification_id)
    return {"success": success}


@router.post("/notifications/read-all")
async def mark_all_read():
    """Mark all notifications as read"""
    notification_center.mark_all_as_read()
    return {"success": True, "message": "All notifications marked as read"}


@router.get("/notifications/unread-count")
async def get_unread_count():
    """Get count of unread notifications"""
    return {"unread_count": notification_center.get_unread_count()}
