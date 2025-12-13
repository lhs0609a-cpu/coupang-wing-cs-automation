"""
Bulk Operations Service
"""
from typing import List, Dict
from sqlalchemy.orm import Session
from loguru import logger
from datetime import datetime

from ..models import Inquiry, Response


class BulkOperationsService:
    """
    Service for handling bulk operations on inquiries and responses
    """

    def __init__(self, db: Session):
        self.db = db

    def bulk_approve_responses(
        self,
        response_ids: List[int],
        approved_by: str
    ) -> Dict:
        """
        Approve multiple responses at once

        Args:
            response_ids: List of response IDs
            approved_by: Approver username

        Returns:
            Operation result
        """
        results = {
            'total': len(response_ids),
            'success': 0,
            'failed': 0,
            'errors': []
        }

        for response_id in response_ids:
            try:
                response = self.db.query(Response).filter(
                    Response.id == response_id
                ).first()

                if not response:
                    results['failed'] += 1
                    results['errors'].append(f"Response {response_id} not found")
                    continue

                response.status = "approved"
                response.approved_by = approved_by
                response.approved_at = datetime.utcnow()

                results['success'] += 1

            except Exception as e:
                results['failed'] += 1
                results['errors'].append(f"Response {response_id}: {str(e)}")
                logger.error(f"Error approving response {response_id}: {str(e)}")

        self.db.commit()

        logger.info(f"Bulk approve: {results['success']}/{results['total']} succeeded")
        return results

    def bulk_reject_responses(
        self,
        response_ids: List[int],
        reason: str = ""
    ) -> Dict:
        """Reject multiple responses"""
        results = {
            'total': len(response_ids),
            'success': 0,
            'failed': 0,
            'errors': []
        }

        for response_id in response_ids:
            try:
                response = self.db.query(Response).filter(
                    Response.id == response_id
                ).first()

                if response:
                    response.status = "rejected"
                    response.rejection_reason = reason
                    results['success'] += 1
                else:
                    results['failed'] += 1

            except Exception as e:
                results['failed'] += 1
                results['errors'].append(str(e))

        self.db.commit()
        return results

    def bulk_assign_inquiries(
        self,
        inquiry_ids: List[int],
        assigned_to: int
    ) -> Dict:
        """Assign multiple inquiries to a user"""
        results = {
            'total': len(inquiry_ids),
            'success': 0,
            'failed': 0
        }

        for inquiry_id in inquiry_ids:
            try:
                inquiry = self.db.query(Inquiry).filter(
                    Inquiry.id == inquiry_id
                ).first()

                if inquiry:
                    inquiry.assigned_to = assigned_to
                    results['success'] += 1
                else:
                    results['failed'] += 1

            except Exception as e:
                results['failed'] += 1
                logger.error(f"Error assigning inquiry {inquiry_id}: {str(e)}")

        self.db.commit()
        return results

    def bulk_add_tags(
        self,
        inquiry_ids: List[int],
        tags: List[str]
    ) -> Dict:
        """Add tags to multiple inquiries"""
        from ..models.comment import InquiryTag

        results = {'success': 0, 'failed': 0}

        for inquiry_id in inquiry_ids:
            try:
                for tag_name in tags:
                    tag = InquiryTag(
                        inquiry_id=inquiry_id,
                        name=tag_name
                    )
                    self.db.add(tag)

                results['success'] += 1

            except Exception as e:
                results['failed'] += 1
                logger.error(f"Error adding tags to inquiry {inquiry_id}: {str(e)}")

        self.db.commit()
        return results

    def bulk_change_status(
        self,
        inquiry_ids: List[int],
        new_status: str
    ) -> Dict:
        """Change status of multiple inquiries"""
        results = {'success': 0, 'failed': 0}

        for inquiry_id in inquiry_ids:
            try:
                inquiry = self.db.query(Inquiry).filter(
                    Inquiry.id == inquiry_id
                ).first()

                if inquiry:
                    inquiry.status = new_status
                    results['success'] += 1

            except Exception as e:
                results['failed'] += 1

        self.db.commit()
        return results
