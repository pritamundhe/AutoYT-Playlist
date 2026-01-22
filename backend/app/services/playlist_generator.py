"""
Playlist generation service
"""
from typing import List, Dict, Optional
from datetime import datetime
import json
import csv
from pathlib import Path

from app.services.query_generator import QueryGenerator
from app.services.youtube_service import YouTubeService
from app.services.relevance_scorer import RelevanceScorer
from app.services.ranking_engine import RankingEnsemble


class PlaylistGenerator:
    """Generate playlists from topics"""
    
    def __init__(self):
        """Initialize playlist generator"""
        self.query_generator = QueryGenerator()
        self.youtube_service = YouTubeService()
        self.relevance_scorer = RelevanceScorer()
    
    def generate_playlist(
        self,
        topics: List[Dict],
        weights: Optional[Dict[str, float]] = None,
        filters: Optional[Dict] = None,
        videos_per_topic: int = 5,
        use_ml_ranking: bool = True
    ) -> Dict:
        """
        Generate playlist from topics
        
        Args:
            topics: List of topic dictionaries
            weights: Ranking weights
            filters: Video filters
            videos_per_topic: Number of videos per topic
            use_ml_ranking: Whether to use ML ranking
        
        Returns:
            Playlist dictionary with videos
        """
        playlist_items = []
        total_duration = 0
        
        # Initialize ranker
        ranker = RankingEnsemble(weights=weights, use_ml=use_ml_ranking)
        
        # Process each topic
        for topic in topics:
            # Generate queries
            difficulty = self.query_generator.classify_difficulty(
                topic['title'],
                topic.get('keywords', [])
            )
            queries = self.query_generator.generate_queries(
                topic['title'],
                topic.get('keywords', []),
                difficulty=difficulty,
                max_queries=2  # Use 2 queries per topic
            )
            
            # Search videos for each query
            all_videos = []
            for query in queries:
                videos = self.youtube_service.search_videos(
                    query,
                    max_results=videos_per_topic * 2,  # Get more to filter
                    filters=filters
                )
                all_videos.extend(videos)
            
            # Remove duplicates
            unique_videos = self._deduplicate_videos(all_videos)
            
            if not unique_videos:
                continue
            
            # Compute relevance scores
            relevance_scores = self.relevance_scorer.compute_batch_relevance(
                topic,
                unique_videos
            )
            
            # Rank videos
            ranked_videos = ranker.rank_videos(unique_videos, relevance_scores)
            
            # Take top N videos
            top_videos = ranked_videos[:videos_per_topic]
            
            # Add to playlist
            for rank, video in enumerate(top_videos, 1):
                playlist_items.append({
                    'topic_id': topic.get('id'),
                    'topic_title': topic['title'],
                    'video': video,
                    'rank': rank,
                    'score': video['score'],
                    'relevance_score': video.get('relevance_score')
                })
                total_duration += video['duration']
        
        return {
            'items': playlist_items,
            'total_videos': len(playlist_items),
            'total_duration': total_duration,
            'topics_covered': len([t for t in topics if any(i['topic_id'] == t.get('id') for i in playlist_items)])
        }
    
    def _deduplicate_videos(self, videos: List[Dict]) -> List[Dict]:
        """
        Remove duplicate videos
        
        Args:
            videos: List of videos
        
        Returns:
            Deduplicated list
        """
        seen = set()
        unique = []
        
        for video in videos:
            video_id = video['youtube_id']
            if video_id not in seen:
                seen.add(video_id)
                unique.append(video)
        
        return unique
    
    def export_to_json(self, playlist: Dict, output_path: str) -> str:
        """
        Export playlist to JSON
        
        Args:
            playlist: Playlist dictionary
            output_path: Output file path
        
        Returns:
            Path to exported file
        """
        # Prepare export data
        export_data = {
            'metadata': {
                'total_videos': playlist['total_videos'],
                'total_duration': playlist['total_duration'],
                'topics_covered': playlist['topics_covered'],
                'exported_at': datetime.utcnow().isoformat()
            },
            'videos': []
        }
        
        for item in playlist['items']:
            video = item['video']
            export_data['videos'].append({
                'topic': item['topic_title'],
                'rank': item['rank'],
                'score': item['score'],
                'youtube_id': video['youtube_id'],
                'title': video['title'],
                'channel': video['channel_title'],
                'url': f"https://www.youtube.com/watch?v={video['youtube_id']}",
                'duration': video['duration'],
                'views': video['views'],
                'likes': video['likes'],
                'upload_date': video['upload_date'].isoformat() if isinstance(video['upload_date'], datetime) else video['upload_date']
            })
        
        # Write to file
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        return output_path
    
    def export_to_csv(self, playlist: Dict, output_path: str) -> str:
        """
        Export playlist to CSV
        
        Args:
            playlist: Playlist dictionary
            output_path: Output file path
        
        Returns:
            Path to exported file
        """
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Header
            writer.writerow([
                'Topic', 'Rank', 'Score', 'Title', 'Channel',
                'URL', 'Duration (s)', 'Views', 'Likes', 'Upload Date'
            ])
            
            # Data
            for item in playlist['items']:
                video = item['video']
                writer.writerow([
                    item['topic_title'],
                    item['rank'],
                    f"{item['score']:.4f}",
                    video['title'],
                    video['channel_title'],
                    f"https://www.youtube.com/watch?v={video['youtube_id']}",
                    video['duration'],
                    video['views'],
                    video['likes'],
                    video['upload_date'].isoformat() if isinstance(video['upload_date'], datetime) else video['upload_date']
                ])
        
        return output_path
    
    def export_to_markdown(self, playlist: Dict, output_path: str, playlist_name: str = "YouTube Playlist") -> str:
        """
        Export playlist to Markdown
        
        Args:
            playlist: Playlist dictionary
            output_path: Output file path
            playlist_name: Name of the playlist
        
        Returns:
            Path to exported file
        """
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            # Header
            f.write(f"# {playlist_name}\n\n")
            f.write(f"**Total Videos:** {playlist['total_videos']}\n")
            f.write(f"**Total Duration:** {playlist['total_duration'] // 60} minutes\n")
            f.write(f"**Topics Covered:** {playlist['topics_covered']}\n\n")
            f.write("---\n\n")
            
            # Group by topic
            current_topic = None
            for item in playlist['items']:
                if item['topic_title'] != current_topic:
                    current_topic = item['topic_title']
                    f.write(f"## {current_topic}\n\n")
                
                video = item['video']
                f.write(f"### {item['rank']}. {video['title']}\n\n")
                f.write(f"**Channel:** {video['channel_title']}\n")
                f.write(f"**URL:** https://www.youtube.com/watch?v={video['youtube_id']}\n")
                f.write(f"**Duration:** {video['duration'] // 60}:{video['duration'] % 60:02d}\n")
                f.write(f"**Views:** {video['views']:,}\n")
                f.write(f"**Likes:** {video['likes']:,}\n")
                f.write(f"**Score:** {item['score']:.4f}\n\n")
        
        return output_path
