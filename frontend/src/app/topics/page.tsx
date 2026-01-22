'use client';

import { useEffect, useState, Suspense } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { useAppStore } from '@/lib/store';
import { topicAPI, playlistAPI } from '@/services/api';
import { Loader2, Play, BookOpen, ChevronRight, AlertCircle } from 'lucide-react';

function TopicsContent() {
    const searchParams = useSearchParams();
    const router = useRouter();
    const documentId = searchParams?.get('id');
    const { currentDocument, setTopics, topics, setIsLoading, isLoading, setError, error } = useAppStore();

    // Local state for configuration
    const [videosPerTopic, setVideosPerTopic] = useState(3);
    const [useMLRanking, setUseMLRanking] = useState(true);

    useEffect(() => {
        if (!documentId) {
            router.push('/');
            return;
        }

        const fetchTopics = async () => {
            try {
                setIsLoading(true);
                // Poll for topics or get them if ready
                // For simplicity, we just fetch assuming they are ready or the extraction is fast
                // In a real app, we might need polling if extraction is slow
                const data = await topicAPI.get(documentId);
                setTopics(data);
            } catch (err: any) {
                console.error("Error fetching topics:", err);
                setError("Failed to load topics. They might still be generating.");
            } finally {
                setIsLoading(false);
            }
        };

        fetchTopics();
    }, [documentId, router, setIsLoading, setTopics, setError]);

    const handleGeneratePlaylist = async () => {
        if (!documentId) return;

        try {
            setIsLoading(true);
            const playlist = await playlistAPI.generate({
                document_id: documentId,
                name: `Playlist for ${currentDocument?.filename || 'Course'}`,
                videos_per_topic: videosPerTopic,
                use_ml_ranking: useMLRanking,
                weights: {
                    views: 0.15,
                    likes: 0.20,
                    subscribers: 0.10,
                    relevance: 0.40,
                    recency: 0.10,
                    duration_penalty: 0.05
                }
            });

            router.push(`/playlist/${playlist.id}`);
        } catch (err: any) {
            setError(err.response?.data?.detail || "Failed to generate playlist");
            setIsLoading(false);
        }
    };

    if (isLoading && !topics) {
        return (
            <div className="flex flex-col items-center justify-center min-h-[60vh]">
                <Loader2 className="w-12 h-12 text-primary-600 animate-spin mb-4" />
                <h2 className="text-xl font-semibold text-gray-700">Analyzing Syllabus...</h2>
                <p className="text-gray-500">Extracting topics and structure</p>
            </div>
        );
    }

    return (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
            <div className="mb-8 flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold text-gray-900">Extracted Topics</h1>
                    <p className="text-gray-600 mt-2">
                        {currentDocument?.filename ? `From: ${currentDocument.filename}` : 'Review the topics extracted from your syllabus'}
                    </p>
                </div>
                <button
                    onClick={handleGeneratePlaylist}
                    disabled={isLoading}
                    className="flex items-center space-x-2 px-6 py-3 bg-primary-600 text-white rounded-lg font-medium hover:bg-primary-700 transition-colors disabled:opacity-50"
                >
                    {isLoading ? (
                        <Loader2 className="w-5 h-5 animate-spin" />
                    ) : (
                        <Play className="w-5 h-5" />
                    )}
                    <span>Generate Playlist</span>
                </button>
            </div>

            {error && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-8 flex items-start space-x-3">
                    <AlertCircle className="w-5 h-5 text-red-600 mt-0.5" />
                    <p className="text-red-700">{error}</p>
                </div>
            )}

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Configuration Panel */}
                <div className="lg:col-span-1">
                    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 sticky top-24">
                        <h3 className="text-lg font-semibold text-gray-900 mb-4">Configuration</h3>

                        <div className="space-y-6">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-2">
                                    Videos per Topic ({videosPerTopic})
                                </label>
                                <input
                                    type="range"
                                    min="1"
                                    max="10"
                                    value={videosPerTopic}
                                    onChange={(e) => setVideosPerTopic(parseInt(e.target.value))}
                                    className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-primary-600"
                                />
                                <div className="flex justify-between text-xs text-gray-500 mt-1">
                                    <span>1</span>
                                    <span>5</span>
                                    <span>10</span>
                                </div>
                            </div>

                            <div className="flex items-center justify-between">
                                <span className="text-sm font-medium text-gray-700">Use AI Ranking</span>
                                <input
                                    type="checkbox"
                                    checked={useMLRanking}
                                    onChange={(e) => setUseMLRanking(e.target.checked)}
                                    className="w-5 h-5 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                                />
                            </div>

                            <div className="p-4 bg-blue-50 rounded-lg text-sm text-blue-700">
                                AI Ranking uses our trained XGBoost model to score videos based on quality, academic relevance, and freshness.
                            </div>
                        </div>
                    </div>
                </div>

                {/* Topics List */}
                <div className="lg:col-span-2 space-y-4">
                    {Array.isArray(topics) && topics.length > 0 ? (
                        topics.map((unit: any, idx: number) => (
                            <div key={idx} className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
                                <div className="bg-gray-50 px-6 py-4 border-b border-gray-200">
                                    <h3 className="font-semibold text-gray-900 flex items-center">
                                        <BookOpen className="w-5 h-5 text-primary-600 mr-2" />
                                        {unit.title}
                                    </h3>
                                </div>
                                <div className="p-6">
                                    <ul className="space-y-3">
                                        {unit.subtopics?.map((topic: any, tIdx: number) => (
                                            <li key={tIdx} className="flex items-start group">
                                                <ChevronRight className="w-5 h-5 text-gray-400 mt-0.5 mr-2 flex-shrink-0" />
                                                <div>
                                                    <span className="text-gray-900 font-medium group-hover:text-primary-600 transition-colors">
                                                        {topic.title}
                                                    </span>
                                                    {topic.subtopics && topic.subtopics.length > 0 && (
                                                        <ul className="mt-2 ml-4 space-y-1">
                                                            {topic.subtopics.map((sub: any, sIdx: number) => (
                                                                <li key={sIdx} className="text-sm text-gray-600">
                                                                    • {sub.title}
                                                                </li>
                                                            ))}
                                                        </ul>
                                                    )}
                                                </div>
                                            </li>
                                        ))}
                                    </ul>
                                </div>
                            </div>
                        ))
                    ) : (
                        <div className="text-center py-12 bg-white rounded-xl border border-gray-200 border-dashed">
                            <p className="text-gray-500">No topics found. Please try uploading a different file.</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

export default function TopicsPage() {
    return (
        <Suspense fallback={
            <div className="flex items-center justify-center min-h-screen">
                <Loader2 className="w-12 h-12 text-primary-600 animate-spin" />
            </div>
        }>
            <TopicsContent />
        </Suspense>
    );
}
