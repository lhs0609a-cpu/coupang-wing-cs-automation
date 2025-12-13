"""
Response Submitter Service
Handles submission of approved responses to Coupang Wing
"""
from typing import Dict, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from loguru import logger

from ..models import Inquiry, Response, ActivityLog
from .coupang_api import CoupangAPIClient
from ..config import settings


class ResponseSubmitter:
    """
    Submits approved responses to Coupang Wing API
    """

    def __init__(self, db: Session, api_client: CoupangAPIClient = None):
        self.db = db
        self.api_client = api_client or CoupangAPIClient()

    def submit_response(
        self,
        response_id: int,
        submitted_by: str = "system"
    ) -> Dict[str, any]:
        """
        Submit an approved response to Coupang Wing

        Args:
            response_id: Response ID to submit
            submitted_by: Username/ID of submitter

        Returns:
            Submission result
        """
        logger.info(f"Attempting to submit response {response_id}")

        # Load response
        response = self.db.query(Response).filter(Response.id == response_id).first()
        if not response:
            logger.error(f"Response {response_id} not found")
            return {"success": False, "error": "Response not found"}

        # Load inquiry
        inquiry = self.db.query(Inquiry).filter(Inquiry.id == response.inquiry_id).first()
        if not inquiry:
            logger.error(f"Inquiry {response.inquiry_id} not found")
            return {"success": False, "error": "Inquiry not found"}

        # Pre-submission validation
        validation_result = self._validate_before_submission(response, inquiry)
        if not validation_result["valid"]:
            logger.error(f"Pre-submission validation failed: {validation_result['issues']}")
            self._log_submission_failed(
                response,
                inquiry,
                "Validation failed",
                validation_result['issues']
            )
            return {
                "success": False,
                "error": "Pre-submission validation failed",
                "issues": validation_result['issues']
            }

        # Final safety check
        if not response.approved_by:
            logger.warning(f"Response {response_id} not approved")
            return {"success": False, "error": "Response not approved"}

        try:
            # Submit to Coupang API
            api_result = self.api_client.submit_online_inquiry_reply(
                inquiry_id=inquiry.coupang_inquiry_id,
                content=response.response_text,
                reply_by=submitted_by
            )

            # Check API response
            if api_result.get("code") in [200, "200"]:
                # Success
                self._mark_submission_success(response, inquiry, submitted_by)
                logger.success(f"Response {response_id} submitted successfully")

                return {
                    "success": True,
                    "response_id": response_id,
                    "inquiry_id": inquiry.id,
                    "coupang_inquiry_id": inquiry.coupang_inquiry_id,
                    "submitted_at": response.submitted_at.isoformat()
                }
            else:
                # API returned error
                error_msg = api_result.get("message", "Unknown error")
                self._mark_submission_failed(response, inquiry, error_msg)
                logger.error(f"API returned error: {error_msg}")

                return {
                    "success": False,
                    "error": error_msg,
                    "api_response": api_result
                }

        except Exception as e:
            # Exception during submission
            error_msg = str(e)
            self._mark_submission_failed(response, inquiry, error_msg)
            logger.error(f"Submission error: {error_msg}")

            return {
                "success": False,
                "error": error_msg
            }

    def _validate_before_submission(
        self,
        response: Response,
        inquiry: Inquiry
    ) -> Dict[str, any]:
        """
        Final validation before submission

        Args:
            response: Response object
            inquiry: Inquiry object

        Returns:
            Validation result
        """
        issues = []

        # Check approval status
        if not response.approved_by or not response.approved_at:
            issues.append("Response not approved")

        # Check validation passed
        if not response.validation_passed:
            issues.append("Response did not pass validation")

        # Check if already submitted
        if response.status == "submitted":
            issues.append("Response already submitted")

        # Check for duplicate submission
        if self.api_client.check_duplicate_reply(inquiry.coupang_inquiry_id):
            issues.append("Duplicate reply detected")

        # Validate content one more time
        content_validation = self.api_client.validate_response_content(response.response_text)
        if not content_validation["valid"]:
            issues.extend(content_validation["issues"])

        # Check inquiry status
        if inquiry.status == "processed":
            issues.append("Inquiry already processed")

        return {
            "valid": len(issues) == 0,
            "issues": issues
        }

    def _mark_submission_success(
        self,
        response: Response,
        inquiry: Inquiry,
        submitted_by: str
    ):
        """
        Mark response as successfully submitted

        Args:
            response: Response object
            inquiry: Inquiry object
            submitted_by: Submitter username
        """
        now = datetime.utcnow()

        # Update response
        response.status = "submitted"
        response.submission_status = "success"
        response.submitted_at = now
        response.submitted_by = submitted_by

        # Calculate response time
        if inquiry.inquiry_date and inquiry.created_at:
            delta = now - inquiry.inquiry_date
            response.response_time_seconds = int(delta.total_seconds())

        # Update inquiry
        inquiry.status = "processed"
        inquiry.updated_at = now

        self.db.commit()

        # Log activity
        self._log_activity(
            action="response_submitted",
            inquiry_id=inquiry.id,
            response_id=response.id,
            actor=submitted_by,
            status="success"
        )

    def _mark_submission_failed(
        self,
        response: Response,
        inquiry: Inquiry,
        error_message: str
    ):
        """
        Mark response submission as failed

        Args:
            response: Response object
            inquiry: Inquiry object
            error_message: Error message
        """
        response.status = "approved"  # Keep as approved for retry
        response.submission_status = "failed"
        response.submission_error = error_message

        inquiry.status = "failed"

        self.db.commit()

        self._log_activity(
            action="response_submission_failed",
            inquiry_id=inquiry.id,
            response_id=response.id,
            status="failed",
            error_message=error_message
        )

    def _log_submission_failed(
        self,
        response: Response,
        inquiry: Inquiry,
        reason: str,
        details: list
    ):
        """
        Log submission failure

        Args:
            response: Response object
            inquiry: Inquiry object
            reason: Failure reason
            details: Details list
        """
        import json

        self._log_activity(
            action="submission_validation_failed",
            inquiry_id=inquiry.id,
            response_id=response.id,
            status="failed",
            details={"reason": reason, "issues": details}
        )

    def _log_activity(
        self,
        action: str,
        inquiry_id: Optional[int] = None,
        response_id: Optional[int] = None,
        actor: str = "system",
        status: str = "success",
        error_message: Optional[str] = None,
        details: Optional[Dict] = None
    ):
        """
        Log activity to database

        Args:
            action: Action name
            inquiry_id: Inquiry ID
            response_id: Response ID
            actor: Actor username
            status: Status
            error_message: Error message
            details: Additional details
        """
        try:
            import json
            log = ActivityLog(
                inquiry_id=inquiry_id,
                response_id=response_id,
                action=action,
                action_type="submit",
                actor=actor,
                actor_type="system" if actor == "system" else "human",
                status=status,
                error_message=error_message,
                details=json.dumps(details, ensure_ascii=False) if details else None
            )
            self.db.add(log)
            self.db.commit()
        except Exception as e:
            logger.error(f"Failed to log activity: {str(e)}")

    def retry_failed_submission(self, response_id: int, submitted_by: str = "system") -> Dict:
        """
        Retry a failed submission

        Args:
            response_id: Response ID
            submitted_by: Submitter username

        Returns:
            Submission result
        """
        response = self.db.query(Response).filter(Response.id == response_id).first()
        if not response:
            return {"success": False, "error": "Response not found"}

        if response.submission_status != "failed":
            return {"success": False, "error": "Response was not in failed state"}

        logger.info(f"Retrying submission for response {response_id}")
        return self.submit_response(response_id, submitted_by)

    def get_submission_stats(self) -> Dict[str, int]:
        """
        Get submission statistics

        Returns:
            Statistics dictionary
        """
        return {
            "total_submitted": self.db.query(Response).filter(
                Response.status == "submitted"
            ).count(),
            "submission_success": self.db.query(Response).filter(
                Response.submission_status == "success"
            ).count(),
            "submission_failed": self.db.query(Response).filter(
                Response.submission_status == "failed"
            ).count(),
            "pending_submission": self.db.query(Response).filter(
                Response.status == "approved"
            ).count()
        }

    def bulk_submit_approved(self, limit: int = 10) -> Dict:
        """
        Submit multiple approved responses in bulk

        Args:
            limit: Maximum number to submit

        Returns:
            Bulk submission result
        """
        # Get approved responses ready for submission
        responses = self.db.query(Response).filter(
            Response.status == "approved",
            Response.validation_passed == True
        ).limit(limit).all()

        results = {
            "total": len(responses),
            "success": 0,
            "failed": 0,
            "details": []
        }

        for response in responses:
            result = self.submit_response(response.id)
            if result["success"]:
                results["success"] += 1
            else:
                results["failed"] += 1

            results["details"].append({
                "response_id": response.id,
                "result": result
            })

        logger.info(f"Bulk submission complete: {results['success']} succeeded, {results['failed']} failed")
        return results
