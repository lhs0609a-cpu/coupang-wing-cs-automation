"""
Advanced Sentiment Analysis & Emotion Visualization
"""
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from loguru import logger
import re

from ..models import Inquiry, Response


class SentimentAnalysisService:
    """
    Advanced sentiment analysis with emotion detection and visualization data
    """

    def __init__(self, db: Session):
        self.db = db

    def analyze_inquiry_sentiment(self, inquiry_text: str) -> Dict:
        """
        Analyze sentiment and emotions in inquiry text

        Args:
            inquiry_text: Text to analyze

        Returns:
            Sentiment analysis results
        """
        if not inquiry_text:
            return {
                'sentiment': 'neutral',
                'confidence': 0.0,
                'emotions': {},
                'urgency_indicators': [],
                'tone': 'neutral'
            }

        # Detect sentiment
        sentiment, confidence = self._detect_sentiment(inquiry_text)

        # Detect emotions
        emotions = self._detect_emotions(inquiry_text)

        # Detect urgency indicators
        urgency_indicators = self._detect_urgency(inquiry_text)

        # Analyze tone
        tone = self._analyze_tone(inquiry_text)

        return {
            'sentiment': sentiment,
            'confidence': confidence,
            'emotions': emotions,
            'urgency_indicators': urgency_indicators,
            'tone': tone,
            'text_length': len(inquiry_text),
            'exclamation_count': inquiry_text.count('!'),
            'question_count': inquiry_text.count('?')
        }

    def _detect_sentiment(self, text: str) -> tuple[str, float]:
        """
        Detect overall sentiment

        Returns:
            (sentiment, confidence)
        """
        text_lower = text.lower()

        # Korean positive keywords
        positive_keywords = [
            '좋', '감사', '만족', '훌륭', '최고', '친절', '빠른', '완벽', '정확',
            '고마', '도움', '해결', 'thanks', 'good', 'great', 'excellent'
        ]

        # Korean negative keywords
        negative_keywords = [
            '나쁜', '실망', '불만', '화가', '최악', '불친절', '느린', '오류', '문제',
            '환불', '취소', '신고', '항의', 'bad', 'terrible', 'disappointed', 'angry',
            '짜증', '속상', '답답', '화나', '열받', '미치'
        ]

        positive_count = sum(1 for keyword in positive_keywords if keyword in text_lower)
        negative_count = sum(1 for keyword in negative_keywords if keyword in text_lower)

        total_count = positive_count + negative_count

        if total_count == 0:
            return 'neutral', 0.5

        if negative_count > positive_count:
            confidence = min(0.6 + (negative_count * 0.1), 0.95)
            return 'negative', confidence
        elif positive_count > negative_count:
            confidence = min(0.6 + (positive_count * 0.1), 0.95)
            return 'positive', confidence
        else:
            return 'neutral', 0.6

    def _detect_emotions(self, text: str) -> Dict[str, float]:
        """
        Detect specific emotions with confidence scores

        Returns:
            Dict mapping emotion names to confidence scores
        """
        text_lower = text.lower()
        emotions = {}

        # Anger indicators
        anger_keywords = ['화', '짜증', '열받', '미치', '최악', '신고', '항의']
        anger_score = sum(1 for keyword in anger_keywords if keyword in text_lower)
        if anger_score > 0:
            emotions['anger'] = min(anger_score * 0.25, 1.0)

        # Frustration indicators
        frustration_keywords = ['답답', '속상', '도대체', '왜', '이해가 안', '납득']
        frustration_score = sum(1 for keyword in frustration_keywords if keyword in text_lower)
        if frustration_score > 0:
            emotions['frustration'] = min(frustration_score * 0.25, 1.0)

        # Anxiety indicators
        anxiety_keywords = ['걱정', '불안', '염려', '혹시', '문제', '괜찮을까']
        anxiety_score = sum(1 for keyword in anxiety_keywords if keyword in text_lower)
        if anxiety_score > 0:
            emotions['anxiety'] = min(anxiety_score * 0.25, 1.0)

        # Satisfaction indicators
        satisfaction_keywords = ['만족', '좋아', '감사', '고마', '훌륭', '완벽']
        satisfaction_score = sum(1 for keyword in satisfaction_keywords if keyword in text_lower)
        if satisfaction_score > 0:
            emotions['satisfaction'] = min(satisfaction_score * 0.25, 1.0)

        # Confusion indicators
        confusion_keywords = ['모르', '이해가 안', '헷갈', '어떻게', '무슨']
        confusion_score = sum(1 for keyword in confusion_keywords if keyword in text_lower)
        if confusion_score > 0:
            emotions['confusion'] = min(confusion_score * 0.25, 1.0)

        return emotions

    def _detect_urgency(self, text: str) -> List[str]:
        """
        Detect urgency indicators

        Returns:
            List of detected urgency indicators
        """
        indicators = []

        # Multiple exclamation marks
        if '!!' in text or '!!!' in text:
            indicators.append('multiple_exclamations')

        # All caps words (for English text)
        caps_words = re.findall(r'\b[A-Z]{3,}\b', text)
        if caps_words:
            indicators.append('caps_lock')

        # Urgent keywords
        urgent_keywords = ['긴급', '급해', '빨리', '시급', '즉시', 'urgent', 'asap', '어서']
        for keyword in urgent_keywords:
            if keyword in text.lower():
                indicators.append(f'keyword_{keyword}')

        # Time-related urgency
        time_keywords = ['오늘', '지금', '당장', '바로', 'today', 'now']
        for keyword in time_keywords:
            if keyword in text.lower():
                indicators.append(f'time_pressure_{keyword}')

        return indicators

    def _analyze_tone(self, text: str) -> str:
        """
        Analyze overall tone of the text

        Returns:
            Tone category
        """
        text_lower = text.lower()

        # Polite indicators
        polite_keywords = ['부탁', '감사', '고맙', '죄송', '미안', '실례', '괜찮으시', '주시']
        polite_count = sum(1 for keyword in polite_keywords if keyword in text_lower)

        # Aggressive indicators
        aggressive_keywords = ['빨리', '당장', '도대체', '왜', '못해', '안돼']
        aggressive_count = sum(1 for keyword in aggressive_keywords if keyword in text_lower)

        # Formal indicators (존댓말)
        formal_keywords = ['합니다', '습니다', '하십시오', '주십시오', '께서']
        formal_count = sum(1 for keyword in formal_keywords if keyword in text_lower)

        if aggressive_count > 2:
            return 'aggressive'
        elif polite_count > 2 or formal_count > 2:
            return 'polite'
        elif formal_count > 0:
            return 'formal'
        else:
            return 'neutral'

    def get_sentiment_trends(
        self,
        days: int = 7,
        category: Optional[str] = None
    ) -> Dict:
        """
        Get sentiment trends over time

        Args:
            days: Number of days to analyze
            category: Filter by category (optional)

        Returns:
            Sentiment trend data for visualization
        """
        start_date = datetime.utcnow() - timedelta(days=days)

        query = self.db.query(
            func.date(Inquiry.created_at).label('date'),
            Inquiry.sentiment,
            func.count(Inquiry.id).label('count')
        ).filter(
            Inquiry.created_at >= start_date
        )

        if category:
            query = query.filter(Inquiry.classified_category == category)

        results = query.group_by(
            func.date(Inquiry.created_at),
            Inquiry.sentiment
        ).all()

        # Organize data by date
        trend_data = {}
        for date, sentiment, count in results:
            date_str = str(date)
            if date_str not in trend_data:
                trend_data[date_str] = {
                    'positive': 0,
                    'negative': 0,
                    'neutral': 0,
                    'total': 0
                }

            trend_data[date_str][sentiment or 'neutral'] = count
            trend_data[date_str]['total'] += count

        # Convert to list format for charts
        chart_data = []
        for date_str in sorted(trend_data.keys()):
            data = trend_data[date_str]
            chart_data.append({
                'date': date_str,
                'positive': data['positive'],
                'negative': data['negative'],
                'neutral': data['neutral'],
                'total': data['total'],
                'positive_ratio': round(data['positive'] / data['total'], 2) if data['total'] > 0 else 0,
                'negative_ratio': round(data['negative'] / data['total'], 2) if data['total'] > 0 else 0
            })

        return {
            'daily_trends': chart_data,
            'period_summary': self._calculate_period_summary(chart_data)
        }

    def _calculate_period_summary(self, chart_data: List[Dict]) -> Dict:
        """Calculate summary statistics for the period"""
        if not chart_data:
            return {
                'total_inquiries': 0,
                'avg_positive_ratio': 0,
                'avg_negative_ratio': 0,
                'sentiment_trend': 'stable'
            }

        total_inquiries = sum(d['total'] for d in chart_data)
        total_positive = sum(d['positive'] for d in chart_data)
        total_negative = sum(d['negative'] for d in chart_data)

        avg_positive_ratio = total_positive / total_inquiries if total_inquiries > 0 else 0
        avg_negative_ratio = total_negative / total_inquiries if total_inquiries > 0 else 0

        # Determine trend (comparing first half vs second half)
        mid_point = len(chart_data) // 2
        first_half_negative = sum(d['negative_ratio'] for d in chart_data[:mid_point]) / max(mid_point, 1)
        second_half_negative = sum(d['negative_ratio'] for d in chart_data[mid_point:]) / max(len(chart_data) - mid_point, 1)

        if second_half_negative < first_half_negative - 0.1:
            sentiment_trend = 'improving'
        elif second_half_negative > first_half_negative + 0.1:
            sentiment_trend = 'declining'
        else:
            sentiment_trend = 'stable'

        return {
            'total_inquiries': total_inquiries,
            'avg_positive_ratio': round(avg_positive_ratio, 2),
            'avg_negative_ratio': round(avg_negative_ratio, 2),
            'sentiment_trend': sentiment_trend
        }

    def get_emotion_distribution(
        self,
        days: int = 7,
        category: Optional[str] = None
    ) -> Dict:
        """
        Get emotion distribution for visualization

        Args:
            days: Number of days to analyze
            category: Filter by category

        Returns:
            Emotion distribution data
        """
        start_date = datetime.utcnow() - timedelta(days=days)

        query = self.db.query(Inquiry).filter(
            Inquiry.created_at >= start_date
        )

        if category:
            query = query.filter(Inquiry.classified_category == category)

        inquiries = query.all()

        # Aggregate emotions
        emotion_counts = {}
        total_analyzed = 0

        for inquiry in inquiries:
            if inquiry.inquiry_text:
                analysis = self.analyze_inquiry_sentiment(inquiry.inquiry_text)
                total_analyzed += 1

                for emotion, score in analysis['emotions'].items():
                    if emotion not in emotion_counts:
                        emotion_counts[emotion] = 0
                    emotion_counts[emotion] += score

        # Calculate percentages
        emotion_distribution = []
        for emotion, total_score in emotion_counts.items():
            emotion_distribution.append({
                'emotion': emotion,
                'count': round(total_score, 1),
                'percentage': round((total_score / max(total_analyzed, 1)) * 100, 1)
            })

        # Sort by percentage
        emotion_distribution.sort(key=lambda x: x['percentage'], reverse=True)

        return {
            'emotions': emotion_distribution,
            'total_analyzed': total_analyzed,
            'period_days': days
        }

    def get_sentiment_by_category(self) -> List[Dict]:
        """
        Get sentiment distribution grouped by inquiry category

        Returns:
            Category-wise sentiment breakdown
        """
        results = self.db.query(
            Inquiry.classified_category,
            Inquiry.sentiment,
            func.count(Inquiry.id).label('count')
        ).filter(
            Inquiry.classified_category.isnot(None)
        ).group_by(
            Inquiry.classified_category,
            Inquiry.sentiment
        ).all()

        # Organize by category
        category_data = {}
        for category, sentiment, count in results:
            if category not in category_data:
                category_data[category] = {
                    'positive': 0,
                    'negative': 0,
                    'neutral': 0,
                    'total': 0
                }

            category_data[category][sentiment or 'neutral'] = count
            category_data[category]['total'] += count

        # Convert to list
        category_sentiment = []
        for category, data in category_data.items():
            category_sentiment.append({
                'category': category,
                'positive': data['positive'],
                'negative': data['negative'],
                'neutral': data['neutral'],
                'total': data['total'],
                'negative_ratio': round(data['negative'] / data['total'], 2) if data['total'] > 0 else 0
            })

        # Sort by negative ratio (problem categories first)
        category_sentiment.sort(key=lambda x: x['negative_ratio'], reverse=True)

        return category_sentiment

    def get_response_tone_analysis(self, days: int = 7) -> Dict:
        """
        Analyze tone effectiveness of responses

        Args:
            days: Number of days to analyze

        Returns:
            Response tone analysis
        """
        start_date = datetime.utcnow() - timedelta(days=days)

        responses = self.db.query(Response).filter(
            Response.created_at >= start_date,
            Response.status == 'approved'
        ).all()

        tone_stats = {
            'total_responses': len(responses),
            'avg_confidence': 0,
            'avg_length': 0,
            'tone_distribution': {}
        }

        if not responses:
            return tone_stats

        total_confidence = sum(r.confidence_score or 0 for r in responses)
        total_length = sum(len(r.response_text) if r.response_text else 0 for r in responses)

        tone_stats['avg_confidence'] = round(total_confidence / len(responses), 2)
        tone_stats['avg_length'] = round(total_length / len(responses), 0)

        # Analyze tone of responses
        for response in responses:
            if response.response_text:
                tone = self._analyze_tone(response.response_text)
                if tone not in tone_stats['tone_distribution']:
                    tone_stats['tone_distribution'][tone] = 0
                tone_stats['tone_distribution'][tone] += 1

        return tone_stats
