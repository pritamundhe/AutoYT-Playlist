'use client';

import { useEffect, useState, Suspense } from 'react';
import { useRouter } from 'next/navigation';
import { playlistAPI } from '@/services/api';
import { Loader2, ExternalLink, Clock, ThumbsUp, Eye, PlayCircle, Share2, Download, Star, Play } from 'lucide-react';
import Image from 'next/image';

function PlaylistContent({ params }: { params: { id: string } }) {
    const router = useRouter();
    const [playlist, setPlaylist] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [activeUnit, setActiveUnit] = useState<string | null>(null);

    useEffect(() => {
        const fetchPlaylist = async () => {
            try {
                const data = await playlistAPI.get(params.id);
                setPlaylist(data);
                // Set first unit as active
                if (data.units && Object.keys(data.units).length > 0) {
                    setActiveUnit(Object.keys(data.units)[0]);
                }
            } catch (err: any) {
                console.error("Error fetching playlist:", err);
                setError("Failed to load playlist.");
            } finally {
                setLoading(false);
            }
        };

        if (params.id) {
            fetchPlaylist();
        }
    }, [params.id]);

    if (loading) {
        return (
            <div className="flex flex-col items-center justify-center min-h-[60vh]">
                <Loader2 className="w-12 h-12 text-primary-600 animate-spin mb-4" />
                <h2 className="text-xl font-semibold text-gray-700">Curating Your Playlist...</h2>
                <p className="text-gray-500">Finding the best videos for your syllabus</p>
            </div>
        );
    }

    if (error || !playlist) {
        return (
            <div className="flex flex-col items-center justify-center min-h-[60vh] max-w-lg mx-auto text-center px-4">
                <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mb-4">
                    <span className="text-2xl">⚠️</span>
                </div>
                <h2 className="text-xl font-semibold text-gray-900 mb-2">Something went wrong</h2>
                <p className="text-gray-600 mb-6">{error || "Playlist not found"}</p>
                <button
                    onClick={() => router.push('/')}
                    className="px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
                >
                    Back to Home
                </button>
            </div>
        );
    }

    // Organize items by unit/topic logic if backend response is flat vs hierarchical
    // Assuming backend returns a structure we can map. If it's just a flat extracted list, we might need to process it.
    // For now, let's assume the API returns 'items' grouped by topic or we do it here.

    // Helper to format number
    const formatNumber = (num: number) => {
        return new Intl.NumberFormat('en-US', { notation: "compact", maximumFractionDigits: 1 }).format(num);
    };

    // Helper to format duration
    const formatDuration = (seconds: number) => {
        const h = Math.floor(seconds / 3600);
        const m = Math.floor((seconds % 3600) / 60);
        return h > 0 ? `${h}h ${m}m` : `${m}m`;
    };

    return (
        <div className="min-h-screen bg-gray-50 pb-20">
            {/* Hero Section */}
            <div className="bg-white border-b border-gray-200">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                    <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-6">
                        <div className="flex-1">
                            <h1 className="text-3xl font-bold text-gray-900 mb-2">{playlist.name}</h1>
                            <div className="flex flex-wrap items-center gap-4 text-sm text-gray-600">
                                <span className="flex items-center">
                                    <PlayCircle className="w-4 h-4 mr-1" />
                                    {playlist.total_videos || playlist.items?.length || 0} Videos
                                </span>
                                <span className="flex items-center">
                                    <Clock className="w-4 h-4 mr-1" />
                                    {formatDuration(playlist.total_duration || 0)} Total Time
                                </span>
                                <span className="px-2 py-0.5 bg-green-100 text-green-700 rounded-full text-xs font-medium">
                                    AI Generated
                                </span>
                            </div>
                        </div>

                        <div className="flex gap-3">
                            <button className="flex items-center px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 font-medium transition-colors">
                                <Share2 className="w-4 h-4 mr-2" />
                                Share
                            </button>
                            <button className="flex items-center px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 font-medium transition-colors shadow-sm">
                                <ExternalLink className="w-4 h-4 mr-2" />
                                Export to YouTube
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
                    {/* Sidebar / Navigation */}
                    <div className="lg:col-span-1 hidden lg:block">
                        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4 sticky top-24">
                            <h3 className="font-semibold text-gray-900 mb-4 px-2">Course Modules</h3>
                            <nav className="space-y-1">
                                {playlist.items && [...new Set(playlist.items.map((i: any) => i.topic?.parent?.title || i.topic?.title))].map((unit: any, idx) => (
                                    <button
                                        key={idx}
                                        onClick={() => setActiveUnit(unit)}
                                        className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-colors ${activeUnit === unit
                                            ? 'bg-primary-50 text-primary-700 font-medium'
                                            : 'text-gray-600 hover:bg-gray-50'
                                            }`}
                                    >
                                        {unit}
                                    </button>
                                ))}
                            </nav>
                        </div>
                    </div>

                    {/* Content */}
                    <div className="lg:col-span-3 space-y-8">
                        {/* Render items grouped by topic */}
                        {playlist.items?.map((item: any, idx: number) => (
                            <div key={item.id} className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden hover:shadow-md transition-shadow">
                                <div className="flex flex-col md:flex-row">
                                    {/* Thumbnail */}
                                    <div className="relative md:w-64 h-48 md:h-auto flex-shrink-0 group">
                                        {item.video?.thumbnail_url ? (
                                            <Image
                                                src={item.video.thumbnail_url}
                                                alt={item.video.title}
                                                fill
                                                className="object-cover"
                                            />
                                        ) : (
                                            <div className="w-full h-full bg-gray-200 flex items-center justify-center">
                                                <PlayCircle className="w-12 h-12 text-gray-400" />
                                            </div>
                                        )}
                                        <div className="absolute inset-0 bg-black/0 group-hover:bg-black/10 transition-colors flex items-center justify-center">
                                            <a
                                                href={`https://www.youtube.com/watch?v=${item.video?.youtube_id}`}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                className="opacity-0 group-hover:opacity-100 transform scale-90 group-hover:scale-100 transition-all"
                                            >
                                                <div className="w-12 h-12 bg-red-600 rounded-full flex items-center justify-center shadow-lg">
                                                    <Play className="w-6 h-6 text-white fill-current ml-1" />
                                                </div>
                                            </a>
                                        </div>
                                        <div className="absolute bottom-2 right-2 px-2 py-1 bg-black/70 text-white text-xs rounded font-medium">
                                            {formatDuration(item.video?.duration)}
                                        </div>
                                    </div>

                                    {/* Info */}
                                    <div className="p-5 flex-1 flex flex-col justify-between">
                                        <div>
                                            <div className="flex items-center space-x-2 mb-2">
                                                <span className="text-xs font-semibold text-primary-600 bg-primary-50 px-2 py-0.5 rounded">
                                                    #{item.rank + 1} for "{item.topic?.title}"
                                                </span>
                                                {item.score > 0.8 && (
                                                    <span className="flex items-center text-xs text-amber-600 bg-amber-50 px-2 py-0.5 rounded font-medium">
                                                        <Star className="w-3 h-3 mr-1 fill-current" />
                                                        Top Pick
                                                    </span>
                                                )}
                                            </div>

                                            <h3 className="text-lg font-bold text-gray-900 mb-1 line-clamp-2">
                                                <a href={`https://www.youtube.com/watch?v=${item.video?.youtube_id}`} target="_blank" rel="noopener noreferrer" className="hover:text-primary-600">
                                                    {item.video?.title}
                                                </a>
                                            </h3>

                                            <p className="text-sm text-gray-600 mb-3 line-clamp-2">
                                                {item.video?.description}
                                            </p>
                                        </div>

                                        <div className="flex items-center justify-between mt-4 border-t border-gray-100 pt-4">
                                            <div className="flex items-center space-x-4 text-sm text-gray-500">
                                                <div className="flex items-center">
                                                    <Eye className="w-4 h-4 mr-1.5" />
                                                    {formatNumber(item.video?.views)}
                                                </div>
                                                <div className="flex items-center">
                                                    <ThumbsUp className="w-4 h-4 mr-1.5" />
                                                    {formatNumber(item.video?.likes)}
                                                </div>
                                            </div>

                                            <div className="text-sm text-gray-500 font-medium">
                                                {item.video?.channel_title}
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
}

export default function PlaylistPage({ params }: { params: { id: string } }) {
    return <PlaylistContent params={params} />;
}
