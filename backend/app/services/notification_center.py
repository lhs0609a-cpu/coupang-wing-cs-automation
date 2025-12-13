"""
Real-time Notification Center using WebSocket
"""
from typing import Dict, List, Optional, Set
from datetime import datetime
from pydantic import BaseModel
from loguru import logger
import json
import asyncio


class Notification(BaseModel):
    """Notification model"""
    id: str
    type: str  # info, success, warning, error, inquiry
    title: str
    message: str
    timestamp: str
    read: bool = False
    link: Optional[str] = None
    data: Optional[Dict] = None
    priority: str = "normal"  # low, normal, high, critical


class NotificationCenter:
    """
    Central notification manager with WebSocket support
    """

    def __init__(self):
        self.connections: Set = set()
        self.notifications: List[Notification] = []
        self.max_notifications = 100

    async def connect(self, websocket):
        """Register new WebSocket connection"""
        self.connections.add(websocket)
        logger.info(f"New WebSocket connection. Total: {len(self.connections)}")

        # Send recent notifications to new connection
        await self._send_recent_notifications(websocket)

    async def disconnect(self, websocket):
        """Remove WebSocket connection"""
        self.connections.discard(websocket)
        logger.info(f"WebSocket disconnected. Total: {len(self.connections)}")

    async def broadcast(self, notification: Notification):
        """
        Broadcast notification to all connected clients

        Args:
            notification: Notification object
        """
        # Store notification
        self.notifications.insert(0, notification)
        if len(self.notifications) > self.max_notifications:
            self.notifications = self.notifications[:self.max_notifications]

        # Broadcast to all connections
        message = notification.json()
        disconnected = set()

        for connection in self.connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error sending to WebSocket: {str(e)}")
                disconnected.add(connection)

        # Remove disconnected clients
        self.connections -= disconnected

        logger.debug(f"Broadcasted notification to {len(self.connections)} clients")

    async def send_inquiry_notification(
        self,
        inquiry_id: int,
        title: str,
        message: str,
        priority: str = "normal"
    ):
        """Send inquiry-related notification"""
        notification = Notification(
            id=f"inquiry_{inquiry_id}_{int(datetime.utcnow().timestamp())}",
            type="inquiry",
            title=title,
            message=message,
            timestamp=datetime.utcnow().isoformat(),
            link=f"/inquiries/{inquiry_id}",
            priority=priority
        )
        await self.broadcast(notification)

    async def send_success_notification(self, title: str, message: str):
        """Send success notification"""
        notification = Notification(
            id=f"success_{int(datetime.utcnow().timestamp())}",
            type="success",
            title=title,
            message=message,
            timestamp=datetime.utcnow().isoformat()
        )
        await self.broadcast(notification)

    async def send_warning_notification(self, title: str, message: str, link: str = None):
        """Send warning notification"""
        notification = Notification(
            id=f"warning_{int(datetime.utcnow().timestamp())}",
            type="warning",
            title=title,
            message=message,
            timestamp=datetime.utcnow().isoformat(),
            link=link,
            priority="high"
        )
        await self.broadcast(notification)

    async def send_error_notification(self, title: str, message: str):
        """Send error notification"""
        notification = Notification(
            id=f"error_{int(datetime.utcnow().timestamp())}",
            type="error",
            title=title,
            message=message,
            timestamp=datetime.utcnow().isoformat(),
            priority="critical"
        )
        await self.broadcast(notification)

    async def send_info_notification(self, title: str, message: str):
        """Send info notification"""
        notification = Notification(
            id=f"info_{int(datetime.utcnow().timestamp())}",
            type="info",
            title=title,
            message=message,
            timestamp=datetime.utcnow().isoformat()
        )
        await self.broadcast(notification)

    async def _send_recent_notifications(self, websocket):
        """Send recent notifications to newly connected client"""
        try:
            for notification in self.notifications[:20]:  # Send last 20
                await websocket.send_text(notification.json())
        except Exception as e:
            logger.error(f"Error sending recent notifications: {str(e)}")

    def get_unread_count(self) -> int:
        """Get count of unread notifications"""
        return sum(1 for n in self.notifications if not n.read)

    def mark_as_read(self, notification_id: str) -> bool:
        """Mark notification as read"""
        for notification in self.notifications:
            if notification.id == notification_id:
                notification.read = True
                return True
        return False

    def mark_all_as_read(self):
        """Mark all notifications as read"""
        for notification in self.notifications:
            notification.read = True

    def get_notifications(
        self,
        limit: int = 50,
        unread_only: bool = False,
        type_filter: Optional[str] = None
    ) -> List[Notification]:
        """
        Get notifications with filters

        Args:
            limit: Maximum notifications to return
            unread_only: Return only unread notifications
            type_filter: Filter by type

        Returns:
            List of notifications
        """
        notifications = self.notifications

        if unread_only:
            notifications = [n for n in notifications if not n.read]

        if type_filter:
            notifications = [n for n in notifications if n.type == type_filter]

        return notifications[:limit]

    def clear_old_notifications(self, days: int = 7):
        """Clear notifications older than specified days"""
        from datetime import timedelta

        cutoff = datetime.utcnow() - timedelta(days=days)
        self.notifications = [
            n for n in self.notifications
            if datetime.fromisoformat(n.timestamp) > cutoff
        ]


# Global notification center instance
notification_center = NotificationCenter()
