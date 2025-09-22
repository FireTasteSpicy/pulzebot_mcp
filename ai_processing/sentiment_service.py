"""
Sentiment analysis service for AI processing.
"""
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import torch.nn.functional as F
from .utils import TextPreprocessor


class SentimentAnalysisService:
    """Service for sentiment analysis using BERT models."""

    def __init__(self):
        """Initialise the sentiment analysis service."""
        try:
            self.tokenizer = AutoTokenizer.from_pretrained('nlptown/bert-base-multilingual-uncased-sentiment')
            self.model = AutoModelForSequenceClassification.from_pretrained('nlptown/bert-base-multilingual-uncased-sentiment')
        except Exception:
            self.tokenizer = None
            self.model = None
        self.preprocessor = TextPreprocessor()

    def analyse_sentiment(self, text):
        """
        Analyse sentiment using BERT model with full 5-class analysis.
        """
        if not text or not self.tokenizer or not self.model:
            return None

        # Clean and preprocess text
        processed_text = self.preprocessor.process(text)
        
        # Skip if processed text is too short or empty
        if len(processed_text.strip()) < 10:
            return None
            
        inputs = self.tokenizer(processed_text, return_tensors="pt", truncation=True, padding=True, max_length=512)
        
        with torch.no_grad():
            outputs = self.model(**inputs)
            predictions = F.softmax(outputs.logits, dim=-1)
            
        predicted_class = torch.argmax(predictions, dim=-1).item()
        confidence = predictions[0][predicted_class].item()
        
        # Use full 5-class sentiment analysis for nuanced results
        sentiment_labels = ['Very Negative', 'Negative', 'Neutral', 'Positive', 'Very Positive']
        label = sentiment_labels[predicted_class]
        
        # Get all confidence scores for debugging
        all_scores = predictions[0].tolist()
        
        # Only filter out very low confidence predictions
        if confidence < 0.3:
            label = 'Neutral'
            predicted_class = 2  # Neutral index
        
        return {
            'sentiment': label,
            'confidence': confidence,
            'raw_scores': all_scores,
            'processed_text': processed_text
        }