"""
Webhook Integration System
"""
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from loguru import logger
import httpx
import asyncio
import hashlib
import hmac
import json

from ..models import Inquiry, Response


class WebhookManager:
    """
    Webhook management and delivery system
    """

    def __init__(self, db: Session):
        self.db = db
        self.webhooks = {}  # In-memory webhook registry
        self.delivery_queue = []
        self.retry_config = {
            'max_retries': 3,
            'retry_delays': [1, 5, 15]  # seconds
        }

    def register_webhook(
        self,
        name: str,
        url: str,
        events: List[str],
        secret: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        active: bool = True
    ) -> Dict:
        """
        Register a new webhook

        Args:
            name: Webhook name
            url: Webhook URL
            events: List of event types to subscribe to
            secret: Secret key for signature verification
            headers: Custom headers
            active: Whether webhook is active

        Returns:
            Webhook configuration
        """
        webhook_id = f"webhook_{int(datetime.utcnow().timestamp())}"

        webhook_config = {
            'id': webhook_id,
            'name': name,
            'url': url,
            'events': events,
            'secret': secret,
            'headers': headers or {},
            'active': active,
            'created_at': datetime.utcnow(),
            'stats': {
                'total_deliveries': 0,
                'successful_deliveries': 0,
                'failed_deliveries': 0,
                'last_delivery_at': None,
                'last_delivery_status': None
            }
        }

        self.webhooks[webhook_id] = webhook_config

        logger.info(f"Registered webhook: {name} ({webhook_id}) for events: {events}")
        return webhook_config

    async def trigger_webhook(
        self,
        event_type: str,
        payload: Dict
    ):
        """
        Trigger webhooks for a specific event

        Args:
            event_type: Event type (e.g., 'inquiry.created', 'response.approved')
            payload: Event data
        """
        # Find webhooks subscribed to this event
        matching_webhooks = [
            webhook for webhook in self.webhooks.values()
            if webhook['active'] and event_type in webhook['events']
        ]

        if not matching_webhooks:
            logger.debug(f"No webhooks registered for event: {event_type}")
            return

        logger.info(f"Triggering {len(matching_webhooks)} webhooks for event: {event_type}")

        # Deliver to each webhook
        tasks = []
        for webhook in matching_webhooks:
            task = self._deliver_webhook(webhook, event_type, payload)
            tasks.append(task)

        # Execute all deliveries concurrently
        await asyncio.gather(*tasks, return_exceptions=True)

    async def _deliver_webhook(
        self,
        webhook: Dict,
        event_type: str,
        payload: Dict
    ):
        """
        Deliver webhook to a single endpoint with retry logic

        Args:
            webhook: Webhook configuration
            event_type: Event type
            payload: Event data
        """
        webhook_id = webhook['id']
        url = webhook['url']

        # Prepare webhook payload
        webhook_payload = {
            'event': event_type,
            'timestamp': datetime.utcnow().isoformat(),
            'webhook_id': webhook_id,
            'data': payload
        }

        # Generate signature if secret is configured
        signature = None
        if webhook['secret']:
            signature = self._generate_signature(
                webhook['secret'],
                json.dumps(webhook_payload)
            )

        # Prepare headers
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'CoupangWing-Webhook/1.0',
            'X-Webhook-Event': event_type,
            'X-Webhook-ID': webhook_id,
            **webhook['headers']
        }

        if signature:
            headers['X-Webhook-Signature'] = signature

        # Attempt delivery with retries
        webhook['stats']['total_deliveries'] += 1

        for attempt in range(self.retry_config['max_retries']):
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.post(
                        url,
                        json=webhook_payload,
                        headers=headers
                    )

                    if response.status_code in [200, 201, 202, 204]:
                        # Success
                        webhook['stats']['successful_deliveries'] += 1
                        webhook['stats']['last_delivery_at'] = datetime.utcnow()
                        webhook['stats']['last_delivery_status'] = 'success'

                        logger.info(
                            f"Webhook delivered successfully: {webhook_id} "
                            f"(event: {event_type}, status: {response.status_code})"
                        )
                        return

                    else:
                        # Non-2xx status code
                        logger.warning(
                            f"Webhook delivery failed: {webhook_id} "
                            f"(attempt {attempt + 1}, status: {response.status_code})"
                        )

            except Exception as e:
                logger.error(
                    f"Webhook delivery error: {webhook_id} "
                    f"(attempt {attempt + 1}, error: {str(e)})"
                )

            # Wait before retry (if not last attempt)
            if attempt < self.retry_config['max_retries'] - 1:
                delay = self.retry_config['retry_delays'][attempt]
                await asyncio.sleep(delay)

        # All retries failed
        webhook['stats']['failed_deliveries'] += 1
        webhook['stats']['last_delivery_at'] = datetime.utcnow()
        webhook['stats']['last_delivery_status'] = 'failed'

        logger.error(f"Webhook delivery failed after all retries: {webhook_id}")

    def _generate_signature(self, secret: str, payload: str) -> str:
        """
        Generate HMAC signature for webhook verification

        Args:
            secret: Secret key
            payload: JSON payload as string

        Returns:
            HMAC signature
        """
        signature = hmac.new(
            secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        return f"sha256={signature}"

    def get_webhook(self, webhook_id: str) -> Optional[Dict]:
        """Get webhook configuration"""
        return self.webhooks.get(webhook_id)

    def list_webhooks(self) -> List[Dict]:
        """List all registered webhooks"""
        return [
            {
                'id': webhook['id'],
                'name': webhook['name'],
                'url': webhook['url'],
                'events': webhook['events'],
                'active': webhook['active'],
                'created_at': webhook['created_at'].isoformat(),
                'stats': webhook['stats']
            }
            for webhook in self.webhooks.values()
        ]

    def update_webhook(
        self,
        webhook_id: str,
        updates: Dict
    ) -> Dict:
        """
        Update webhook configuration

        Args:
            webhook_id: Webhook ID
            updates: Fields to update

        Returns:
            Updated webhook configuration
        """
        if webhook_id not in self.webhooks:
            raise ValueError(f"Webhook {webhook_id} not found")

        webhook = self.webhooks[webhook_id]

        # Update allowed fields
        allowed_fields = ['name', 'url', 'events', 'secret', 'headers', 'active']
        for field in allowed_fields:
            if field in updates:
                webhook[field] = updates[field]

        webhook['updated_at'] = datetime.utcnow()

        logger.info(f"Updated webhook: {webhook_id}")
        return webhook

    def delete_webhook(self, webhook_id: str):
        """Delete a webhook"""
        if webhook_id not in self.webhooks:
            raise ValueError(f"Webhook {webhook_id} not found")

        del self.webhooks[webhook_id]
        logger.info(f"Deleted webhook: {webhook_id}")

    def get_webhook_stats(self, webhook_id: str) -> Dict:
        """Get delivery statistics for a webhook"""
        if webhook_id not in self.webhooks:
            raise ValueError(f"Webhook {webhook_id} not found")

        webhook = self.webhooks[webhook_id]
        stats = webhook['stats']

        success_rate = 0
        if stats['total_deliveries'] > 0:
            success_rate = stats['successful_deliveries'] / stats['total_deliveries']

        return {
            'webhook_id': webhook_id,
            'webhook_name': webhook['name'],
            'total_deliveries': stats['total_deliveries'],
            'successful_deliveries': stats['successful_deliveries'],
            'failed_deliveries': stats['failed_deliveries'],
            'success_rate': round(success_rate, 4),
            'last_delivery_at': stats['last_delivery_at'].isoformat() if stats['last_delivery_at'] else None,
            'last_delivery_status': stats['last_delivery_status']
        }

    async def test_webhook(self, webhook_id: str) -> Dict:
        """
        Send a test event to a webhook

        Args:
            webhook_id: Webhook ID

        Returns:
            Test result
        """
        if webhook_id not in self.webhooks:
            raise ValueError(f"Webhook {webhook_id} not found")

        webhook = self.webhooks[webhook_id]

        test_payload = {
            'test': True,
            'message': 'This is a test webhook delivery',
            'timestamp': datetime.utcnow().isoformat()
        }

        try:
            await self._deliver_webhook(webhook, 'webhook.test', test_payload)

            return {
                'success': True,
                'message': 'Test webhook delivered successfully',
                'webhook_id': webhook_id
            }

        except Exception as e:
            return {
                'success': False,
                'message': f'Test webhook failed: {str(e)}',
                'webhook_id': webhook_id
            }


# Event helper functions
async def trigger_inquiry_created(db: Session, inquiry: Inquiry):
    """Trigger webhook for inquiry created event"""
    webhook_manager = WebhookManager(db)

    payload = {
        'inquiry_id': inquiry.id,
        'customer_id': inquiry.customer_id,
        'customer_name': inquiry.customer_name,
        'category': inquiry.classified_category,
        'risk_level': inquiry.risk_level,
        'is_urgent': inquiry.is_urgent,
        'sentiment': inquiry.sentiment,
        'created_at': inquiry.created_at.isoformat()
    }

    await webhook_manager.trigger_webhook('inquiry.created', payload)


async def trigger_response_approved(db: Session, response: Response):
    """Trigger webhook for response approved event"""
    webhook_manager = WebhookManager(db)

    payload = {
        'response_id': response.id,
        'inquiry_id': response.inquiry_id,
        'approved_by': response.approved_by,
        'confidence_score': response.confidence_score,
        'approved_at': response.approved_at.isoformat() if response.approved_at else None
    }

    await webhook_manager.trigger_webhook('response.approved', payload)


async def trigger_high_risk_detected(db: Session, inquiry: Inquiry):
    """Trigger webhook for high risk inquiry detected"""
    webhook_manager = WebhookManager(db)

    payload = {
        'inquiry_id': inquiry.id,
        'customer_id': inquiry.customer_id,
        'risk_level': inquiry.risk_level,
        'category': inquiry.classified_category,
        'requires_human': inquiry.requires_human,
        'created_at': inquiry.created_at.isoformat()
    }

    await webhook_manager.trigger_webhook('inquiry.high_risk', payload)
