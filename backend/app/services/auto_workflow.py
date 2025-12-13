"""
Automated Workflow Service
Handles automatic processing, approval, and submission
"""
from typing import Dict, List
from sqlalchemy.orm import Session
from loguru import logger
from datetime import datetime

from ..models import Inquiry, Response
from .inquiry_collector import InquiryCollector
from .inquiry_analyzer import InquiryAnalyzer
from .response_generator import ResponseGenerator
from .validator import ResponseValidator
from .submitter import ResponseSubmitter
from ..config import settings


class AutoWorkflow:
    """
    Orchestrates the automated workflow from inquiry collection to submission
    """

    def __init__(self, db: Session):
        self.db = db
        self.collector = InquiryCollector(db)
        self.analyzer = InquiryAnalyzer(db)
        self.generator = ResponseGenerator(db)
        self.validator = ResponseValidator(db)
        self.submitter = ResponseSubmitter(db)

    def run_full_auto_workflow(
        self,
        limit: int = 10,
        auto_submit: bool = False
    ) -> Dict:
        """
        Run complete automated workflow

        Args:
            limit: Maximum inquiries to process
            auto_submit: Whether to auto-submit approved responses

        Returns:
            Results dictionary
        """
        results = {
            "collected": 0,
            "analyzed": 0,
            "generated": 0,
            "validated": 0,
            "auto_approved": 0,
            "submitted": 0,
            "requires_human": 0,
            "errors": [],
            "details": []
        }

        logger.info(f"Starting automated workflow (limit={limit}, auto_submit={auto_submit})")

        try:
            # Step 1: Collect new inquiries
            try:
                inquiries = self.collector.collect_new_inquiries()
                results["collected"] = len(inquiries)
                logger.info(f"Collected {len(inquiries)} new inquiries")
            except Exception as e:
                logger.error(f"Collection error: {str(e)}")
                results["errors"].append(f"Collection: {str(e)}")

            # Step 2: Get pending inquiries
            pending = self.collector.get_pending_inquiries(limit=limit)
            logger.info(f"Processing {len(pending)} pending inquiries")

            # Step 3: Process each inquiry
            for inquiry in pending:
                try:
                    result = self._process_single_inquiry(inquiry, auto_submit)
                    results["details"].append(result)

                    # Update counters
                    if result["analyzed"]:
                        results["analyzed"] += 1
                    if result["generated"]:
                        results["generated"] += 1
                    if result["validated"]:
                        results["validated"] += 1
                    if result["auto_approved"]:
                        results["auto_approved"] += 1
                    if result["submitted"]:
                        results["submitted"] += 1
                    if result["requires_human"]:
                        results["requires_human"] += 1

                except Exception as e:
                    error_msg = f"Inquiry {inquiry.id}: {str(e)}"
                    logger.error(error_msg)
                    results["errors"].append(error_msg)

            logger.success(f"Workflow complete: {results}")
            return results

        except Exception as e:
            logger.error(f"Workflow error: {str(e)}")
            results["errors"].append(str(e))
            return results

    def _process_single_inquiry(
        self,
        inquiry: Inquiry,
        auto_submit: bool
    ) -> Dict:
        """
        Process a single inquiry through the workflow

        Args:
            inquiry: Inquiry to process
            auto_submit: Whether to auto-submit

        Returns:
            Processing result
        """
        result = {
            "inquiry_id": inquiry.id,
            "analyzed": False,
            "generated": False,
            "validated": False,
            "auto_approved": False,
            "submitted": False,
            "requires_human": False,
            "error": None
        }

        try:
            # Mark as processing
            self.collector.mark_inquiry_as_processing(inquiry.id)

            # Step 1: Analyze inquiry
            analysis = self.analyzer.analyze_inquiry(inquiry)
            result["analyzed"] = True

            # Check if requires human review
            if inquiry.requires_human:
                logger.warning(f"Inquiry {inquiry.id} flagged for human review")
                result["requires_human"] = True
                return result

            # Step 2: Generate response using AI
            response = self.generator.generate_response(inquiry, method="ai")
            if not response:
                logger.error(f"Failed to generate response for inquiry {inquiry.id}")
                result["error"] = "Response generation failed"
                return result

            result["generated"] = True
            result["response_id"] = response.id

            # Step 3: Validate response
            validation = self.validator.validate_response(response, inquiry)
            result["validated"] = validation["passed"]
            result["confidence"] = validation["confidence"]
            result["risk_level"] = validation["risk_level"]

            # Step 4: Auto-approval decision
            can_auto_approve = self._can_auto_approve(response, validation)

            if can_auto_approve:
                # Auto-approve
                response.status = "approved"
                response.approved_by = "system_auto"
                response.approved_at = datetime.utcnow()
                response.auto_approved = True
                self.db.commit()

                result["auto_approved"] = True
                logger.info(f"Response {response.id} auto-approved")

                # Step 5: Auto-submit if enabled
                if auto_submit:
                    submission_result = self.submitter.submit_response(
                        response.id,
                        submitted_by="system_auto"
                    )

                    if submission_result["success"]:
                        result["submitted"] = True
                        logger.success(f"Response {response.id} auto-submitted")
                    else:
                        result["error"] = submission_result.get("error", "Submission failed")
                        logger.error(f"Auto-submit failed: {result['error']}")
            else:
                # Requires human approval
                result["requires_human"] = True
                logger.info(f"Response {response.id} requires human approval")

            # Mark inquiry as processed
            self.collector.mark_inquiry_as_processed(inquiry.id)

        except Exception as e:
            logger.error(f"Error processing inquiry {inquiry.id}: {str(e)}")
            result["error"] = str(e)
            self.collector.mark_inquiry_as_failed(inquiry.id, str(e))

        return result

    def _can_auto_approve(
        self,
        response: Response,
        validation: Dict
    ) -> bool:
        """
        Determine if response can be auto-approved

        Args:
            response: Response object
            validation: Validation result

        Returns:
            True if can auto-approve
        """
        # Must pass validation
        if not validation["passed"]:
            return False

        # Must have high confidence
        if validation["confidence"] < settings.AUTO_APPROVE_THRESHOLD:
            return False

        # Must be low risk
        if validation["risk_level"] != "low":
            return False

        # Response must be validated
        if not response.validation_passed:
            return False

        return True

    def auto_process_and_submit(self, limit: int = 10) -> Dict:
        """
        Convenience method for full auto-processing with submission

        Args:
            limit: Maximum inquiries to process

        Returns:
            Results dictionary
        """
        return self.run_full_auto_workflow(limit=limit, auto_submit=True)

    def get_workflow_stats(self) -> Dict:
        """
        Get statistics about automated workflow

        Returns:
            Statistics dictionary
        """
        total_responses = self.db.query(Response).count()
        auto_approved = self.db.query(Response).filter(
            Response.auto_approved == True
        ).count()
        auto_submitted = self.db.query(Response).filter(
            Response.auto_approved == True,
            Response.status == "submitted"
        ).count()

        auto_approval_rate = (auto_approved / total_responses * 100) if total_responses > 0 else 0
        auto_submission_rate = (auto_submitted / auto_approved * 100) if auto_approved > 0 else 0

        return {
            "total_responses": total_responses,
            "auto_approved": auto_approved,
            "auto_submitted": auto_submitted,
            "auto_approval_rate": round(auto_approval_rate, 2),
            "auto_submission_rate": round(auto_submission_rate, 2)
        }

    def process_pending_approvals(self) -> Dict:
        """
        Process all pending approvals that can be auto-approved

        Returns:
            Results dictionary
        """
        results = {
            "processed": 0,
            "auto_approved": 0,
            "submitted": 0,
            "errors": []
        }

        # Get pending responses
        pending_responses = self.db.query(Response).filter(
            Response.status.in_(["pending_approval", "draft"])
        ).all()

        results["processed"] = len(pending_responses)

        for response in pending_responses:
            try:
                # Re-validate
                inquiry = self.db.query(Inquiry).filter(
                    Inquiry.id == response.inquiry_id
                ).first()

                validation = self.validator.validate_response(response, inquiry)

                # Check if can auto-approve
                if self._can_auto_approve(response, validation):
                    response.status = "approved"
                    response.approved_by = "system_auto"
                    response.approved_at = datetime.utcnow()
                    response.auto_approved = True
                    self.db.commit()

                    results["auto_approved"] += 1

                    # Auto-submit
                    submission = self.submitter.submit_response(
                        response.id,
                        submitted_by="system_auto"
                    )

                    if submission["success"]:
                        results["submitted"] += 1

            except Exception as e:
                results["errors"].append(f"Response {response.id}: {str(e)}")

        return results
