"""
Privacy and Sensitive Information Masking Service
"""
from typing import Dict, List, Optional, Tuple
import re
from loguru import logger


class PrivacyMaskService:
    """
    Service for detecting and masking sensitive information
    """

    def __init__(self):
        # Regex patterns for sensitive data detection
        self.patterns = {
            'phone': [
                r'01[016789]-?\d{3,4}-?\d{4}',  # Korean mobile
                r'\d{2,3}-?\d{3,4}-?\d{4}',  # Korean landline
                r'\+?\d{1,3}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}'  # International
            ],
            'email': [
                r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
            ],
            'credit_card': [
                r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',  # 16-digit card
                r'\b\d{4}[-\s]?\d{6}[-\s]?\d{5}\b'  # AMEX 15-digit
            ],
            'ssn_korea': [
                r'\d{6}-?\d{7}',  # Korean resident registration number
                r'\d{6}-?[1-4]\d{6}'  # With validation for first digit of second part
            ],
            'account_number': [
                r'\b\d{3}-?\d{2,6}-?\d{4,8}\b'  # Bank account patterns
            ],
            'address': [
                r'\b\d{5}\b',  # Postal code (5 digits)
                r'[가-힣]+시\s+[가-힣]+구\s+[가-힣]+동\s+\d+[-\d]*',  # Korean address format
                r'[가-힣]+도\s+[가-힣]+시\s+[가-힣]+구'
            ],
            'ip_address': [
                r'\b(?:\d{1,3}\.){3}\d{1,3}\b'  # IPv4
            ],
            'passport': [
                r'\b[A-Z]{1,2}\d{6,9}\b'  # Passport number
            ]
        }

        # Masking formats
        self.mask_formats = {
            'phone': lambda m: m[:3] + '-****-' + m[-4:] if len(m) >= 7 else '***-****-****',
            'email': lambda m: self._mask_email(m),
            'credit_card': lambda m: '****-****-****-' + m[-4:] if len(m.replace('-', '').replace(' ', '')) >= 4 else '****-****-****-****',
            'ssn_korea': lambda m: m[:6] + '-*******' if len(m) >= 13 else '******-*******',
            'account_number': lambda m: '***-***-****',
            'address': lambda m: '[주소]',
            'ip_address': lambda m: '***.***.***.' + m.split('.')[-1] if '.' in m else '***.***.***.***',
            'passport': lambda m: m[:2] + '******' if len(m) >= 2 else '********'
        }

    def detect_sensitive_data(self, text: str) -> Dict[str, List[Dict]]:
        """
        Detect all sensitive information in text

        Args:
            text: Text to analyze

        Returns:
            Dict mapping data types to list of detected instances
        """
        if not text:
            return {}

        detections = {}

        for data_type, patterns in self.patterns.items():
            matches = []
            for pattern in patterns:
                for match in re.finditer(pattern, text):
                    matches.append({
                        'value': match.group(),
                        'start': match.start(),
                        'end': match.end(),
                        'type': data_type
                    })

            if matches:
                detections[data_type] = matches

        return detections

    def mask_sensitive_data(
        self,
        text: str,
        mask_types: Optional[List[str]] = None,
        custom_masks: Optional[Dict[str, str]] = None
    ) -> Tuple[str, Dict]:
        """
        Mask sensitive information in text

        Args:
            text: Text to mask
            mask_types: List of data types to mask (None = mask all)
            custom_masks: Custom masking patterns

        Returns:
            Tuple of (masked_text, detection_report)
        """
        if not text:
            return text, {}

        masked_text = text
        detection_report = {
            'original_length': len(text),
            'masked_count': 0,
            'detections': {}
        }

        # Determine which types to mask
        types_to_mask = mask_types if mask_types else list(self.patterns.keys())

        # Collect all matches with their positions
        all_matches = []

        for data_type in types_to_mask:
            if data_type not in self.patterns:
                continue

            for pattern in self.patterns[data_type]:
                for match in re.finditer(pattern, text):
                    all_matches.append({
                        'value': match.group(),
                        'start': match.start(),
                        'end': match.end(),
                        'type': data_type
                    })

        # Sort matches by position (reverse order for replacement)
        all_matches.sort(key=lambda x: x['start'], reverse=True)

        # Replace matches
        for match in all_matches:
            data_type = match['type']

            # Get masking function
            if custom_masks and data_type in custom_masks:
                masked_value = custom_masks[data_type]
            elif data_type in self.mask_formats:
                masked_value = self.mask_formats[data_type](match['value'])
            else:
                masked_value = '***'

            # Replace in text
            masked_text = (
                masked_text[:match['start']] +
                masked_value +
                masked_text[match['end']:]
            )

            # Record in report
            if data_type not in detection_report['detections']:
                detection_report['detections'][data_type] = []

            detection_report['detections'][data_type].append({
                'original': match['value'],
                'masked': masked_value,
                'position': match['start']
            })

            detection_report['masked_count'] += 1

        detection_report['masked_length'] = len(masked_text)

        logger.info(f"Masked {detection_report['masked_count']} sensitive data instances")
        return masked_text, detection_report

    def _mask_email(self, email: str) -> str:
        """Mask email address preserving domain"""
        if '@' not in email:
            return '***@***.com'

        local, domain = email.split('@', 1)

        # Mask local part
        if len(local) <= 2:
            masked_local = '*' * len(local)
        else:
            masked_local = local[0] + '*' * (len(local) - 2) + local[-1]

        # Keep domain
        return f"{masked_local}@{domain}"

    def unmask_data(
        self,
        masked_text: str,
        original_text: str,
        user_role: str
    ) -> str:
        """
        Unmask data based on user permissions

        Args:
            masked_text: Masked text
            original_text: Original unmasked text
            user_role: User role for permission check

        Returns:
            Text with appropriate masking level
        """
        # Define permission levels
        full_access_roles = ['admin', 'manager', 'supervisor']
        partial_access_roles = ['agent', 'cs_representative']

        if user_role in full_access_roles:
            # Full access - return original text
            logger.info(f"User role {user_role} granted full access to unmasked data")
            return original_text

        elif user_role in partial_access_roles:
            # Partial access - unmask some types
            partial_mask_types = ['phone', 'email']  # Keep SSN, credit card masked
            masked, _ = self.mask_sensitive_data(
                original_text,
                mask_types=[t for t in self.patterns.keys() if t not in partial_mask_types]
            )
            logger.info(f"User role {user_role} granted partial access")
            return masked

        else:
            # No access - return fully masked
            logger.info(f"User role {user_role} - data remains fully masked")
            return masked_text

    def validate_masked_output(self, text: str) -> Dict:
        """
        Validate that sensitive data has been properly masked

        Args:
            text: Text to validate

        Returns:
            Validation result
        """
        detections = self.detect_sensitive_data(text)

        is_safe = len(detections) == 0

        return {
            'is_safe': is_safe,
            'remaining_sensitive_data': detections,
            'data_types_found': list(detections.keys()),
            'total_instances': sum(len(matches) for matches in detections.values())
        }

    def create_redaction_report(
        self,
        original_text: str,
        masked_text: str
    ) -> Dict:
        """
        Create a detailed redaction report

        Args:
            original_text: Original text
            masked_text: Masked text

        Returns:
            Redaction report
        """
        original_detections = self.detect_sensitive_data(original_text)
        masked_validation = self.validate_masked_output(masked_text)

        return {
            'original_text_length': len(original_text),
            'masked_text_length': len(masked_text),
            'sensitive_data_detected': original_detections,
            'total_redactions': sum(len(matches) for matches in original_detections.values()),
            'redaction_by_type': {
                data_type: len(matches)
                for data_type, matches in original_detections.items()
            },
            'masking_validation': masked_validation,
            'is_fully_masked': masked_validation['is_safe']
        }

    def get_masking_statistics(self, texts: List[str]) -> Dict:
        """
        Get statistics on sensitive data in a collection of texts

        Args:
            texts: List of texts to analyze

        Returns:
            Aggregated statistics
        """
        stats = {
            'total_texts': len(texts),
            'texts_with_sensitive_data': 0,
            'total_detections': 0,
            'detection_by_type': {}
        }

        for text in texts:
            detections = self.detect_sensitive_data(text)

            if detections:
                stats['texts_with_sensitive_data'] += 1

            for data_type, matches in detections.items():
                if data_type not in stats['detection_by_type']:
                    stats['detection_by_type'][data_type] = 0

                stats['detection_by_type'][data_type] += len(matches)
                stats['total_detections'] += len(matches)

        # Calculate percentages
        if stats['total_texts'] > 0:
            stats['sensitive_data_percentage'] = round(
                (stats['texts_with_sensitive_data'] / stats['total_texts']) * 100,
                2
            )

        return stats

    def add_custom_pattern(
        self,
        data_type: str,
        pattern: str,
        mask_format: Optional[callable] = None
    ):
        """
        Add a custom sensitive data pattern

        Args:
            data_type: Type of sensitive data
            pattern: Regex pattern
            mask_format: Function to format masked value
        """
        if data_type not in self.patterns:
            self.patterns[data_type] = []

        self.patterns[data_type].append(pattern)

        if mask_format:
            self.mask_formats[data_type] = mask_format
        elif data_type not in self.mask_formats:
            self.mask_formats[data_type] = lambda m: '***'

        logger.info(f"Added custom pattern for {data_type}")
