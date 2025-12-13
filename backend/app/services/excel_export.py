"""
Excel/CSV Import/Export Service
"""
import csv
import io
from typing import List, Dict
from datetime import datetime
from sqlalchemy.orm import Session
from loguru import logger

from ..models import Inquiry, Response


class ExcelExportService:
    """
    Service for Excel/CSV import and export
    """

    def __init__(self, db: Session):
        self.db = db

    def export_inquiries_to_csv(
        self,
        inquiry_ids: List[int] = None,
        filters: Dict = None
    ) -> str:
        """
        Export inquiries to CSV format

        Args:
            inquiry_ids: Specific inquiry IDs to export
            filters: Filter criteria

        Returns:
            CSV string
        """
        query = self.db.query(Inquiry)

        if inquiry_ids:
            query = query.filter(Inquiry.id.in_(inquiry_ids))

        inquiries = query.all()

        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow([
            'ID',
            'Customer Name',
            'Customer ID',
            'Order Number',
            'Product Name',
            'Inquiry Text',
            'Category',
            'Risk Level',
            'Status',
            'Is Urgent',
            'Requires Human',
            'Confidence Score',
            'Inquiry Date',
            'Created At'
        ])

        # Write data
        for inquiry in inquiries:
            writer.writerow([
                inquiry.id,
                inquiry.customer_name or '',
                inquiry.customer_id or '',
                inquiry.order_number or '',
                inquiry.product_name or '',
                inquiry.inquiry_text[:500] if inquiry.inquiry_text else '',  # Truncate long text
                inquiry.classified_category or '',
                inquiry.risk_level or '',
                inquiry.status,
                'Yes' if inquiry.is_urgent else 'No',
                'Yes' if inquiry.requires_human else 'No',
                inquiry.confidence_score or 0,
                inquiry.inquiry_date.strftime('%Y-%m-%d %H:%M:%S') if inquiry.inquiry_date else '',
                inquiry.created_at.strftime('%Y-%m-%d %H:%M:%S')
            ])

        logger.info(f"Exported {len(inquiries)} inquiries to CSV")
        return output.getvalue()

    def export_responses_to_csv(self, response_ids: List[int] = None) -> str:
        """Export responses to CSV"""
        query = self.db.query(Response)

        if response_ids:
            query = query.filter(Response.id.in_(response_ids))

        responses = query.all()

        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow([
            'ID',
            'Inquiry ID',
            'Response Text',
            'Confidence Score',
            'Risk Level',
            'Status',
            'Generation Method',
            'Validated',
            'Approved By',
            'Submitted At',
            'Created At'
        ])

        # Data
        for response in responses:
            writer.writerow([
                response.id,
                response.inquiry_id,
                response.response_text[:500],
                response.confidence_score or 0,
                response.risk_level or '',
                response.status,
                response.generation_method or '',
                'Yes' if response.validation_passed else 'No',
                response.approved_by or '',
                response.submitted_at.strftime('%Y-%m-%d %H:%M:%S') if response.submitted_at else '',
                response.created_at.strftime('%Y-%m-%d %H:%M:%S')
            ])

        logger.info(f"Exported {len(responses)} responses to CSV")
        return output.getvalue()

    def import_inquiries_from_csv(self, csv_content: str) -> Dict:
        """
        Import inquiries from CSV

        Args:
            csv_content: CSV file content

        Returns:
            Import result
        """
        results = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'errors': []
        }

        try:
            csv_file = io.StringIO(csv_content)
            reader = csv.DictReader(csv_file)

            for row in reader:
                results['total'] += 1

                try:
                    inquiry = Inquiry(
                        customer_name=row.get('Customer Name'),
                        customer_id=row.get('Customer ID'),
                        order_number=row.get('Order Number'),
                        product_name=row.get('Product Name'),
                        inquiry_text=row.get('Inquiry Text'),
                        classified_category=row.get('Category'),
                        status=row.get('Status', 'pending')
                    )

                    self.db.add(inquiry)
                    results['success'] += 1

                except Exception as e:
                    results['failed'] += 1
                    results['errors'].append(f"Row {results['total']}: {str(e)}")

            self.db.commit()
            logger.info(f"Imported {results['success']}/{results['total']} inquiries")

        except Exception as e:
            logger.error(f"CSV import error: {str(e)}")
            results['errors'].append(str(e))

        return results

    def export_report_to_csv(self, report_data: Dict) -> str:
        """Export any report data to CSV"""
        output = io.StringIO()
        writer = csv.writer(output)

        # Generic report export
        if 'daily_breakdown' in report_data:
            writer.writerow(['Date', 'Inquiries', 'Responses', 'Auto Approved'])

            for day in report_data['daily_breakdown']:
                writer.writerow([
                    day['date'],
                    day['inquiries'],
                    day['responses'],
                    day['auto_approved']
                ])

        return output.getvalue()
