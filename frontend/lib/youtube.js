
import { google } from 'googleapis';

const youtube = google.youtube({
    version: 'v3',
    auth: process.env.YOUTUBE_API_KEY,
});

export async function searchVideos(query, maxResults = 20) {
    try {
        // 1. Search for video IDs
        const searchResponse = await youtube.search.list({
            part: 'id,snippet',
            q: query,
            maxResults: maxResults,
            type: 'video',
        });

        const videoIds = searchResponse.data.items.map(item => item.id.videoId).join(',');

        if (!videoIds) return [];

        // 2. Fetch video details (stats, duration)
        const videosResponse = await youtube.videos.list({
            part: 'snippet,statistics,contentDetails',
            id: videoIds,
        });

        return videosResponse.data.items.map((item) => ({
            id: item.id,
            title: item.snippet.title,
            description: item.snippet.description,
            thumbnail: item.snippet.thumbnails.medium.url,
            channel: item.snippet.channelTitle,
            url: `https://www.youtube.com/watch?v=${item.id}`,
            views: parseInt(item.statistics.viewCount || '0', 10),
            likes: parseInt(item.statistics.likeCount || '0', 10),
            duration: item.contentDetails.duration,
            publishedAt: item.snippet.publishedAt,
        }));
    } catch (error) {
        console.error('YouTube API Error:', error);
        return [];
    }
}
