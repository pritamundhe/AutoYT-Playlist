"""
Simplified NLP processor that uses pre-trained models from Kaggle
No heavy dependencies - just loads pickled models
"""
import re
import pickle
import json
from typing import List, Dict, Optional
from pathlib import Path



# Hack to allow unpickling of TopicExtractor if it was saved in __main__ (Jupyter Notebooks)
if '__main__' in sys.modules:
    pass
else:
    # We delay this assignment until the class is actually defined below, or we assume the class definition follows.
    # However, Python executes sequentially. We can't assign it before it's defined.
    # So we should put this AFTER the class definition.
    pass

class TopicExtractor:
    """Extract topics using pre-trained models (trained on Kaggle)"""
    
    def __init__(self, model_path: str = "ml_models/nlp/topic_extractor.pkl"):
        """Initialize with pre-trained model"""
        self.model_path = Path(model_path)
        self.model = None
        
        # Try to load pre-trained model
        if self.model_path.exists():
            with open(self.model_path, 'rb') as f:
                self.model = pickle.load(f)
            print(f"Loaded pre-trained model from {model_path}")
        else:
            print(f"Warning: No pre-trained model found at {model_path}")
            print("Using rule-based fallback")
    
    def extract_topics(self, text: str, max_depth: int = 3, min_keywords: int = 3) -> Dict:
        """
        Extract hierarchical topics from text
        
        If model is available, use it. Otherwise, use simple rule-based extraction.
        """
        if self.model:
            # Use pre-trained model
            return self._extract_with_model(text, max_depth, min_keywords)
        else:
            # Fallback to rule-based extraction
            return self._extract_rule_based(text, max_depth, min_keywords)
    
    def _extract_with_model(self, text: str, max_depth: int, min_keywords: int) -> Dict:
        """Extract using pre-trained model from Kaggle"""
        # The pickled model acts as the TopicExtractor instance
        # It returns a list of dictionaries: [{'number': '1', 'name': '...', 'subtopics': [...]}, ...]
        raw_topics = self.model.extract_topics(text)
        
        hierarchy = {'units': []}
        
        for item in raw_topics:
            unit = {
                'title': f"{item['type']} {item['number']}: {item['name']}",
                'level': 1,
                'keywords': self._extract_keywords_simple(item['name']),
                'topics': []
            }
            
            # Map subtopics to topics
            for subtopic_text in item.get('subtopics', []):
                topic = {
                    'title': subtopic_text,
                    'level': 2,
                    'keywords': self._extract_keywords_simple(subtopic_text),
                    'subtopics': []
                }
                unit['topics'].append(topic)
                
            hierarchy['units'].append(unit)
            
        return hierarchy
    
    def _extract_rule_based(self, text: str, max_depth: int, min_keywords: int) -> Dict:
        """
        Simple rule-based topic extraction (fallback)
        Looks for common academic patterns
        """
        hierarchy = {'units': []}
        
        # Split by common academic markers
        lines = text.split('\n')
        current_unit = None
        current_topic = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Detect units (Unit 1, Module 1, Chapter 1, etc.)
            unit_match = re.match(r'(?:Unit|Module|Chapter|Week)\s+(\d+)[:\s]+(.+)', line, re.IGNORECASE)
            if unit_match:
                if current_unit:
                    hierarchy['units'].append(current_unit)
                
                current_unit = {
                    'title': unit_match.group(2).strip(),
                    'level': 1,
                    'keywords': self._extract_keywords_simple(unit_match.group(2)),
                    'topics': []
                }
                current_topic = None
                continue
            
            # Detect topics (numbered or bulleted)
            topic_match = re.match(r'(?:\d+\.\d+|\d+\.|-|\*)\s+(.+)', line)
            if topic_match and current_unit:
                topic_text = topic_match.group(1).strip()
                if len(topic_text) > 5:  # Ignore very short lines
                    topic = {
                        'title': topic_text,
                        'level': 2,
                        'keywords': self._extract_keywords_simple(topic_text),
                        'subtopics': []
                    }
                    current_unit['topics'].append(topic)
        
        # Add last unit
        if current_unit:
            hierarchy['units'].append(current_unit)
        
        # If no structure found, create a single unit
        if not hierarchy['units']:
            hierarchy['units'].append({
                'title': 'Main Content',
                'level': 1,
                'keywords': self._extract_keywords_simple(text[:200]),
                'topics': []
            })
        
        return hierarchy
    
    def _extract_keywords_simple(self, text: str) -> List[str]:
        """
        Simple keyword extraction (fallback)
        Just extracts capitalized words and common terms
        """
        # Remove common words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for'}
        
        # Extract words
        words = re.findall(r'\b[A-Z][a-z]+\b|\b[a-z]{4,}\b', text)
        
        # Filter and deduplicate
        keywords = []
        seen = set()
        for word in words:
            word_lower = word.lower()
            if word_lower not in stop_words and word_lower not in seen:
                keywords.append(word_lower)
                seen.add(word_lower)
                if len(keywords) >= 10:
                    break
        
        return keywords[:10]


# Hack to allow unpickling of TopicExtractor
import sys
sys.modules['__main__'].TopicExtractor = TopicExtractor


class HierarchyBuilder:
    """Build and manage topic hierarchy"""
    
    @staticmethod
    def flatten_hierarchy(hierarchy: Dict) -> List[Dict]:
        """
        Flatten hierarchical structure to list
        """
        flat_topics = []
        
        for unit in hierarchy.get('units', []):
            unit_topic = {
                'title': unit['title'],
                'level': 1,
                'keywords': unit.get('keywords', []),
                'parent_id': None,
                'order_index': len(flat_topics)
            }
            flat_topics.append(unit_topic)
            unit_id = len(flat_topics) - 1
            
            for topic in unit.get('topics', []):
                topic_item = {
                    'title': topic['title'],
                    'level': 2,
                    'keywords': topic.get('keywords', []),
                    'parent_id': unit_id,
                    'order_index': len(flat_topics)
                }
                flat_topics.append(topic_item)
                topic_id = len(flat_topics) - 1
                
                for subtopic in topic.get('subtopics', []):
                    subtopic_item = {
                        'title': subtopic['title'],
                        'level': 3,
                        'keywords': subtopic.get('keywords', []),
                        'parent_id': topic_id,
                        'order_index': len(flat_topics)
                    }
                    flat_topics.append(subtopic_item)
        
        return flat_topics
