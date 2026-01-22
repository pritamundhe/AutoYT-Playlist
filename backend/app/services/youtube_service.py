"""
YouTube Data API v3 integration service
"""
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import isodate

from app.core.config import settings
from app.core.redis_client import redis_client


class YouTubeService:
    """YouTube API integration with caching and quota management"""
    
    def __init__(self, api_key: str = None):
        """Initialize YouTube API client"""
        self.api_key = api_key or settings.YOUTUBE_API_KEY
        self.youtube = build('youtube', 'v3', developerKey=self.api_key)
        self.quota_used = 0
        self.quota_limit = settings.YOUTUBE_API_QUOTA_LIMIT
        self.last_request_time = 0
        self.min_request_interval = 0.2  # 5 requests per second max
    
    def search_videos(
        self,
        query: str,
        max_results: int = 10,
        filters: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Search for videos using YouTube API
        
        Args:
            query: Search query
            max_results: Maximum number of results
            filters: Optional filters (language, upload date, etc.)
        
        Returns:
            List of video metadata dictionaries
        """
        # Check cache first
        cache_key = f"youtube:search:{query}:{max_results}"
        cached = redis_client.get(cache_key)
        if cached:
            return cached
        
        # Rate limiting
        self._rate_limit()
        
        try:
            # Build search parameters
            search_params = {
                'q': query,
                'part': 'snippet',
                'type': 'video',
                'maxResults': min(max_results, 50),
                'relevanceLanguage': filters.get('language', 'en') if filters else 'en',
                'videoDefinition': 'any',
                'videoCaption': 'any',
            }
            
            # Add date filter if provided
            if filters and filters.get('upload_date_after'):
                search_params['publishedAfter'] = filters['upload_date_after'].isoformat() + 'Z'
            
            # Execute search
            search_response = self.youtube.search().list(**search_params).execute()
            self.quota_used += 100  # Search costs 100 units
            
            # Extract video IDs
            video_ids = [item['id']['videoId'] for item in search_response.get('items', [])]
            
            if not video_ids:
                return []
            
            # Get detailed video information
            videos = self._get_video_details(video_ids, filters)
            
            # Cache results
            redis_client.set(cache_key, videos, ttl=settings.YOUTUBE_CACHE_TTL)
            
            return videos
        
        except HttpError as e:
            print(f"YouTube API error: {e}")
            if e.resp.status == 403:
                print("Quota exceeded or API key invalid")
            return []
        except Exception as e:
            print(f"Error searching videos: {e}")
            return []
    
    def _get_video_details(self, video_ids: List[str], filters: Optional[Dict] = None) -> List[Dict]:
        """
        Get detailed information for videos
        
        Args:
            video_ids: List of video IDs
            filters: Optional filters to apply
        
        Returns:
            List of video metadata
        """
        # Check cache for each video
        videos = []
        uncached_ids = []
        
        for video_id in video_ids:
            cache_key = f"youtube:video:{video_id}"
            cached = redis_client.get(cache_key)
            if cached:
                videos.append(cached)
            else:
                uncached_ids.append(video_id)
        
        # Fetch uncached videos
        if uncached_ids:
            try:
                # Rate limiting
                self._rate_limit()
                
                # Get video details (batched)
                video_response = self.youtube.videos().list(
                    part='snippet,contentDetails,statistics',
                    id=','.join(uncached_ids)
                ).execute()
                self.quota_used += 1  # Videos.list costs 1 unit
                
                # Get channel details for subscriber count
                channel_ids = [item['snippet']['channelId'] for item in video_response.get('items', [])]
                channel_stats = self._get_channel_stats(channel_ids)
                
                # Process each video
                for item in video_response.get('items', []):
                    video = self._parse_video_item(item, channel_stats)
                    
                    # Apply filters
                    if self._apply_filters(video, filters):
                        videos.append(video)
                        
                        # Cache video
                        cache_key = f"youtube:video:{video['youtube_id']}"
                        redis_client.set(cache_key, video, ttl=settings.YOUTUBE_CACHE_TTL * 7)  # 7 days
            
            except Exception as e:
                print(f"Error getting video details: {e}")
        
        return videos
    
    def _get_channel_stats(self, channel_ids: List[str]) -> Dict[str, int]:
        """
        Get subscriber counts for channels
        
        Args:
            channel_ids: List of channel IDs
        
        Returns:
            Dictionary mapping channel ID to subscriber count
        """
        stats = {}
        
        if not channel_ids:
            return stats
        
        try:
            # Rate limiting
            self._rate_limit()
            
            # Get channel statistics
            channel_response = self.youtube.channels().list(
                part='statistics',
                id=','.join(set(channel_ids))  # Remove duplicates
            ).execute()
            self.quota_used += 1
            
            for item in channel_response.get('items', []):
                channel_id = item['id']
                subscriber_count = int(item['statistics'].get('subscriberCount', 0))
                stats[channel_id] = subscriber_count
        
        except Exception as e:
            print(f"Error getting channel stats: {e}")
        
        return stats
    
    def _parse_video_item(self, item: Dict, channel_stats: Dict[str, int]) -> Dict:
        """
        Parse video item from API response
        
        Args:
            item: Video item from API
            channel_stats: Channel statistics
        
        Returns:
            Parsed video dictionary
        """
        snippet = item['snippet']
        statistics = item.get('statistics', {})
        content_details = item.get('contentDetails', {})
        
        # Parse duration
        duration_iso = content_details.get('duration', 'PT0S')
        duration_seconds = int(isodate.parse_duration(duration_iso).total_seconds())
        
        # Parse upload date
        upload_date = datetime.fromisoformat(snippet['publishedAt'].replace('Z', '+00:00'))
        
        # Get channel subscriber count
        channel_id = snippet['channelId']
        subscribers = channel_stats.get(channel_id, 0)
        
        return {
            'youtube_id': item['id'],
            'title': snippet['title'],
            'description': snippet.get('description', ''),
            'channel_id': channel_id,
            'channel_title': snippet['channelTitle'],
            'views': int(statistics.get('viewCount', 0)),
            'likes': int(statistics.get('likeCount', 0)),
            'comments': int(statistics.get('commentCount', 0)),
            'subscribers': subscribers,
            'duration': duration_seconds,
            'upload_date': upload_date,
            'category_id': snippet.get('categoryId'),
            'tags': snippet.get('tags', []),
            'has_captions': content_details.get('caption') == 'true',
            'is_hd': content_details.get('definition') == 'hd',
            'thumbnail_url': snippet['thumbnails'].get('high', {}).get('url'),
        }
    
    def _apply_filters(self, video: Dict, filters: Optional[Dict]) -> bool:
        """
        Apply filters to video
        
        Args:
            video: Video metadata
            filters: Filter criteria
        
        Returns:
            True if video passes filters
        """
        if not filters:
            return True
        
        # Min views filter
        if filters.get('min_views') and video['views'] < filters['min_views']:
            return False
        
        # Duration filters
        if filters.get('max_duration') and video['duration'] > filters['max_duration']:
            return False
        if filters.get('min_duration') and video['duration'] < filters['min_duration']:
            return False
        
        # Caption filter
        if filters.get('has_captions') and not video['has_captions']:
            return False
        
        # HD filter
        if filters.get('is_hd') and not video['is_hd']:
            return False
        
        return True
    
    def _rate_limit(self):
        """Implement rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            time.sleep(self.min_request_interval - time_since_last)
        
        self.last_request_time = time.time()
    
    def create_playlist(self, title: str, description: str, video_ids: List[str], oauth_token: str) -> Dict:
        """
        Create YouTube playlist (requires OAuth)
        
        Args:
            title: Playlist title
            description: Playlist description
            video_ids: List of video IDs
            oauth_token: OAuth access token
        
        Returns:
            Playlist information
        """
        # Note: This requires OAuth implementation
        # For now, return a mock response
        return {
            'success': False,
            'message': 'OAuth implementation required for playlist creation'
        }
    
    def get_quota_usage(self) -> Dict:
        """
        Get current quota usage
        
        Returns:
            Quota usage information
        """
        return {
            'used': self.quota_used,
            'limit': self.quota_limit,
            'remaining': self.quota_limit - self.quota_used,
            'percentage': (self.quota_used / self.quota_limit) * 100
        }
