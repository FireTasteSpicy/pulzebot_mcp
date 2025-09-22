"""
Predictive Analytics and Learning Service
Advanced analytics, machine learning insights, and predictive modeling for team health and productivity.
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from django.utils import timezone
from config.demo_time import now as demo_now
from django.db.models import Q, Count, Avg, Min, Max
from collections import defaultdict, Counter
import re

from dashboard.models import StandupSession, Project, TeamMember, PipelineAnalytics, WorkItemReference


logger = logging.getLogger(__name__)


class PredictiveAnalyticsService:
    """
    Advanced analytics service providing predictive insights, learning from patterns,
    and sophisticated trend analysis for team health and productivity.
    """
    
    def __init__(self):
        self.sentiment_threshold_positive = 0.6
        self.sentiment_threshold_negative = 0.4
        self.productivity_baseline = 5.0  # 0-10 scale
        
    def generate_predictive_insights(self, project: Project, days_back: int = 60) -> Dict[str, Any]:
        """
        Generate comprehensive predictive insights for a project.
        """
        end_date = demo_now().date()
        start_date = end_date - timedelta(days=days_back)
        
        sessions = StandupSession.objects.filter(
            project=project,
            date__gte=start_date,
            status='completed'
        ).order_by('date')
        
        if sessions.count() < 7:
            return {
                'error': 'Insufficient data for predictive analysis',
                'minimum_sessions_required': 7,
                'current_sessions': sessions.count()
            }
        
        insights = {
            'project_id': project.id,
            'project_name': project.name,
            'analysis_period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'sessions_analysed': sessions.count()
            },
            'predictive_models': {},
            'risk_assessment': {},
            'recommendations': [],
            'confidence_scores': {},
            'generated_at': demo_now().isoformat()
        }
        
        try:
            # Sentiment prediction model
            sentiment_prediction = self._predict_sentiment_trends(sessions)
            insights['predictive_models']['sentiment'] = sentiment_prediction
            
            # Productivity prediction model
            productivity_prediction = self._predict_productivity_trends(sessions)
            insights['predictive_models']['productivity'] = productivity_prediction
            
            # Blocker pattern prediction
            blocker_prediction = self._predict_blocker_patterns(sessions)
            insights['predictive_models']['blockers'] = blocker_prediction
            
            # Team velocity prediction
            velocity_prediction = self._predict_team_velocity(sessions)
            insights['predictive_models']['velocity'] = velocity_prediction
            
            # Risk assessment
            risk_assessment = self._assess_team_risks(sessions)
            insights['risk_assessment'] = risk_assessment
            
            # Generate actionable recommendations
            recommendations = self._generate_recommendations(
                sentiment_prediction, productivity_prediction, blocker_prediction, risk_assessment
            )
            insights['recommendations'] = recommendations
            
            # Calculate confidence scores
            confidence_scores = self._calculate_confidence_scores(sessions, insights['predictive_models'])
            insights['confidence_scores'] = confidence_scores
            
        except Exception as e:
            logger.error(f"Predictive analytics error for project {project.id}: {str(e)}")
            insights['error'] = str(e)
        
        return insights
    
    def _predict_sentiment_trends(self, sessions) -> Dict[str, Any]:
        """Predict sentiment trends using time series analysis."""
        
        # Extract sentiment data
        sentiment_data = []
        for session in sessions:
            if session.sentiment_score is not None:
                sentiment_data.append({
                    'date': session.date,
                    'score': float(session.sentiment_score),
                    'user': session.user.username
                })
        
        if len(sentiment_data) < 5:
            return {'error': 'Insufficient sentiment data for prediction'}
        
        # Group by date and calculate daily averages
        daily_sentiment = defaultdict(list)
        for data in sentiment_data:
            daily_sentiment[data['date']].append(data['score'])
        
        daily_averages = []
        dates = []
        for date, scores in daily_sentiment.items():
            daily_averages.append(sum(scores) / len(scores))
            dates.append(date)
        
        # Sort by date
        date_score_pairs = list(zip(dates, daily_averages))
        date_score_pairs.sort(key=lambda x: x[0])
        dates, daily_averages = zip(*date_score_pairs)
        
        # Simple linear regression for trend prediction
        trend_slope = self._calculate_trend_slope(list(range(len(daily_averages))), daily_averages)
        
        # Predict next 7 days
        future_predictions = []
        last_score = daily_averages[-1]
        for i in range(1, 8):
            predicted_score = last_score + (trend_slope * i)
            predicted_score = max(0.0, min(1.0, predicted_score))  # Clamp between 0 and 1
            future_predictions.append({
                'date': (dates[-1] + timedelta(days=i)).isoformat(),
                'predicted_sentiment': round(predicted_score, 3),
                'confidence': max(0.5, 1.0 - (i * 0.1))  # Decreasing confidence over time
            })
        
        # Analyse patterns
        recent_avg = sum(daily_averages[-7:]) / min(7, len(daily_averages))
        historical_avg = sum(daily_averages) / len(daily_averages)
        
        # Detect seasonal patterns (weekly cycles)
        weekly_pattern = self._detect_weekly_patterns(dates, daily_averages)
        
        return {
            'current_trend': 'improving' if trend_slope > 0.01 else 'declining' if trend_slope < -0.01 else 'stable',
            'trend_slope': round(trend_slope, 4),
            'recent_average': round(recent_avg, 3),
            'historical_average': round(historical_avg, 3),
            'future_predictions': future_predictions,
            'weekly_patterns': weekly_pattern,
            'volatility': round(self._calculate_volatility(daily_averages), 3),
            'data_points': len(daily_averages)
        }
    
    def _predict_productivity_trends(self, sessions) -> Dict[str, Any]:
        """Predict productivity trends based on work item references and content quality."""
        
        productivity_data = []
        for session in sessions:
            # Calculate productivity score
            work_items_count = session.work_item_refs.count()
            content_length = (
                len(session.yesterday_work or '') + 
                len(session.today_plan or '') + 
                len(session.blockers or '')
            )
            
            # Quality indicators
            has_specific_tasks = bool(re.search(r'\b(implement|fix|debug|review|test|deploy)\b', 
                                              (session.today_plan or '').lower()))
            has_quantifiable_goals = bool(re.search(r'\b(\d+|finish|complete|deliver)\b', 
                                                   (session.today_plan or '').lower()))
            mentions_collaboration = bool(re.search(r'\b(with|team|pair|review|meeting)\b', 
                                                   (session.yesterday_work or '').lower()))
            
            # Productivity score (0-10 scale)
            productivity_score = min(10, 
                (work_items_count * 2) +  # Work item references
                (content_length / 50) +   # Content depth
                (2 if has_specific_tasks else 0) +  # Task specificity
                (2 if has_quantifiable_goals else 0) +  # Goal clarity
                (1 if mentions_collaboration else 0)  # Team collaboration
            )
            
            productivity_data.append({
                'date': session.date,
                'score': productivity_score,
                'work_items': work_items_count,
                'content_length': content_length,
                'user': session.user.username
            })
        
        if len(productivity_data) < 5:
            return {'error': 'Insufficient productivity data for prediction'}
        
        # Group by date and calculate daily averages
        daily_productivity = defaultdict(list)
        for data in productivity_data:
            daily_productivity[data['date']].append(data['score'])
        
        daily_averages = []
        dates = []
        for date, scores in daily_productivity.items():
            daily_averages.append(sum(scores) / len(scores))
            dates.append(date)
        
        # Sort by date
        date_score_pairs = list(zip(dates, daily_averages))
        date_score_pairs.sort(key=lambda x: x[0])
        dates, daily_averages = zip(*date_score_pairs)
        
        # Calculate trend
        trend_slope = self._calculate_trend_slope(list(range(len(daily_averages))), daily_averages)
        
        # Predict future productivity
        future_predictions = []
        last_score = daily_averages[-1]
        for i in range(1, 8):
            predicted_score = last_score + (trend_slope * i)
            predicted_score = max(0.0, min(10.0, predicted_score))
            future_predictions.append({
                'date': (dates[-1] + timedelta(days=i)).isoformat(),
                'predicted_productivity': round(predicted_score, 2),
                'confidence': max(0.4, 1.0 - (i * 0.12))
            })
        
        # Identify productivity patterns
        peak_productivity_day = self._find_peak_day(dates, daily_averages)
        low_productivity_indicators = self._identify_low_productivity_patterns(productivity_data)
        
        return {
            'current_trend': 'improving' if trend_slope > 0.1 else 'declining' if trend_slope < -0.1 else 'stable',
            'trend_slope': round(trend_slope, 3),
            'average_productivity': round(sum(daily_averages) / len(daily_averages), 2),
            'baseline_comparison': round((sum(daily_averages[-7:]) / 7) - self.productivity_baseline, 2),
            'future_predictions': future_predictions,
            'peak_productivity_day': peak_productivity_day,
            'low_productivity_indicators': low_productivity_indicators,
            'data_points': len(daily_averages)
        }
    
    def _predict_blocker_patterns(self, sessions) -> Dict[str, Any]:
        """Predict blocker patterns and recurring issues."""
        
        blocker_sessions = sessions.filter(blockers__isnull=False).exclude(blockers='')
        
        if blocker_sessions.count() < 3:
            return {'error': 'Insufficient blocker data for pattern analysis'}
        
        # Extract and analyse blocker text
        blocker_texts = [session.blockers.lower() for session in blocker_sessions]
        all_blocker_text = ' '.join(blocker_texts)
        
        # Categorize blockers
        blocker_categories = self._categorize_blockers(blocker_texts)
        
        # Temporal pattern analysis
        blocker_timeline = []
        for session in blocker_sessions:
            blocker_timeline.append({
                'date': session.date,
                'user': session.user.username,
                'blocker_text': session.blockers,
                'categories': blocker_categories.get(session.blockers, [])
            })
        
        # Predict blocker probability
        recent_days = 14
        recent_sessions = sessions.filter(date__gte=demo_now().date() - timedelta(days=recent_days))
        recent_blocker_rate = recent_sessions.filter(blockers__isnull=False).exclude(blockers='').count() / max(recent_sessions.count(), 1)
        
        # Weekly pattern analysis
        blocker_by_weekday = defaultdict(int)
        total_by_weekday = defaultdict(int)
        
        for session in sessions:
            weekday = session.date.weekday()  # 0=Monday, 6=Sunday
            total_by_weekday[weekday] += 1
            if session.blockers and session.blockers.strip():
                blocker_by_weekday[weekday] += 1
        
        weekday_patterns = {}
        for weekday in range(7):
            weekday_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            if total_by_weekday[weekday] > 0:
                blocker_rate = blocker_by_weekday[weekday] / total_by_weekday[weekday]
                weekday_patterns[weekday_names[weekday]] = {
                    'blocker_rate': round(blocker_rate, 3),
                    'total_sessions': total_by_weekday[weekday]
                }
        
        # Predict next week's blocker probability
        next_week_predictions = []
        for i in range(7):
            next_date = demo_now().date() + timedelta(days=i+1)
            weekday = next_date.weekday()
            weekday_name = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][weekday]
            
            if weekday_name in weekday_patterns:
                predicted_probability = weekday_patterns[weekday_name]['blocker_rate']
            else:
                predicted_probability = recent_blocker_rate
            
            next_week_predictions.append({
                'date': next_date.isoformat(),
                'weekday': weekday_name,
                'blocker_probability': round(predicted_probability, 3),
                'risk_level': 'high' if predicted_probability > 0.4 else 'medium' if predicted_probability > 0.2 else 'low'
            })
        
        return {
            'overall_blocker_rate': round(blocker_sessions.count() / sessions.count(), 3),
            'recent_blocker_rate': round(recent_blocker_rate, 3),
            'blocker_categories': dict(Counter([cat for cats in blocker_categories.values() for cat in cats])),
            'weekday_patterns': weekday_patterns,
            'next_week_predictions': next_week_predictions,
            'recurring_patterns': self._find_recurring_blocker_patterns(blocker_texts),
            'total_blocker_sessions': blocker_sessions.count()
        }
    
    def _predict_team_velocity(self, sessions) -> Dict[str, Any]:
        """Predict team velocity based on work item completion and standup consistency."""
        
        # Calculate team velocity metrics
        velocity_data = []
        
        # Group sessions by week
        weekly_data = defaultdict(list)
        for session in sessions:
            week_start = session.date - timedelta(days=session.date.weekday())
            weekly_data[week_start].append(session)
        
        for week_start, week_sessions in weekly_data.items():
            if len(week_sessions) < 2:  # Skip weeks with too few sessions
                continue
                
            # Calculate weekly metrics
            total_work_items = sum(session.work_item_refs.count() for session in week_sessions)
            unique_users = len(set(session.user for session in week_sessions))
            avg_sentiment = sum(session.sentiment_score or 0.5 for session in week_sessions) / len(week_sessions)
            
            # Estimate completed work (this would be better with actual completion data)
            estimated_completed = total_work_items * 0.7  # Assume 70% completion rate
            
            velocity_data.append({
                'week_start': week_start,
                'sessions_count': len(week_sessions),
                'unique_contributors': unique_users,
                'work_items_referenced': total_work_items,
                'estimated_completed': estimated_completed,
                'avg_sentiment': avg_sentiment,
                'velocity_score': estimated_completed * avg_sentiment  # Weighted by team mood
            })
        
        if len(velocity_data) < 3:
            return {'error': 'Insufficient data for velocity prediction'}
        
        # Sort by week
        velocity_data.sort(key=lambda x: x['week_start'])
        
        # Calculate trend
        velocity_scores = [week['velocity_score'] for week in velocity_data]
        velocity_trend = self._calculate_trend_slope(list(range(len(velocity_scores))), velocity_scores)
        
        # Predict next 2 weeks
        last_velocity = velocity_scores[-1]
        future_velocity = []
        for i in range(1, 3):
            predicted_velocity = last_velocity + (velocity_trend * i)
            predicted_velocity = max(0, predicted_velocity)
            
            next_week_start = velocity_data[-1]['week_start'] + timedelta(weeks=i)
            future_velocity.append({
                'week_start': next_week_start.isoformat(),
                'predicted_velocity': round(predicted_velocity, 2),
                'confidence': max(0.3, 1.0 - (i * 0.2))
            })
        
        # Calculate velocity stability
        velocity_volatility = self._calculate_volatility(velocity_scores)
        
        return {
            'current_velocity': round(velocity_scores[-1], 2),
            'velocity_trend': 'improving' if velocity_trend > 0.1 else 'declining' if velocity_trend < -0.1 else 'stable',
            'average_velocity': round(sum(velocity_scores) / len(velocity_scores), 2),
            'velocity_volatility': round(velocity_volatility, 3),
            'future_predictions': future_velocity,
            'weekly_data': [{
                'week_start': week['week_start'].isoformat(),
                'velocity_score': round(week['velocity_score'], 2),
                'contributors': week['unique_contributors'],
                'work_items': week['work_items_referenced']
            } for week in velocity_data[-4:]],  # Last 4 weeks
            'data_points': len(velocity_data)
        }
    
    def _assess_team_risks(self, sessions) -> Dict[str, Any]:
        """Assess various team health and productivity risks."""
        
        recent_sessions = sessions.filter(date__gte=demo_now().date() - timedelta(days=14))
        
        risks = {
            'sentiment_risk': self._assess_sentiment_risk(recent_sessions),
            'productivity_risk': self._assess_productivity_risk(recent_sessions),
            'communication_risk': self._assess_communication_risk(recent_sessions),
            'workload_risk': self._assess_workload_risk(recent_sessions),
            'consistency_risk': self._assess_consistency_risk(recent_sessions)
        }
        
        # Calculate overall risk score
        risk_scores = [risk['score'] for risk in risks.values() if 'score' in risk]
        overall_risk = sum(risk_scores) / len(risk_scores) if risk_scores else 0
        
        return {
            'overall_risk_score': round(overall_risk, 2),
            'risk_level': 'high' if overall_risk > 0.7 else 'medium' if overall_risk > 0.4 else 'low',
            'individual_risks': risks,
            'risk_factors': self._identify_risk_factors(risks),
            'assessment_date': demo_now().isoformat()
        }
    
    def _assess_sentiment_risk(self, sessions) -> Dict[str, Any]:
        """Assess risk based on sentiment trends."""
        sentiment_scores = [s.sentiment_score for s in sessions if s.sentiment_score is not None]
        
        if not sentiment_scores:
            return {'score': 0.5, 'reason': 'No sentiment data available'}
        
        avg_sentiment = sum(sentiment_scores) / len(sentiment_scores)
        negative_sessions = sum(1 for score in sentiment_scores if score < self.sentiment_threshold_negative)
        negative_ratio = negative_sessions / len(sentiment_scores)
        
        # Risk increases with low average sentiment and high negative ratio
        risk_score = max(0, min(1, (1 - avg_sentiment) + negative_ratio))
        
        return {
            'score': round(risk_score, 3),
            'average_sentiment': round(avg_sentiment, 3),
            'negative_sessions_ratio': round(negative_ratio, 3),
            'trend': 'concerning' if risk_score > 0.6 else 'moderate' if risk_score > 0.3 else 'good'
        }
    
    def _assess_productivity_risk(self, sessions) -> Dict[str, Any]:
        """Assess risk based on productivity indicators."""
        total_sessions = sessions.count()
        
        if total_sessions == 0:
            return {'score': 0.5, 'reason': 'No session data available'}
        
        # Count sessions with minimal content
        minimal_content_sessions = 0
        no_work_items_sessions = 0
        
        for session in sessions:
            content_length = len((session.yesterday_work or '') + (session.today_plan or ''))
            if content_length < 50:  # Very short updates
                minimal_content_sessions += 1
            
            if session.work_item_refs.count() == 0:
                no_work_items_sessions += 1
        
        minimal_ratio = minimal_content_sessions / total_sessions
        no_items_ratio = no_work_items_sessions / total_sessions
        
        # Risk increases with high ratios of minimal content
        risk_score = (minimal_ratio + no_items_ratio) / 2
        
        return {
            'score': round(risk_score, 3),
            'minimal_content_ratio': round(minimal_ratio, 3),
            'no_work_items_ratio': round(no_items_ratio, 3),
            'trend': 'concerning' if risk_score > 0.6 else 'moderate' if risk_score > 0.3 else 'good'
        }
    
    def _assess_communication_risk(self, sessions) -> Dict[str, Any]:
        """Assess risk based on communication patterns."""
        total_sessions = sessions.count()
        unique_users = sessions.values('user').distinct().count()
        
        if total_sessions == 0 or unique_users == 0:
            return {'score': 0.5, 'reason': 'Insufficient data'}
        
        # Calculate participation consistency
        user_session_counts = defaultdict(int)
        for session in sessions:
            user_session_counts[session.user.username] += 1
        
        # Risk if participation is uneven or too low
        max_possible_sessions = 10  # Assume 2 weeks of workdays
        avg_participation = sum(user_session_counts.values()) / len(user_session_counts)
        participation_rate = avg_participation / max_possible_sessions
        
        # Risk increases with low participation
        risk_score = max(0, min(1, 1 - participation_rate))
        
        return {
            'score': round(risk_score, 3),
            'participation_rate': round(participation_rate, 3),
            'unique_contributors': unique_users,
            'avg_sessions_per_user': round(avg_participation, 1),
            'trend': 'concerning' if risk_score > 0.6 else 'moderate' if risk_score > 0.3 else 'good'
        }
    
    def _assess_workload_risk(self, sessions) -> Dict[str, Any]:
        """Assess risk based on workload indicators."""
        blocker_sessions = sessions.filter(blockers__isnull=False).exclude(blockers='')
        total_sessions = sessions.count()
        
        if total_sessions == 0:
            return {'score': 0.5, 'reason': 'No session data'}
        
        blocker_ratio = blocker_sessions.count() / total_sessions
        
        # Analyse blocker severity
        high_stress_indicators = 0
        for session in blocker_sessions:
            blocker_text = (session.blockers or '').lower()
            if any(word in blocker_text for word in ['urgent', 'critical', 'stuck', 'blocked', 'frustrated', 'overwhelmed']):
                high_stress_indicators += 1
        
        stress_ratio = high_stress_indicators / max(total_sessions, 1)
        
        # Risk increases with high blocker frequency and stress indicators
        risk_score = min(1, blocker_ratio + stress_ratio)
        
        return {
            'score': round(risk_score, 3),
            'blocker_frequency': round(blocker_ratio, 3),
            'stress_indicators': high_stress_indicators,
            'stress_ratio': round(stress_ratio, 3),
            'trend': 'concerning' if risk_score > 0.5 else 'moderate' if risk_score > 0.25 else 'good'
        }
    
    def _assess_consistency_risk(self, sessions) -> Dict[str, Any]:
        """Assess risk based on standup consistency."""
        # Check for gaps in standup submissions
        dates = [session.date for session in sessions.order_by('date')]
        
        if len(dates) < 2:
            return {'score': 0.5, 'reason': 'Insufficient date range'}
        
        # Calculate expected vs actual sessions
        date_range = (dates[-1] - dates[0]).days + 1
        workdays = sum(1 for i in range(date_range) if (dates[0] + timedelta(days=i)).weekday() < 5)
        
        consistency_ratio = len(dates) / max(workdays, 1)
        
        # Risk increases with low consistency
        risk_score = max(0, min(1, 1 - consistency_ratio))
        
        return {
            'score': round(risk_score, 3),
            'consistency_ratio': round(consistency_ratio, 3),
            'sessions_submitted': len(dates),
            'expected_workdays': workdays,
            'trend': 'concerning' if risk_score > 0.4 else 'moderate' if risk_score > 0.2 else 'good'
        }
    
    def _identify_risk_factors(self, risks: Dict) -> List[str]:
        """Identify the top risk factors for the team."""
        risk_factors = []
        
        for risk_name, risk_data in risks.items():
            if risk_data.get('score', 0) > 0.5:
                risk_factors.append(f"High {risk_name.replace('_', ' ')}: {risk_data.get('trend', 'unknown')}")
        
        return risk_factors
    
    def _generate_recommendations(self, sentiment_pred: Dict, productivity_pred: Dict, 
                                blocker_pred: Dict, risk_assessment: Dict) -> List[Dict[str, Any]]:
        """Generate actionable recommendations based on predictive analysis."""
        recommendations = []
        
        # Sentiment-based recommendations
        if sentiment_pred.get('current_trend') == 'declining':
            recommendations.append({
                'category': 'Team Morale',
                'priority': 'high',
                'recommendation': 'Schedule team building activities or retrospective to address declining sentiment',
                'rationale': f"Sentiment trend is declining with slope {sentiment_pred.get('trend_slope', 0)}",
                'expected_impact': 'Improve team morale and communication',
                'timeline': '1-2 weeks'
            })
        
        # Productivity-based recommendations
        if productivity_pred.get('current_trend') == 'declining':
            recommendations.append({
                'category': 'Productivity',
                'priority': 'medium',
                'recommendation': 'Review current processes and identify bottlenecks in team workflow',
                'rationale': f"Productivity trend is declining with baseline comparison {productivity_pred.get('baseline_comparison', 0)}",
                'expected_impact': 'Restore productivity levels and improve efficiency',
                'timeline': '2-3 weeks'
            })
        
        # Blocker-based recommendations
        if blocker_pred.get('overall_blocker_rate', 0) > 0.3:
            high_risk_days = [pred for pred in blocker_pred.get('next_week_predictions', []) 
                            if pred.get('risk_level') == 'high']
            if high_risk_days:
                recommendations.append({
                    'category': 'Blocker Prevention',
                    'priority': 'high',
                    'recommendation': f"Proactive planning for {', '.join([pred['weekday'] for pred in high_risk_days])} - high blocker risk days",
                    'rationale': f"Historical data shows {blocker_pred.get('overall_blocker_rate', 0):.1%} blocker rate",
                    'expected_impact': 'Reduce blocker frequency and team frustration',
                    'timeline': 'Immediate'
                })
        
        # Risk-based recommendations
        overall_risk = risk_assessment.get('overall_risk_score', 0)
        if overall_risk > 0.6:
            recommendations.append({
                'category': 'Risk Mitigation',
                'priority': 'high',
                'recommendation': 'Implement immediate team health interventions and increase check-in frequency',
                'rationale': f"Overall risk score is {overall_risk:.2f} indicating high team health risk",
                'expected_impact': 'Prevent team burnout and maintain productivity',
                'timeline': 'Immediate'
            })
        
        # Add positive reinforcement recommendations
        if sentiment_pred.get('current_trend') == 'improving' and productivity_pred.get('current_trend') == 'improving':
            recommendations.append({
                'category': 'Positive Reinforcement',
                'priority': 'low',
                'recommendation': 'Recognize and celebrate the team\'s positive momentum in upcoming meetings',
                'rationale': 'Both sentiment and productivity trends are improving',
                'expected_impact': 'Maintain positive team dynamics and motivation',
                'timeline': 'Next team meeting'
            })
        
        return recommendations
    
    def _calculate_confidence_scores(self, sessions, predictive_models: Dict) -> Dict[str, float]:
        """Calculate confidence scores for each predictive model."""
        total_sessions = sessions.count()
        date_range = (sessions.last().date - sessions.first().date).days if sessions.count() > 1 else 1
        
        base_confidence = min(1.0, total_sessions / 30)  # More data = higher confidence
        recency_factor = min(1.0, 30 / max(date_range, 1))  # Recent data = higher confidence
        
        confidence_scores = {}
        
        for model_name, model_data in predictive_models.items():
            if model_data.get('error'):
                confidence_scores[model_name] = 0.0
            else:
                # Model-specific confidence adjustments
                model_confidence = base_confidence * recency_factor
                
                if model_name == 'sentiment':
                    data_points = model_data.get('data_points', 0)
                    model_confidence *= min(1.0, data_points / 20)
                elif model_name == 'productivity':
                    data_points = model_data.get('data_points', 0)
                    model_confidence *= min(1.0, data_points / 15)
                elif model_name == 'blockers':
                    blocker_sessions = model_data.get('total_blocker_sessions', 0)
                    model_confidence *= min(1.0, blocker_sessions / 10)
                elif model_name == 'velocity':
                    data_points = model_data.get('data_points', 0)
                    model_confidence *= min(1.0, data_points / 8)
                
                confidence_scores[model_name] = round(model_confidence, 3)
        
        return confidence_scores
    
    # Helper methods for statistical calculations
    
    def _calculate_trend_slope(self, x_values: List[float], y_values: List[float]) -> float:
        """Calculate linear regression slope for trend analysis."""
        if len(x_values) != len(y_values) or len(x_values) < 2:
            return 0.0
        
        n = len(x_values)
        sum_x = sum(x_values)
        sum_y = sum(y_values)
        sum_xy = sum(x * y for x, y in zip(x_values, y_values))
        sum_x_squared = sum(x * x for x in x_values)
        
        denominator = n * sum_x_squared - sum_x * sum_x
        if denominator == 0:
            return 0.0
        
        slope = (n * sum_xy - sum_x * sum_y) / denominator
        return slope
    
    def _calculate_volatility(self, values: List[float]) -> float:
        """Calculate volatility (standard deviation) of a series."""
        if len(values) < 2:
            return 0.0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance ** 0.5
    
    def _detect_weekly_patterns(self, dates: List, values: List[float]) -> Dict[str, float]:
        """Detect weekly patterns in data."""
        weekday_values = defaultdict(list)
        
        for date, value in zip(dates, values):
            weekday = date.weekday()
            weekday_values[weekday].append(value)
        
        weekday_averages = {}
        weekday_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        for weekday, values_list in weekday_values.items():
            if values_list:
                weekday_averages[weekday_names[weekday]] = round(sum(values_list) / len(values_list), 3)
        
        return weekday_averages
    
    def _find_peak_day(self, dates: List, values: List[float]) -> str:
        """Find the day of week with highest average values."""
        weekday_patterns = self._detect_weekly_patterns(dates, values)
        
        if not weekday_patterns:
            return 'Unknown'
        
        peak_day = max(weekday_patterns.items(), key=lambda x: x[1])
        return peak_day[0]
    
    def _identify_low_productivity_patterns(self, productivity_data: List[Dict]) -> List[str]:
        """Identify patterns associated with low productivity."""
        patterns = []
        
        low_productivity_sessions = [data for data in productivity_data if data['score'] < 3.0]
        
        if not low_productivity_sessions:
            return patterns
        
        # Analyse common characteristics
        avg_content_length = sum(data['content_length'] for data in low_productivity_sessions) / len(low_productivity_sessions)
        avg_work_items = sum(data['work_items'] for data in low_productivity_sessions) / len(low_productivity_sessions)
        
        if avg_content_length < 100:
            patterns.append(f"Short standup updates (avg {avg_content_length:.0f} characters)")
        
        if avg_work_items < 1:
            patterns.append(f"Few work item references (avg {avg_work_items:.1f} items)")
        
        # Day of week analysis
        weekday_counts = defaultdict(int)
        for data in low_productivity_sessions:
            weekday_counts[data['date'].weekday()] += 1
        
        if weekday_counts:
            most_common_weekday = max(weekday_counts.items(), key=lambda x: x[1])
            weekday_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            patterns.append(f"Most common on {weekday_names[most_common_weekday[0]]}")
        
        return patterns
    
    def _categorize_blockers(self, blocker_texts: List[str]) -> Dict[str, List[str]]:
        """Categorize blockers by type."""
        categories = {
            'technical': ['bug', 'error', 'broken', 'failing', 'crash', 'issue', 'problem'],
            'dependency': ['waiting', 'blocked by', 'depends on', 'pending', 'approval'],
            'resource': ['access', 'permission', 'account', 'credentials', 'server'],
            'knowledge': ['unclear', 'understand', 'documentation', 'help', 'guidance'],
            'process': ['review', 'meeting', 'decision', 'policy', 'procedure']
        }
        
        blocker_categories = {}
        
        for blocker_text in blocker_texts:
            text_categories = []
            for category, keywords in categories.items():
                if any(keyword in blocker_text for keyword in keywords):
                    text_categories.append(category)
            
            if not text_categories:
                text_categories = ['other']
            
            blocker_categories[blocker_text] = text_categories
        
        return blocker_categories
    
    def _find_recurring_blocker_patterns(self, blocker_texts: List[str]) -> List[Dict[str, Any]]:
        """Find recurring patterns in blocker descriptions."""
        # Simple keyword frequency analysis
        word_counts = defaultdict(int)
        
        for text in blocker_texts:
            words = re.findall(r'\b\w{4,}\b', text.lower())  # Words with 4+ characters
            for word in words:
                if word not in ['with', 'from', 'this', 'that', 'have', 'been', 'were', 'will']:
                    word_counts[word] += 1
        
        # Find words mentioned multiple times
        recurring_patterns = []
        for word, count in word_counts.items():
            if count >= 2:
                recurring_patterns.append({
                    'pattern': word,
                    'frequency': count,
                    'type': 'keyword'
                })
        
        # Sort by frequency
        recurring_patterns.sort(key=lambda x: x['frequency'], reverse=True)
        
        return recurring_patterns[:5]  # Top 5 patterns
