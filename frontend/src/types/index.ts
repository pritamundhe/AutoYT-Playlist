/**
 * TypeScript type definitions
 */

export interface Document {
    id: string;
    filename: string;
    file_type: string;
    file_size: number;
    upload_date: string;
    status: 'uploaded' | 'processing' | 'completed' | 'failed';
    error_message?: string;
}

export interface Topic {
    id: string;
    document_id: string;
    title: string;
    level: number;
    keywords: string[];
    description?: string;
    parent_id?: string;
    order_index: number;
    subtopics?: Topic[];
}

export interface Video {
    id: string;
    youtube_id: string;
    title: string;
    description?: string;
    channel_title: string;
    views: number;
    likes: number;
    duration: number;
    upload_date: string;
    thumbnail_url?: string;
    has_captions: boolean;
    is_hd: boolean;
}

export interface PlaylistItem {
    id: string;
    video: Video;
    topic_title: string;
    rank: number;
    score: number;
    relevance_score?: number;
}

export interface Playlist {
    id: string;
    document_id: string;
    name: string;
    description?: string;
    total_videos: number;
    total_duration: number;
    created_date: string;
    youtube_playlist_id?: string;
    youtube_url?: string;
    items?: PlaylistItem[];
}

export interface RankingWeights {
    views: number;
    likes: number;
    subscribers: number;
    relevance: number;
    recency: number;
    duration_penalty: number;
}

export interface PlaylistFilters {
    min_views?: number;
    max_duration?: number;
    min_duration?: number;
    language?: string;
    upload_date_after?: string;
    has_captions?: boolean;
    is_hd?: boolean;
}

export interface PlaylistCreateRequest {
    document_id: string;
    name: string;
    description?: string;
    weights: RankingWeights;
    filters?: PlaylistFilters;
    videos_per_topic: number;
    use_ml_ranking: boolean;
}

export interface EvaluationResult {
    id: string;
    playlist_id: string;
    precision_at_1?: number;
    precision_at_3?: number;
    precision_at_5?: number;
    precision_at_10?: number;
    ndcg?: number;
    topic_coverage?: number;
    user_satisfaction?: number;
    evaluated_at: string;
}
