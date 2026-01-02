"""
Inquiry Collector Service
Collects and processes customer inquiries from Coupang Wing
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from loguru import logger

from ..models import Inquiry, ActivityLog
from ..exceptions import NotFoundError, ValidationError, APIError, DatabaseError
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
        account_id: Optional[int] = None,
        inquiry_type: str = "online",
        status_filter: Optional[str] = None
    ) -> List[Inquiry]:
        """
        Collect new inquiries from Coupang Wing

        Args:
            account_id: Coupang account ID to collect inquiries from
            inquiry_type: Type of inquiries to collect ('online' or 'callcenter')
            status_filter: Filter by status (e.g., 'WAITING' for unanswered)

        Returns:
            List of newly collected Inquiry objects
        """
        # Validate inquiry_type
        if inquiry_type not in ("online", "callcenter"):
            raise ValidationError(f"Invalid inquiry_type: {inquiry_type}. Must be 'online' or 'callcenter'")

        logger.info(f"Starting inquiry collection: account={account_id}, type={inquiry_type}, status={status_filter}")

        try:
            # Fetch inquiries from API
            # Note: account_id is used for logging/tracking only
            # CoupangAPIClient already has vendor_id set in constructor
            if inquiry_type == "online":
                response = self.api_client.get_online_inquiries(
                    status=status_filter or "WAITING",
                    answered_type="NOANSWER"  # Get unanswered inquiries
                )
            else:
                response = self.api_client.get_call_center_inquiries(
                    partner_counseling_status="NO_ANSWER"  # Get unanswered inquiries
                )

            # Check API response status
            response_code = response.get("code", "")
            if response_code and response_code not in ("200", "SUCCESS", "OK"):
                error_msg = response.get("message", "Unknown API error")
                logger.error(f"Coupang API returned error: code={response_code}, message={error_msg}")
                raise APIError(f"Coupang API error: {error_msg}")

            # Parse response and save to database
            inquiries = self._parse_and_save_inquiries(response, inquiry_type)

            logger.success(f"Collected {len(inquiries)} new inquiries")
            return inquiries

        except (ValidationError, NotFoundError):
            raise
        except SQLAlchemyError as e:
            logger.error(f"Database error collecting inquiries: {str(e)}")
            self._log_activity("inquiry_collection_failed", error_message=str(e))
            raise DatabaseError(f"Database error while collecting inquiries: {str(e)}")
        except Exception as e:
            logger.error(f"API error collecting inquiries: {str(e)}")
            self._log_activity("inquiry_collection_failed", error_message=str(e))
            raise APIError(f"Failed to collect inquiries from Coupang API: {str(e)}")

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
        # Coupang API response structure: { "code": "...", "message": "...", "data": { "content": [...] } }
        # or sometimes: { "code": "...", "data": [...] }
        inquiry_data_list = []

        data = api_response.get("data", [])
        if isinstance(data, dict):
            # Try common Coupang API response structures
            inquiry_data_list = data.get("content", []) or data.get("inquiries", []) or data.get("items", [])
        elif isinstance(data, list):
            inquiry_data_list = data

        logger.info(f"Parsed {len(inquiry_data_list)} inquiries from API response")

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
        if limit < 1 or limit > 500:
            raise ValidationError(f"Invalid limit: {limit}. Must be between 1 and 500")

        try:
            return self.db.query(Inquiry).filter(
                Inquiry.status == "pending"
            ).order_by(
                Inquiry.is_urgent.desc(),
                Inquiry.inquiry_date.asc()
            ).limit(limit).all()
        except SQLAlchemyError as e:
            logger.error(f"Database error fetching pending inquiries: {str(e)}")
            raise DatabaseError(f"Failed to fetch pending inquiries: {str(e)}")

    def mark_inquiry_as_processing(self, inquiry_id: int):
        """
        Mark inquiry as being processed

        Args:
            inquiry_id: Inquiry ID

        Raises:
            NotFoundError: If inquiry not found
            DatabaseError: If database operation fails
        """
        try:
            inquiry = self.db.query(Inquiry).filter(Inquiry.id == inquiry_id).first()
            if not inquiry:
                raise NotFoundError(f"Inquiry not found: {inquiry_id}")

            inquiry.status = "processing"
            inquiry.updated_at = datetime.utcnow()
            self.db.commit()

            self._log_activity(
                action="inquiry_processing_started",
                inquiry_id=inquiry_id
            )
        except NotFoundError:
            raise
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error marking inquiry as processing: {str(e)}")
            raise DatabaseError(f"Failed to update inquiry status: {str(e)}")

    def mark_inquiry_as_processed(self, inquiry_id: int):
        """
        Mark inquiry as processed

        Args:
            inquiry_id: Inquiry ID

        Raises:
            NotFoundError: If inquiry not found
            DatabaseError: If database operation fails
        """
        try:
            inquiry = self.db.query(Inquiry).filter(Inquiry.id == inquiry_id).first()
            if not inquiry:
                raise NotFoundError(f"Inquiry not found: {inquiry_id}")

            inquiry.status = "processed"
            inquiry.updated_at = datetime.utcnow()
            self.db.commit()

            self._log_activity(
                action="inquiry_processed",
                inquiry_id=inquiry_id
            )
        except NotFoundError:
            raise
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error marking inquiry as processed: {str(e)}")
            raise DatabaseError(f"Failed to update inquiry status: {str(e)}")

    def mark_inquiry_as_failed(self, inquiry_id: int, error_message: str = ""):
        """
        Mark inquiry as failed

        Args:
            inquiry_id: Inquiry ID
            error_message: Error message

        Raises:
            NotFoundError: If inquiry not found
            DatabaseError: If database operation fails
        """
        try:
            inquiry = self.db.query(Inquiry).filter(Inquiry.id == inquiry_id).first()
            if not inquiry:
                raise NotFoundError(f"Inquiry not found: {inquiry_id}")

            inquiry.status = "failed"
            inquiry.updated_at = datetime.utcnow()
            self.db.commit()

            self._log_activity(
                action="inquiry_processing_failed",
                inquiry_id=inquiry_id,
                error_message=error_message
            )
        except NotFoundError:
            raise
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error marking inquiry as failed: {str(e)}")
            raise DatabaseError(f"Failed to update inquiry status: {str(e)}")

    def flag_for_human_review(self, inquiry_id: int, reason: str = ""):
        """
        Flag inquiry for human review

        Args:
            inquiry_id: Inquiry ID
            reason: Reason for flagging

        Raises:
            NotFoundError: If inquiry not found
            DatabaseError: If database operation fails
        """
        try:
            inquiry = self.db.query(Inquiry).filter(Inquiry.id == inquiry_id).first()
            if not inquiry:
                raise NotFoundError(f"Inquiry not found: {inquiry_id}")

            inquiry.requires_human = True
            inquiry.updated_at = datetime.utcnow()
            self.db.commit()

            self._log_activity(
                action="inquiry_flagged_for_human",
                inquiry_id=inquiry_id,
                details={"reason": reason}
            )

            logger.warning(f"Inquiry {inquiry_id} flagged for human review: {reason}")
        except NotFoundError:
            raise
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error flagging inquiry for human review: {str(e)}")
            raise DatabaseError(f"Failed to flag inquiry for human review: {str(e)}")

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

        Raises:
            DatabaseError: If database operation fails
        """
        try:
            return {
                "total": self.db.query(Inquiry).count(),
                "pending": self.db.query(Inquiry).filter(Inquiry.status == "pending").count(),
                "processing": self.db.query(Inquiry).filter(Inquiry.status == "processing").count(),
                "processed": self.db.query(Inquiry).filter(Inquiry.status == "processed").count(),
                "failed": self.db.query(Inquiry).filter(Inquiry.status == "failed").count(),
                "requires_human": self.db.query(Inquiry).filter(Inquiry.requires_human == True).count(),
                "urgent": self.db.query(Inquiry).filter(Inquiry.is_urgent == True).count()
            }
        except SQLAlchemyError as e:
            logger.error(f"Database error fetching inquiry stats: {str(e)}")
            raise DatabaseError(f"Failed to fetch inquiry statistics: {str(e)}")
