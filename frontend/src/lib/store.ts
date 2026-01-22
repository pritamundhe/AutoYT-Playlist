/**
 * Zustand store for application state
 */
import { create } from 'zustand';
import { Document, Topic, Playlist, RankingWeights } from '@/types';

interface AppState {
    // Document state
    currentDocument: Document | null;
    setCurrentDocument: (document: Document | null) => void;

    // Topics state
    topics: Topic[];
    setTopics: (topics: Topic[]) => void;

    // Playlist state
    currentPlaylist: Playlist | null;
    setCurrentPlaylist: (playlist: Playlist | null) => void;

    // Ranking weights
    weights: RankingWeights;
    setWeights: (weights: RankingWeights) => void;

    // UI state
    isLoading: boolean;
    setIsLoading: (loading: boolean) => void;

    error: string | null;
    setError: (error: string | null) => void;
}

export const useAppStore = create<AppState>((set) => ({
    // Document state
    currentDocument: null,
    setCurrentDocument: (document) => set({ currentDocument: document }),

    // Topics state
    topics: [],
    setTopics: (topics) => set({ topics }),

    // Playlist state
    currentPlaylist: null,
    setCurrentPlaylist: (playlist) => set({ currentPlaylist: playlist }),

    // Default ranking weights
    weights: {
        views: 0.15,
        likes: 0.20,
        subscribers: 0.10,
        relevance: 0.40,
        recency: 0.10,
        duration_penalty: 0.05,
    },
    setWeights: (weights) => set({ weights }),

    // UI state
    isLoading: false,
    setIsLoading: (loading) => set({ isLoading: loading }),

    error: null,
    setError: (error) => set({ error }),
}));
