"""
Utility functions for the dashboard app.
"""
from datetime import date, timedelta
from typing import List, Union


def generate_date_range(start_date: date, end_date: date) -> List[date]:
    """Generate a list of dates between start_date and end_date (inclusive)."""
    date_list = []
    current_date = start_date
    
    while current_date <= end_date:
        date_list.append(current_date)
        current_date += timedelta(days=1)
    
    return date_list


def format_metric_value(value: float, format_type: str = 'decimal', precision: int = 1) -> str:
    """Format metric values for display."""
    if format_type == 'percentage':
        return f"{value:.{precision}f}%"
    elif format_type == 'decimal':
        return f"{value:.{precision}f}"
    elif format_type == 'integer':
        return str(round(value))
    else:
        return str(value)


def get_metric_color(value: float, metric_type: str) -> str:
    """Get color coding for metric values based on thresholds."""
    # Define thresholds for different metric types
    thresholds = {
        'productivity': {'good': 80, 'warning': 60},
        'sentiment': {'good': 4.0, 'warning': 3.0},
        'completion_rate': {'good': 80, 'warning': 60},
        'response_time': {'good': 1.0, 'warning': 3.0, 'reverse': True},  # Lower is better
    }
    
    if metric_type not in thresholds:
        return 'gray'
    
    threshold = thresholds[metric_type]
    reverse = threshold.get('reverse', False)
    
    if reverse:
        # For metrics where lower is better (e.g., response time)
        if value <= threshold['good']:
            return 'green'
        elif value <= threshold['warning']:
            return 'yellow'
        else:
            return 'red'
    else:
        # For metrics where higher is better (e.g., productivity)
        if value >= threshold['good']:
            return 'green'
        elif value >= threshold['warning']:
            return 'yellow'
        else:
            return 'red'


def calculate_percentage_change(current: float, previous: float) -> float:
    """Calculate percentage change between two values."""
    if previous == 0:
        return 0.0
    return ((current - previous) / previous) * 100


def aggregate_team_metrics(team_name: str, start_date: date, end_date: date) -> dict:
    """Aggregate metrics for a team over a date range."""
    from .models import TeamMetrics
    
    metrics = TeamMetrics.objects.filter(
        team_name=team_name,
        date__gte=start_date,
        date__lte=end_date
    )
    
    aggregated = {}
    for metric in metrics:
        if metric.metric_type not in aggregated:
            aggregated[metric.metric_type] = []
        aggregated[metric.metric_type].append(metric.value)
    
    # Calculate averages
    result = {}
    for metric_type, values in aggregated.items():
        result[metric_type] = {
            'average': sum(values) / len(values),
            'count': len(values),
            'min': min(values),
            'max': max(values)
        }
    
    return result
