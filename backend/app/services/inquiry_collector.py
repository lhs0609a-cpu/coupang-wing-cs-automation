"""
Inquiry Collector Service
Collects and processes customer inquiries from Coupang Wing
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from loguru import logger

from ..models import Inquiry, ActivityLog
from .coupang_api import CoupangAPIClient


class InquiryCollector:
    """
    Collects customer inquiries from Coupang Wing API
    """

    def __init__(self, db: Session, api_client: CoupangAPIClient = None):
        self.db = db
        self.api_client = api_client or CoupangAPIClient()

    def collect_new_inquiries(
        self,
        inquiry_type: str = "online",
        status_filter: Optional[str] = None
    ) -> List[Inquiry]:
        """
        Collect new inquiries from Coupang Wing

        Args:
            inquiry_type: Type of inquiries to collect ('online' or 'callcenter')
            status_filter: Filter by status (e.g., 'WAITING' for unanswered)

        Returns:
            List of newly collected Inquiry objects
        """
        logger.info(f"Starting inquiry collection: type={inquiry_type}, status={status_filter}")

        try:
            # Fetch inquiries from API
            if inquiry_type == "online":
                response = self.api_client.get_online_inquiries(
                    status=status_filter or "WAITING",
                    answered_type="NOANSWER"  # Get unanswered inquiries
                )
            else:
                response = self.api_client.get_call_center_inquiries(
                    partner_counseling_status="NO_ANSWER"  # Get unanswered inquiries
                )

            # Parse response and save to database
            inquiries = self._parse_and_save_inquiries(response, inquiry_type)

            logger.success(f"Collected {len(inquiries)} new inquiries")
            return inquiries

        except Exception as e:
            logger.error(f"Error collecting inquiries: {str(e)}")
            self._log_activity("inquiry_collection_failed", error_message=str(e))
            raise

    def _parse_and_save_inquiries(
        self,
        api_response: Dict[str, Any],
        inquiry_type: str
    ) -> List[Inquiry]:
        """
        Parse API response and save inquiries to database

        Args:
            api_response: Response from Coupang API
            inquiry_type: Type of inquiry

        Returns:
            List of Inquiry objects
        """
        inquiries = []

        # Extract inquiry data from response
        # Note: Actual structure depends on Coupang API response format
        inquiry_data_list = api_response.get("data", [])
        if isinstance(inquiry_data_list, dict):
            inquiry_data_list = inquiry_data_list.get("inquiries", [])

        for data in inquiry_data_list:
            try:
                # Check if inquiry already exists
                coupang_id = str(data.get("inquiryId") or data.get("id"))
                existing = self.db.query(Inquiry).filter(
                    Inquiry.coupang_inquiry_id == coupang_id
                ).first()

                if existing:
                    logger.debug(f"Inquiry {coupang_id} already exists, skipping")
                    continue

                # Create new inquiry
                inquiry = self._create_inquiry_from_data(data, inquiry_type)
                self.db.add(inquiry)
                self.db.commit()
                self.db.refresh(inquiry)

                inquiries.append(inquiry)

                # Log activity
                self._log_activity(
                    action="inquiry_collected",
                    inquiry_id=inquiry.id,
                    details={"coupang_inquiry_id": coupang_id, "type": inquiry_type}
                )

                logger.info(f"Saved new inquiry: {coupang_id}")

            except Exception as e:
                logger.error(f"Error parsing inquiry: {str(e)}")
                self.db.rollback()
                continue

        return inquiries

    def _create_inquiry_from_data(self, data: Dict[str, Any], inquiry_type: str) -> Inquiry:
        """
        Create Inquiry object from API data

        Args:
            data: Inquiry data from API
            inquiry_type: Type of inquiry

        Returns:
            Inquiry object
        """
        inquiry = Inquiry(
            coupang_inquiry_id=str(data.get("inquiryId") or data.get("id")),
            vendor_id=data.get("vendorId", ""),

            # Customer info
            customer_name=data.get("customerName") or data.get("userName", ""),
            customer_id=data.get("customerId") or data.get("userId", ""),

            # Order info
            order_number=data.get("orderNumber") or data.get("orderId", ""),
            product_id=str(data.get("productId", "")),
            product_name=data.get("productName", ""),

            # Inquiry content
            inquiry_text=data.get("inquiryContent") or data.get("content", ""),
            inquiry_category=data.get("category") or data.get("inquiryType", ""),
            inquiry_subcategory=data.get("subcategory", ""),

            # Dates
            inquiry_date=self._parse_date(data.get("inquiryDate") or data.get("createdAt")),

            # Status
            status="pending"
        )

        return inquiry

    def _parse_date(self, date_str: Any) -> datetime:
        """
        Parse date string to datetime object

        Args:
            date_str: Date string from API

        Returns:
            datetime object
        """
        if isinstance(date_str, datetime):
            return date_str

        if not date_str:
            return datetime.utcnow()

        # Try common date formats
        formats = [
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
            "%Y/%m/%d %H:%M:%S"
        ]

        for fmt in formats:
            try:
                return datetime.strptime(str(date_str)[:19], fmt)
            except:
                continue

        logger.warning(f"Could not parse date: {date_str}, using current time")
        return datetime.utcnow()

    def get_pending_inquiries(self, limit: int = 50) -> List[Inquiry]:
        """
        Get pending inquiries that need processing

        Args:
            limit: Maximum number of inquiries to return

        Returns:
            List of pending Inquiry objects
        """
        return self.db.query(Inquiry).filter(
            Inquiry.status == "pending"
        ).order_by(
            Inquiry.is_urgent.desc(),
            Inquiry.inquiry_date.asc()
        ).limit(limit).all()

    def mark_inquiry_as_processing(self, inquiry_id: int):
        """
        Mark inquiry as being processed

        Args:
            inquiry_id: Inquiry ID
        """
        inquiry = self.db.query(Inquiry).filter(Inquiry.id == inquiry_id).first()
        if inquiry:
            inquiry.status = "processing"
            inquiry.updated_at = datetime.utcnow()
            self.db.commit()

            self._log_activity(
                action="inquiry_processing_started",
                inquiry_id=inquiry_id
            )

    def mark_inquiry_as_processed(self, inquiry_id: int):
        """
        Mark inquiry as processed

        Args:
            inquiry_id: Inquiry ID
        """
        inquiry = self.db.query(Inquiry).filter(Inquiry.id == inquiry_id).first()
        if inquiry:
            inquiry.status = "processed"
            inquiry.updated_at = datetime.utcnow()
            self.db.commit()

            self._log_activity(
                action="inquiry_processed",
                inquiry_id=inquiry_id
            )

    def mark_inquiry_as_failed(self, inquiry_id: int, error_message: str = ""):
        """
        Mark inquiry as failed

        Args:
            inquiry_id: Inquiry ID
            error_message: Error message
        """
        inquiry = self.db.query(Inquiry).filter(Inquiry.id == inquiry_id).first()
        if inquiry:
            inquiry.status = "failed"
            inquiry.updated_at = datetime.utcnow()
            self.db.commit()

            self._log_activity(
                action="inquiry_processing_failed",
                inquiry_id=inquiry_id,
                error_message=error_message
            )

    def flag_for_human_review(self, inquiry_id: int, reason: str = ""):
        """
        Flag inquiry for human review

        Args:
            inquiry_id: Inquiry ID
            reason: Reason for flagging
        """
        inquiry = self.db.query(Inquiry).filter(Inquiry.id == inquiry_id).first()
        if inquiry:
            inquiry.requires_human = True
            inquiry.updated_at = datetime.utcnow()
            self.db.commit()

            self._log_activity(
                action="inquiry_flagged_for_human",
                inquiry_id=inquiry_id,
                details={"reason": reason}
            )

            logger.warning(f"Inquiry {inquiry_id} flagged for human review: {reason}")

    def _log_activity(
        self,
        action: str,
        inquiry_id: Optional[int] = None,
        details: Optional[Dict] = None,
        error_message: Optional[str] = None
    ):
        """
        Log activity to database

        Args:
            action: Action name
            inquiry_id: Related inquiry ID
            details: Additional details
            error_message: Error message if any
        """
        try:
            import json
            log = ActivityLog(
                inquiry_id=inquiry_id,
                action=action,
                action_type="collect",
                actor="system",
                actor_type="system",
                details=json.dumps(details) if details else None,
                status="success" if not error_message else "failed",
                error_message=error_message
            )
            self.db.add(log)
            self.db.commit()
        except Exception as e:
            logger.error(f"Failed to log activity: {str(e)}")

    def get_inquiry_stats(self) -> Dict[str, int]:
        """
        Get statistics about inquiries

        Returns:
            Dictionary with inquiry statistics
        """
        return {
            "total": self.db.query(Inquiry).count(),
            "pending": self.db.query(Inquiry).filter(Inquiry.status == "pending").count(),
            "processing": self.db.query(Inquiry).filter(Inquiry.status == "processing").count(),
            "processed": self.db.query(Inquiry).filter(Inquiry.status == "processed").count(),
            "failed": self.db.query(Inquiry).filter(Inquiry.status == "failed").count(),
            "requires_human": self.db.query(Inquiry).filter(Inquiry.requires_human == True).count(),
            "urgent": self.db.query(Inquiry).filter(Inquiry.is_urgent == True).count()
        }
