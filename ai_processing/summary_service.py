"""
Summary generation service using Gemini AI.
"""
import os
import json
import re
from dotenv import load_dotenv
import google.generativeai as genai
from .utils import process_demo_data

# Load environment variables
load_dotenv()


class SummaryGenerationService:
    """Service for generating context-aware summaries using Gemini AI."""

    def __init__(self):
        """Initialise the summary generation service."""
        try:
            genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
            self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        except Exception as e:
            self.model = None
            print(f"Error initializing Gemini model: {e}")

    def validate_summary_format(self, text, expected_sentiment, expected_confidence):
        """
        Validate that the generated summary meets HTML formatting requirements.
        """
        if not text:
            return False, "Empty text"
        
        # Check required HTML bullet point format
        has_strategic_assessment = '<strong class="text-primary">Strategic Assessment:</strong>' in text
        has_strategic_context = '<strong class="text-primary">Strategic Context:</strong>' in text
        has_performance_patterns = '<strong class="text-primary">Performance Patterns:</strong>' in text
        has_individual_recommendations = 'Individual Recommendations' in text
        
        # Count HTML bullet points (should have at least 5 core sections)
        bullet_count = text.count('<div class="bullet-point">')
        
        # Check that it starts correctly with HTML
        starts_correctly = (
            text.strip().startswith('<strong class="text-primary">👤 Individual Performance Analysis</strong>') or
            text.strip().startswith('**👤 Individual Performance Analysis**')  # Accept markdown as fallback
        )
        
        # Check that sentiment analysis is NOT present (we don't want it in the AI output)
        has_unwanted_sentiment = 'Sentiment Analysis:' in text
        
        validation_results = {
            'starts_correctly': starts_correctly,
            'has_strategic_assessment': has_strategic_assessment,
            'has_strategic_context': has_strategic_context,
            'has_performance_patterns': has_performance_patterns,
            'has_individual_recommendations': has_individual_recommendations,
            'no_unwanted_sentiment': not has_unwanted_sentiment,
            'bullet_count': bullet_count,
            'bullet_count_ok': bullet_count >= 5
        }
        
        all_requirements_met = all([
            starts_correctly,
            has_strategic_assessment,
            has_strategic_context,
            has_performance_patterns,
            has_individual_recommendations,
            not has_unwanted_sentiment,
            bullet_count >= 5
        ])
        
        if not all_requirements_met:
            missing = [k for k, v in validation_results.items() if not v and k != 'bullet_count']
            return False, f"Missing: {missing}"
        
        return True, "Valid format"

    def generate_summary(self, context):
        """
        Generate summary with validation and retry logic.
        """
        if not context or not self.model:
            return None

        try:
            prompt = self.build_prompt(context)
        except Exception as e:
            print(f"Error building prompt: {e}")
            return None

        # Get expected sentiment for validation
        sentiment_data = context.get('sentiment_data', {})
        expected_sentiment = sentiment_data.get('overall_sentiment', 'Neutral')
        expected_confidence = sentiment_data.get('confidence', 0.5)

        # Try up to 3 times to get a properly formatted response
        for attempt in range(3):
            try:
                response = self.model.generate_content(prompt)
                text = getattr(response, 'text', None)
                if not text:
                    continue
                
                # Sanitise the output
                Sanitised_text = self.Sanitise_gemini_output(text)
                
                # Validate the format
                is_valid, validation_message = self.validate_summary_format(
                    Sanitised_text, expected_sentiment, expected_confidence
                )
                
                if is_valid:
                    return Sanitised_text
                else:
                    print(f"Attempt {attempt + 1}: Validation failed - {validation_message}")
                    if attempt < 2:  # Don't print for last attempt
                        print(f"Retrying with stronger prompt...")
                        # Add more emphasis to the prompt for retry
                        prompt += "\n\nREMINDER: YOU MUST FOLLOW THE EXACT BULLET POINT FORMAT WITH DASHES!"
                    
            except Exception as e:
                print(f"Attempt {attempt + 1}: Error generating summary: {e}")
                
        print("Failed to generate properly formatted summary after 3 attempts")
        return None

    def build_prompt(self, context):
        """
        Construct the Gemini prompt string, avoiding banned output patterns.
        """
        jira_data = context.get("jira_data")
        github_data = context.get("github_data")
        sentiment_data = context.get("sentiment_data")
        user_info = context.get("user_info", {})

        # Require all data sources to be present - no fallbacks
        if not all([jira_data, github_data, sentiment_data]):
            raise ValueError("Incomplete context for prompt building")

        processed_context = process_demo_data(jira_data, github_data, sentiment_data)
        if not processed_context:
            raise ValueError("Processed context unavailable")

        # Extract sentiment data explicitly for AI processing
        overall_sentiment = sentiment_data.get('overall_sentiment', 'neutral').replace('_', ' ').title()
        overall_confidence = sentiment_data.get('confidence', 0.5)
        
        # Extract user information
        username = user_info.get('username', 'unknown_user')
        user_display_name = user_info.get('first_name', username)
        if not user_display_name or user_display_name == username:
            user_display_name = user_info.get('full_name', username)
        
        individual_sentiments = []
        for update in sentiment_data.get('recent_updates', []):
            user_sentiment = update.get('sentiment', 'neutral').replace('_', ' ').title()
            user_confidence = update.get('confidence', 0.5)
            individual_sentiments.append(
                f"{update.get('user', 'Unknown')}: {user_sentiment} (confidence: {user_confidence:.2f})"
            )

        prompt = f"""
        You are an AI assistant providing individual performance analysis for a software developer.

        ## CRITICAL INSTRUCTIONS:
        - Do NOT generate team summaries, team assessments, or overall team analysis
        - Do NOT use phrases like "Strategic Team Standup Replacement Summary" or "Overall Team Assessment"
        - Start DIRECTLY with individual performance analysis
        - Analyse ONLY ONE USER from the provided data
        - Focus exclusively on the individual's work, sentiment, and performance

        ## CONTEXT DATA FOR INDIVIDUAL ANALYSIS:
        JIRA: {json.dumps(jira_data, indent=2)}
        GITHUB: {json.dumps(github_data, indent=2)}
        SENTIMENT: {json.dumps(sentiment_data, indent=2)}
        PROCESSED CONTEXT: {json.dumps(processed_context, indent=2)}

        ## USER INFORMATION (USE THESE EXACT VALUES):
        Username (internal): {username}
        Display Name (use in analysis): {user_display_name}
        
        CRITICAL: Always refer to the user by their display name "{user_display_name}" in your analysis, NOT by their username "{username}".

        ## INDIVIDUAL SENTIMENT DATA (USE THESE EXACT VALUES):
        Primary User Sentiment: {overall_sentiment}
        Primary User Confidence: {overall_confidence:.2f}
        
        IMPORTANT: Use the exact sentiment values above in your analysis, not neutral or 0.0!

        ## MANDATORY OUTPUT FORMAT (COPY THIS EXACTLY - USE HTML FORMAT):
        
        <strong class="text-primary">👤 Individual Performance Analysis</strong>
        
        <div class="bullet-point"><strong class="text-primary">Strategic Assessment:</strong> [summary focused solely on this individual user]</div>
        <div class="bullet-point"><strong class="text-primary">Strategic Context:</strong> [Analyse this user's work in relation to team goals and project outcomes]</div>
        <div class="bullet-point"><strong class="text-primary">Performance Patterns:</strong> [Identify trends in this user's work, productivity patterns, skill utilization]</div>
        <div class="bullet-point"><strong class="text-primary">Work Items Impact:</strong> [Analyse the strategic importance of this user's PRs/Issues/Tickets]</div>
        <div class="bullet-point"><strong class="text-primary">Risk Assessment:</strong> [Identify potential blockers, dependencies, or skill gaps for this user]</div>
        <div class="bullet-point"><strong class="text-primary">Growth Opportunities:</strong> [Suggest areas for improvement or skill development for this user]</div>

        <div class="bullet-point"><strong class="text-primary"><i class="fas fa-lightbulb text-success me-1"></i> Individual Recommendations</strong>:</div>
        <div class="bullet-point"><strong class="text-primary">Immediate Actions (Next 1-2 days):</strong> [Specific actions for this individual]</div>
        <div class="bullet-point"><strong class="text-primary">Skill Development (Next 1-2 weeks):</strong> [Learning opportunities for this person]</div>
        <div class="bullet-point"><strong class="text-primary">Career Growth (Next 1-2 months):</strong> [Development initiatives for this individual]</div>
        <div class="bullet-point"><strong class="text-primary">Support Needed:</strong> [Resources or assistance this person might need]</div>
        
        ## ABSOLUTELY CRITICAL FORMATTING RULES (FAILURE TO FOLLOW = REJECTION):
        1. USE EXACT HTML FORMAT: <div class="bullet-point"><strong class="text-primary">Section:</strong> content</div>
        2. Every section MUST be wrapped in <div class="bullet-point"> tags
        3. Section names MUST use <strong class="text-primary">Name:</strong> format
        4. NO markdown format, ONLY HTML with the exact CSS classes shown above
        5. DO NOT include sentiment analysis in the output (it's displayed separately)
        
        ## STRICT REQUIREMENTS:
        - **NO TEAM ANALYSIS** - do not generate any team-wide summaries or assessments
        - **INDIVIDUAL ONLY** - analyse only the primary user from the data
        - **START WITH INDIVIDUAL ANALYSIS** - begin immediately with "Individual Performance Analysis"
        - **NO SENTIMENT ANALYSIS** - do not include sentiment analysis in your output (it's displayed separately)
        - **DATA-DRIVEN** - base analysis on the provided GitHub/Jira/standup data for this user only
        - **ACTIONABLE INSIGHTS** - provide strategic and specific recommendations for this individual
        - **USE DISPLAY NAME** - refer to the user as "{user_display_name}" throughout your analysis, NOT as "{username}"
        - Do not mention other team members or users in the analysis
        - Do not place assessments or icons in parentheses after names
        - Do not reference sentiment scores or emotional states in your analysis
        """

        return prompt

    def Sanitise_gemini_output(self, text: str) -> str:
        """
        Clean and validate HTML output from Gemini model.
        """
        if not text:
            return ""

        cleaned = text
        
        # AGGRESSIVE REMOVAL: Find and extract ONLY the Individual Performance Analysis section
        # Look for the HTML Individual Performance Analysis marker first
        html_marker = r'<strong class="text-primary">👤 Individual Performance Analysis</strong>'
        match = re.search(html_marker, cleaned, flags=re.IGNORECASE)
        
        if match:
            # Extract everything from the HTML marker onwards
            cleaned = cleaned[match.start():]
        else:
            # If no HTML marker found, look for markdown markers and convert to HTML
            markdown_marker = r'\*\*👤 Individual Performance Analysis\*\*'
            match = re.search(markdown_marker, cleaned, flags=re.IGNORECASE)
            
            if match:
                # Extract from markdown marker and convert to HTML
                cleaned = cleaned[match.start():]
                cleaned = re.sub(r'\*\*👤 Individual Performance Analysis\*\*', 
                               '<strong class="text-primary">👤 Individual Performance Analysis</strong>', 
                               cleaned)
            else:
                # If no marker found, look for alternative markers
                alt_markers = [
                    r'Individual Performance Analysis',
                    r'### Individual Assessment',
                    r'Individual Assessment for'
                ]
                
                for marker in alt_markers:
                    match = re.search(marker, cleaned, flags=re.IGNORECASE)
                    if match:
                        # Add the proper HTML header and extract from there
                        cleaned = '<strong class="text-primary">👤 Individual Performance Analysis</strong>\n\n' + cleaned[match.start():]
                        break
                else:
                    print("Warning: No individual performance analysis marker found")
        
        # Remove any remaining team-wide analysis patterns (both HTML and markdown)
        patterns_to_remove = [
            r'<strong[^>]*>.*?Strategic Team Standup.*?</strong>.*?(?=<div|<strong|$)',
            r'<strong[^>]*>.*?Overall Team Assessment.*?</strong>.*?(?=<div|<strong|$)',
            r'\*\*Strategic Team Standup.*?\*\*[^\*]*',
            r'\*\*Overall Team Assessment\*\*[^\*]*',
            r'Strategic Team Standup Analysis[^\*]*',
            # Remove sentiment analysis lines (both HTML and markdown formats)
            r'<div class="bullet-point"><i class="fas fa-comment[^>]*>.*?Sentiment Analysis:.*?</div>',
            r'<div class="bullet-point">.*?Sentiment Analysis:.*?</div>',
            r'-?\s*💭?\s*\*?Sentiment Analysis:.*?(?=\n|$)',
            r'-?\s*\*\*?Sentiment Analysis\*\*?:.*?(?=\n|$)',
            r'📈.*Strategic Metadata.*',
            r'\{[^}]*"team_sentiment"[^}]*\}',
            r'Team Overall Sentiment:.*?\n',
            r'Team Overall Confidence:.*?\n',
            r'Sprint Progress:.*?(?=\*\*|<div|Individual|$)'
        ]
        
        for pattern in patterns_to_remove:
            cleaned = re.sub(pattern, '', cleaned, flags=re.DOTALL | re.IGNORECASE)
        
        # Convert any remaining markdown bullet points to HTML format
        lines = cleaned.split('\n')
        fixed_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Convert markdown bullet points to HTML divs
            if re.match(r'^-\s*\*\*([^*]+):\*\*(.*)$', line):
                match = re.match(r'^-\s*\*\*([^*]+):\*\*(.*)$', line)
                if match:
                    section_name = match.group(1).strip()
                    content = match.group(2).strip()
                    if '💡' in section_name:
                        line = f'<div class="bullet-point"><strong class="text-primary"><i class="fas fa-lightbulb text-success me-1"></i> {section_name.replace("💡", "").strip()}:</strong>{content}</div>'
                    else:
                        line = f'<div class="bullet-point"><strong class="text-primary">{section_name}:</strong>{content}</div>'
            
            # Handle sentiment analysis lines specially
            elif '💭' in line and 'Sentiment Analysis' in line:
                if not line.startswith('<div class="bullet-point">'):
                    # Convert markdown to HTML
                    line = re.sub(r'^-?\s*💭\s*\*([^*]+)\*(.*)$', 
                                r'<div class="bullet-point"><i class="fas fa-comment text-muted me-1"></i> <em>\1</em>\2</div>', 
                                line)
            
            # Fix any remaining markdown patterns
            elif line.startswith('- **') and not line.startswith('<div'):
                # Convert remaining markdown bullets to HTML
                match = re.match(r'^-\s*\*\*([^*]+):\*\*(.*)$', line)
                if match:
                    section_name = match.group(1).strip()
                    content = match.group(2).strip()
                    line = f'<div class="bullet-point"><strong class="text-primary">{section_name}:</strong>{content}</div>'
            
            # Keep HTML lines as they are
            elif line.startswith('<div class="bullet-point">') or line.startswith('<strong class="text-primary">'):
                pass  # Already in correct HTML format
            
            # Try to wrap unrecognized content that looks like bullet points
            elif line.startswith('**') and ':' in line:
                # Handle markdown headers without dashes
                match = re.match(r'^\*\*([^*]+):\*\*(.*)$', line)
                if match:
                    section_name = match.group(1).strip()
                    content = match.group(2).strip()
                    line = f'<div class="bullet-point"><strong class="text-primary">{section_name}:</strong>{content}</div>'
            
            if line:  # Only add non-empty lines
                fixed_lines.append(line)
        
        # Rejoin the lines
        cleaned = '\n'.join(fixed_lines)
        
        # Final cleanup - remove excessive whitespace
        cleaned = re.sub(r'\n\s*\n+', '\n', cleaned)
        cleaned = cleaned.strip()
        
        return cleaned