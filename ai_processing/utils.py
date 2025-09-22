# ai_processing/utils.py
import os
import re
import tempfile

def process_demo_data(jira_data, github_data, sentiment_data):
    """Process and validate work context data"""
    
    if not all([jira_data, github_data, sentiment_data]):
        return None

    # Handle missing sprint_info with defaults
    sprint_info = jira_data.get("sprint_info", {
        "completed_story_points": 0,
        "total_story_points": 1,  # Avoid division by zero
        "team_velocity": 0
    })

    context = {
        "active_issues": len(jira_data.get("issues", [])),
        "open_prs": len([pr for pr in github_data.get("pull_requests", []) if pr.get("state") == "open"]),
        "sprint_progress": {
            "completion_rate": (sprint_info["completed_story_points"] / 
                              sprint_info["total_story_points"]) * 100,
            "velocity_trend": "on_track" if sprint_info["team_velocity"] >= 20 else "behind"
        },
        "risk_indicators": {
            "failed_checks": any(check == "failed" for pr in github_data.get("pull_requests", []) 
                               for check in pr.get("status_checks", {}).values()),
            "blockers_present": any(issue.get("blockers") for issue in jira_data.get("issues", [])),
            "negative_sentiment": sentiment_data.get("overall_sentiment") in ["Negative", "Very Negative"]
        }
    }
    
    return context

def format_text_for_display(text):
    """Format text for display purposes"""
    if not text:
        return ""
    return text.strip().replace('\n', ' ').replace('\r', '')

class AudioPreprocessor:
    """Simple audio preprocessor for basic file handling."""

    def __init__(self):
        # Simplified - no heavy audio processing dependencies
        self.available = False

    def validate_format(self, file_path):
        """Validate if the audio file format is supported based on extension."""
        if not os.path.exists(file_path):
            return False
        return file_path.lower().endswith(('.wav', '.mp3', '.m4a', '.flac'))

    def process(self, file_path, target_format='wav', sample_rate=16000):
        """
        Process an audio file - simplified version that just returns original file.
        Advanced audio processing has been removed to reduce dependencies.
        """
        # Return original file - advanced processing removed for simplicity
        return file_path

class TextPreprocessor:
    """Handles text preprocessing for technical terminology."""

    def __init__(self):
        self.technical_terms = {
            "k8s": "kubernetes",
            "pr": "pull request",
            "ci/cd": "continuous integration and continuous delivery",
        }

    def process(self, text):
        """
        Process text to clean, normalise, and replace technical shorthand with full terms.
        """
        if not text:
            return ""
        
        if text is None:
            return ""
        
        # Clean and normalise text
        processed = text.strip()
        processed = re.sub(r'\s+', ' ', processed)  # Replace multiple spaces with single space
        processed = re.sub(r'[!]+', '!', processed)  # Replace multiple exclamation marks
        processed = processed.lower()  # Convert to lowercase for consistency
        
        # Replace technical shorthand with full terms
        for shorthand, full_term in self.technical_terms.items():
            processed = re.sub(r'\b' + re.escape(shorthand) + r'\b', full_term, processed, flags=re.IGNORECASE)
        
        return processed
