"""
Query generation service for YouTube search
"""
from typing import List, Dict
import random


class QueryGenerator:
    """Generate optimized YouTube search queries from topics"""
    
    # Query templates by difficulty level
    TEMPLATES = {
        'beginner': [
            "{topic} tutorial for beginners",
            "introduction to {topic}",
            "{topic} explained simply",
            "learn {topic} basics",
            "{topic} for dummies",
            "what is {topic} simple explanation",
        ],
        'intermediate': [
            "{topic} tutorial",
            "{topic} explained",
            "{topic} course",
            "learn {topic}",
            "{topic} guide",
            "understanding {topic}",
        ],
        'advanced': [
            "{topic} advanced tutorial",
            "{topic} deep dive",
            "{topic} in depth",
            "advanced {topic}",
            "{topic} research",
            "{topic} expert guide",
        ],
        'practical': [
            "{topic} examples",
            "{topic} hands on",
            "{topic} practical",
            "{topic} project",
            "how to use {topic}",
            "{topic} implementation",
        ]
    }
    
    def __init__(self):
        """Initialize query generator"""
        pass
    
    def generate_queries(
        self,
        topic: str,
        keywords: List[str] = None,
        difficulty: str = 'intermediate',
        max_queries: int = 4
    ) -> List[str]:
        """
        Generate multiple query variations for a topic
        
        Args:
            topic: Topic title
            keywords: Additional keywords
            difficulty: Difficulty level (beginner/intermediate/advanced)
            max_queries: Maximum number of queries to generate
        
        Returns:
            List of search queries
        """
        queries = []
        
        # Clean topic
        topic_clean = self._clean_topic(topic)
        
        # Get templates for difficulty level
        templates = self.TEMPLATES.get(difficulty, self.TEMPLATES['intermediate'])
        
        # Generate from templates
        for template in templates[:max_queries]:
            query = template.format(topic=topic_clean)
            queries.append(query)
        
        # Add keyword variations if provided
        if keywords and len(queries) < max_queries:
            for keyword in keywords[:2]:
                query = f"{keyword} tutorial"
                if query not in queries:
                    queries.append(query)
        
        # Add practical variation
        if len(queries) < max_queries:
            practical_template = random.choice(self.TEMPLATES['practical'])
            queries.append(practical_template.format(topic=topic_clean))
        
        return queries[:max_queries]
    
    def classify_difficulty(self, topic: str, keywords: List[str] = None) -> str:
        """
        Classify difficulty level of a topic
        
        Args:
            topic: Topic title
            keywords: Topic keywords
        
        Returns:
            Difficulty level (beginner/intermediate/advanced)
        """
        topic_lower = topic.lower()
        keywords_lower = [kw.lower() for kw in (keywords or [])]
        
        # Beginner indicators
        beginner_terms = [
            'introduction', 'basics', 'fundamentals', 'overview',
            'getting started', 'first', 'basic', 'simple'
        ]
        
        # Advanced indicators
        advanced_terms = [
            'advanced', 'deep', 'research', 'optimization',
            'architecture', 'theory', 'algorithm', 'complex'
        ]
        
        # Check topic and keywords
        all_text = topic_lower + ' ' + ' '.join(keywords_lower)
        
        if any(term in all_text for term in beginner_terms):
            return 'beginner'
        elif any(term in all_text for term in advanced_terms):
            return 'advanced'
        else:
            return 'intermediate'
    
    def _clean_topic(self, topic: str) -> str:
        """
        Clean topic for search query
        
        Args:
            topic: Raw topic title
        
        Returns:
            Cleaned topic
        """
        # Remove common prefixes
        prefixes = ['Unit', 'Module', 'Chapter', 'Week', 'Lecture', 'Topic']
        for prefix in prefixes:
            if topic.startswith(prefix):
                # Remove prefix and number
                topic = topic[len(prefix):].lstrip(' :0123456789.-')
        
        # Remove excessive punctuation
        topic = topic.replace(':', '').replace(';', '')
        
        # Limit length
        if len(topic) > 60:
            topic = topic[:57] + "..."
        
        return topic.strip()
    
    def expand_with_synonyms(self, topic: str) -> List[str]:
        """
        Expand topic with synonyms (simplified version)
        
        Args:
            topic: Topic title
        
        Returns:
            List of topic variations
        """
        # Common academic synonyms
        synonyms = {
            'machine learning': ['ML', 'artificial intelligence', 'AI'],
            'deep learning': ['neural networks', 'DL'],
            'data structure': ['data structures', 'DSA'],
            'algorithm': ['algorithms', 'algorithmic'],
            'database': ['databases', 'DBMS', 'SQL'],
            'network': ['networking', 'computer networks'],
            'programming': ['coding', 'software development'],
        }
        
        topic_lower = topic.lower()
        variations = [topic]
        
        for key, syns in synonyms.items():
            if key in topic_lower:
                for syn in syns:
                    variations.append(topic_lower.replace(key, syn))
        
        return list(set(variations))[:3]
