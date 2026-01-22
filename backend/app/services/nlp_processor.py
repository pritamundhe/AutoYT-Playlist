"""
NLP processing service for topic extraction using Sentence-BERT and spaCy
"""
import re
from typing import List, Dict, Tuple, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
import spacy
from sklearn.cluster import HDBSCAN
from keybert import KeyBERT
import yake
from rake_nltk import Rake


class TopicExtractor:
    """Extract topics from syllabus text using NLP"""
    
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """Initialize NLP models"""
        self.sentence_model = SentenceTransformer(model_name)
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            print("Downloading spaCy model...")
            import subprocess
            subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"])
            self.nlp = spacy.load("en_core_web_sm")
        
        self.keyword_extractor = KeyBERT(model=self.sentence_model)
        self.yake_extractor = yake.KeywordExtractor(
            lan="en",
            n=3,  # max n-gram size
            dedupLim=0.9,
            top=10
        )
        self.rake_extractor = Rake()
    
    def extract_topics(self, text: str, max_depth: int = 3, min_keywords: int = 3) -> Dict:
        """
        Extract hierarchical topics from text
        
        Args:
            text: Cleaned syllabus text
            max_depth: Maximum hierarchy depth
            min_keywords: Minimum keywords per topic
        
        Returns:
            Dictionary with hierarchical topics
        """
        # Segment text into sections
        sections = self._segment_text(text)
        
        # Build hierarchy
        hierarchy = self._build_hierarchy(sections, max_depth)
        
        # Extract keywords for each topic
        for unit in hierarchy['units']:
            unit['keywords'] = self._extract_keywords(unit['text'], min_keywords)
            for topic in unit.get('topics', []):
                topic['keywords'] = self._extract_keywords(topic['text'], min_keywords)
                for subtopic in topic.get('subtopics', []):
                    subtopic['keywords'] = self._extract_keywords(subtopic['text'], min_keywords)
        
        return hierarchy
    
    def _segment_text(self, text: str) -> List[Dict]:
        """
        Segment text into logical sections
        
        Args:
            text: Input text
        
        Returns:
            List of sections with metadata
        """
        sections = []
        
        # Split by common academic patterns
        patterns = [
            r'(?:^|\n)(?:Unit|Module|Chapter|Week|Lecture)\s+(\d+)[:\s]+(.+?)(?=\n(?:Unit|Module|Chapter|Week|Lecture)\s+\d+|\Z)',
            r'(?:^|\n)(\d+\.)\s+(.+?)(?=\n\d+\.|\Z)',
            r'(?:^|\n)([A-Z][^\n]{10,100})(?=\n)',
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.MULTILINE | re.DOTALL)
            for match in matches:
                if len(match.groups()) >= 2:
                    sections.append({
                        'title': match.group(2).strip(),
                        'text': match.group(0).strip(),
                        'level': 1
                    })
        
        # If no structured sections found, use sentence clustering
        if not sections:
            sections = self._cluster_sentences(text)
        
        return sections
    
    def _cluster_sentences(self, text: str) -> List[Dict]:
        """
        Cluster sentences using embeddings when no structure is found
        
        Args:
            text: Input text
        
        Returns:
            List of clustered sections
        """
        # Split into sentences
        doc = self.nlp(text)
        sentences = [sent.text.strip() for sent in doc.sents if len(sent.text.strip()) > 20]
        
        if len(sentences) < 3:
            return [{'title': 'Main Content', 'text': text, 'level': 1}]
        
        # Generate embeddings
        embeddings = self.sentence_model.encode(sentences)
        
        # Cluster
        try:
            clusterer = HDBSCAN(min_cluster_size=2, min_samples=1)
            labels = clusterer.fit_predict(embeddings)
            
            # Group sentences by cluster
            clusters = {}
            for idx, label in enumerate(labels):
                if label not in clusters:
                    clusters[label] = []
                clusters[label].append(sentences[idx])
            
            # Create sections from clusters
            sections = []
            for label, sents in clusters.items():
                if label == -1:  # Noise cluster
                    continue
                text = ' '.join(sents)
                title = self._generate_title(sents[0])
                sections.append({
                    'title': title,
                    'text': text,
                    'level': 1
                })
            
            return sections if sections else [{'title': 'Main Content', 'text': text, 'level': 1}]
        
        except Exception as e:
            print(f"Clustering failed: {e}")
            return [{'title': 'Main Content', 'text': text, 'level': 1}]
    
    def _build_hierarchy(self, sections: List[Dict], max_depth: int) -> Dict:
        """
        Build hierarchical topic structure
        
        Args:
            sections: List of sections
            max_depth: Maximum depth
        
        Returns:
            Hierarchical structure
        """
        hierarchy = {'units': []}
        
        for section in sections:
            unit = {
                'title': section['title'],
                'text': section['text'],
                'level': 1,
                'topics': []
            }
            
            # Extract sub-topics if depth allows
            if max_depth > 1:
                subtopics = self._extract_subtopics(section['text'])
                unit['topics'] = subtopics
            
            hierarchy['units'].append(unit)
        
        return hierarchy
    
    def _extract_subtopics(self, text: str) -> List[Dict]:
        """
        Extract subtopics from section text
        
        Args:
            text: Section text
        
        Returns:
            List of subtopics
        """
        subtopics = []
        
        # Pattern for numbered/bulleted lists
        patterns = [
            r'(?:^|\n)\s*(\d+\.\d+)\s+(.+?)(?=\n\s*\d+\.\d+|\Z)',
            r'(?:^|\n)\s*[•\-\*]\s+(.+?)(?=\n\s*[•\-\*]|\Z)',
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.MULTILINE | re.DOTALL)
            for match in matches:
                title = match.group(1 if len(match.groups()) == 1 else 2).strip()
                if len(title) > 5 and len(title) < 200:
                    subtopics.append({
                        'title': title,
                        'text': match.group(0).strip(),
                        'level': 2,
                        'subtopics': []
                    })
        
        return subtopics
    
    def _extract_keywords(self, text: str, min_keywords: int = 3) -> List[str]:
        """
        Extract keywords using ensemble of methods
        
        Args:
            text: Input text
            min_keywords: Minimum number of keywords
        
        Returns:
            List of keywords
        """
        keywords = set()
        
        # KeyBERT
        try:
            keybert_keywords = self.keyword_extractor.extract_keywords(
                text,
                keyphrase_ngram_range=(1, 2),
                stop_words='english',
                top_n=10
            )
            keywords.update([kw[0] for kw in keybert_keywords])
        except:
            pass
        
        # YAKE
        try:
            yake_keywords = self.yake_extractor.extract_keywords(text)
            keywords.update([kw[0] for kw in yake_keywords[:10]])
        except:
            pass
        
        # RAKE
        try:
            self.rake_extractor.extract_keywords_from_text(text)
            rake_keywords = self.rake_extractor.get_ranked_phrases()[:10]
            keywords.update(rake_keywords)
        except:
            pass
        
        # Convert to list and clean
        keywords = list(keywords)
        keywords = [kw.lower().strip() for kw in keywords if len(kw) > 2]
        
        # Remove duplicates and sort by length (prefer shorter, more specific terms)
        keywords = sorted(set(keywords), key=len)
        
        return keywords[:max(min_keywords, 10)]
    
    def _generate_title(self, text: str) -> str:
        """
        Generate a title from text
        
        Args:
            text: Input text
        
        Returns:
            Generated title
        """
        # Take first sentence or first 50 chars
        doc = self.nlp(text[:200])
        first_sent = next(doc.sents, None)
        if first_sent:
            title = first_sent.text.strip()
            if len(title) > 100:
                title = title[:97] + "..."
            return title
        return text[:50] + "..."


class HierarchyBuilder:
    """Build and manage topic hierarchy"""
    
    @staticmethod
    def flatten_hierarchy(hierarchy: Dict) -> List[Dict]:
        """
        Flatten hierarchical structure to list
        
        Args:
            hierarchy: Hierarchical topics
        
        Returns:
            Flat list of topics with parent references
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
