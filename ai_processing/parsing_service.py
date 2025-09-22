"""
Standup Parsing Service - AI-powered text segmentation for standup updates.

This service takes raw transcription text and segments it into the three
key standup components: yesterday's work, today's plan, and blockers.
"""

import re
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class StandupParsingService:
    """
    AI-powered service to parse standup transcriptions into structured data.
    """
    
    def __init__(self):
        # Keywords that typically indicate each section
        self.yesterday_keywords = [
            'yesterday', 'last time', 'previously', 'finished', 'completed', 
            'worked on', 'did', 'accomplished', 'wrapped up', 'closed'
        ]
        self.today_keywords = [
            'today', 'now', 'next', 'will work', 'plan to', 'going to',
            'focus on', 'working on', 'starting', 'beginning'
        ]
        self.blocker_keywords = [
            'blocked', 'blocker', 'issue', 'problem', 'stuck', 'need help',
            'waiting for', 'dependency', 'challenge', 'obstacle', 'impediment'
        ]
    
    def parse_standup_transcription(self, transcription: str) -> Dict[str, str]:
        """
        Parse a standup transcription into yesterday, today, and blockers.
        """
        if not transcription or not transcription.strip():
            return {"yesterday": "", "today": "", "blockers": ""}
        
        try:
            # Clean and normalise the text
            text = self._normalise_text(transcription)
            
            # Split into sentences for analysis
            sentences = self._split_into_sentences(text)
            
            # Classify sentences into categories
            classified = self._classify_sentences(sentences)
            
            # Build the final result
            result = {
                "yesterday": self._join_sentences(classified.get('yesterday', [])),
                "today": self._join_sentences(classified.get('today', [])),
                "blockers": self._join_sentences(classified.get('blockers', []))
            }
            
            # If we couldn't classify anything, try a simpler approach
            if not any(result.values()):
                result = self._fallback_parsing(text)
            
            logger.info(f"Successfully parsed standup transcription into {len([k for k, v in result.items() if v])} sections")
            return result
            
        except Exception as e:
            logger.error(f"Error parsing standup transcription: {e}")
            # Return transcription as today's plan if parsing fails
            return {
                "yesterday": "",
                "today": transcription.strip(),
                "blockers": ""
            }
    
    def _normalise_text(self, text: str) -> str:
        """Clean and normalise the input text."""
        # Remove extra whitespace and normalise punctuation
        text = re.sub(r'\s+', ' ', text.strip())
        # Ensure sentences end with periods for better splitting
        text = re.sub(r'([a-z])(\s+[A-Z])', r'\1. \2', text)
        return text
    
    def _split_into_sentences(self, text: str) -> list:
        """Split text into individual sentences."""
        # More sophisticated sentence splitting that preserves sentence boundaries better
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _classify_sentences(self, sentences: list) -> Dict[str, list]:
        """Classify sentences into yesterday, today, and blockers categories."""
        classified = {'yesterday': [], 'today': [], 'blockers': []}
        
        current_category = None
        
        for sentence in sentences:
            sentence_lower = sentence.lower()
            
            # Check for explicit category indicators
            category = self._identify_category(sentence_lower)
            
            if category:
                current_category = category
                # Include the sentence if it has actual content beyond the keyword
                if self._has_content_beyond_keywords(sentence_lower, category):
                    classified[category].append(sentence)
                continue
            
            # If we have a current category, assign the sentence to it
            if current_category:
                classified[current_category].append(sentence)
            else:
                # Default assignment based on sentence content
                if any(keyword in sentence_lower for keyword in self.blocker_keywords):
                    classified['blockers'].append(sentence)
                elif any(keyword in sentence_lower for keyword in self.yesterday_keywords):
                    classified['yesterday'].append(sentence)
                else:
                    # Default to today if no clear indicators
                    classified['today'].append(sentence)
        
        return classified
    
    def _identify_category(self, sentence_lower: str) -> Optional[str]:
        """Identify if a sentence indicates a category transition."""
        if any(keyword in sentence_lower for keyword in self.yesterday_keywords):
            return 'yesterday'
        elif any(keyword in sentence_lower for keyword in self.today_keywords):
            return 'today'
        elif any(keyword in sentence_lower for keyword in self.blocker_keywords):
            return 'blockers'
        return None
    
    def _has_content_beyond_keywords(self, sentence_lower: str, category: str) -> bool:
        """Check if sentence has meaningful content beyond just category keywords."""
        # Get relevant keywords for the category
        if category == 'yesterday':
            keywords = self.yesterday_keywords
        elif category == 'today':
            keywords = self.today_keywords
        else:
            keywords = self.blocker_keywords
        
        # Remove keywords and common words to see if there's meaningful content
        words = sentence_lower.split()
        content_words = []
        for word in words:
            # Skip if word is a keyword or common connector
            if (not any(keyword in word for keyword in keywords) and 
                word not in ['i', 'am', 'was', 'will', 'be', 'by', 'the', 'a', 'an', 'and', 'or']):
                content_words.append(word)
        
        # Consider it meaningful if it has at least 2 content words
        return len(content_words) >= 2
    
    def _join_sentences(self, sentences: list) -> str:
        """Join sentences back into a coherent paragraph."""
        if not sentences:
            return ""
        
        # Clean up sentences and join them
        cleaned_sentences = []
        for sentence in sentences:
            # Remove extra periods and whitespace
            cleaned = sentence.strip().rstrip('.')
            if cleaned:
                cleaned_sentences.append(cleaned)
        
        if not cleaned_sentences:
            return ""
        
        return ". ".join(cleaned_sentences) + "."
    
    def _fallback_parsing(self, text: str) -> Dict[str, str]:
        """
        Fallback parsing method that uses simple heuristics.
        Splits text into roughly equal parts if no clear structure is found.
        """
        sentences = self._split_into_sentences(text)
        
        if len(sentences) <= 1:
            # Single sentence - put it in today
            return {"yesterday": "", "today": text, "blockers": ""}
        elif len(sentences) == 2:
            # Two sentences - first is yesterday, second is today
            return {
                "yesterday": sentences[0] + ".",
                "today": sentences[1] + ".",
                "blockers": ""
            }
        else:
            # Multiple sentences - distribute roughly evenly
            third = len(sentences) // 3
            return {
                "yesterday": self._join_sentences(sentences[:third]),
                "today": self._join_sentences(sentences[third:third*2]),
                "blockers": self._join_sentences(sentences[third*2:])
            }