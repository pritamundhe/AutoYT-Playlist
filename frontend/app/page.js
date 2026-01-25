
'use client';

import { useState, useMemo, useEffect } from 'react';
import { useSession, signIn, signOut } from "next-auth/react";

import VideoModal from '../components/VideoModal';
import { UploadCloud, FileText, Layout, Download, Youtube, Eye, ThumbsUp, Play, Clock, Search, Sparkles, History as HistoryIcon, Timer, Check, CheckCircle } from 'lucide-react';

export default function Home() {
    const { data: session } = useSession();
    const [file, setFile] = useState(null);
    const [loading, setLoading] = useState(false);
    const [playlist, setPlaylist] = useState(null);
    const [error, setError] = useState(null);

    // History State
    const [showHistory, setShowHistory] = useState(false);
    const [history, setHistory] = useState([]);

    // State for Features
    const [playlistName, setPlaylistName] = useState('');
    const [minLikes, setMinLikes] = useState(0);
    const [sortBy, setSortBy] = useState('relevance');
    const [isSortOpen, setIsSortOpen] = useState(false);
    // View Mode: 'grid' | 'list'
    const [viewMode, setViewMode] = useState('grid');

    const sortOptions = {
        relevance: { label: 'Relevance', icon: Sparkles },
        views: { label: 'Most Views', icon: Eye },
        likes: { label: 'Most Likes', icon: ThumbsUp },
        date: { label: 'Newest', icon: Clock },
        duration: { label: 'Duration', icon: Timer }
    };

    // Preview & Export
    const [previewId, setPreviewId] = useState(null);
    const [selectedVideos, setSelectedVideos] = useState(new Set());

    // Save Modal State
    const [saveStatus, setSaveStatus] = useState('idle'); // idle, loading, success, error
    const [saveMessage, setSaveMessage] = useState('');

    const handleFileChange = (e) => {
        if (e.target.files) {
            setFile(e.target.files[0]);
            // Default name to filename without extension
            setPlaylistName(e.target.files[0].name.replace(/\.[^/.]+$/, ""));
        }
    };

    const handleUpload = async (e) => {
        e.preventDefault();
        if (!file) return;

        setLoading(true);
        setError(null);
        setPlaylist(null);
        setSelectedVideos(new Set()); // Start with NO selection

        const formData = new FormData();
        formData.append('file', file);

        try {
            const res = await fetch('/api/upload', {
                method: 'POST',
                body: formData,
            });

            const data = await res.json();

            if (!res.ok) {
                throw new Error(data.error || 'Something went wrong');
            }

            setPlaylist(data.playlist);
            // User requested: "playlist banate samay videos cards mei" -> Grid View
            setViewMode('grid');

            // Save to History
            await fetch('/api/history', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name: e.target.files[0].name.replace(/\.[^/.]+$/, "") || 'Untitled Playlist',
                    topics: data.playlist,
                    userName: session?.user?.name || 'Anonymous'
                })
            });

        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const toggleSelection = (videoId) => {
        const newSet = new Set(selectedVideos);
        if (newSet.has(videoId)) {
            newSet.delete(videoId);
        } else {
            newSet.add(videoId);
        }
        setSelectedVideos(newSet);
    };

    const handleExportYouTube = async () => {
        if (selectedVideos.size === 0) return;

        // If not signed in, fallback to old method
        if (!session) {
            const ids = Array.from(selectedVideos).join(',');
            window.open(`http://www.youtube.com/watch_videos?video_ids=${ids}`, '_blank');
            return;
        }

        // Save to YouTube Account
        try {
            setSaveStatus('loading');
            setSaveMessage('Creating playlist on YouTube...');

            const res = await fetch('/api/youtube/create', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    accessToken: session.accessToken,
                    name: playlistName || 'AutoYT Playlist',
                    videoIds: Array.from(selectedVideos)
                })
            });
            const data = await res.json();
            if (data.success) {
                // Save to History as per user request
                const historyData = {
                    name: playlistName || 'AutoYT Playlist',
                    topics: playlist.map(item => ({
                        topic: item.topic,
                        videos: item.videos.filter(v => selectedVideos.has(v.id))
                    })).filter(item => item.videos.length > 0),
                    userName: session?.user?.name || 'Anonymous'
                };

                await fetch('/api/history', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(historyData)
                });

                setSaveStatus('success');
                setSaveMessage(`Playlist "${playlistName}" created successfully!`);

                // Close after 2 seconds
                setTimeout(() => {
                    setSaveStatus('idle');
                    setSaveMessage('');
                }, 2000);
            } else {
                throw new Error(data.error);
            }
        } catch (err) {
            setSaveStatus('error');
            setSaveMessage('Failed: ' + err.message);
            // Allow manual close or close after longer delay
            setTimeout(() => {
                setSaveStatus('idle');
                setSaveMessage('');
            }, 4000);
        }
    };

    const handleDownloadJSON = () => {
        if (!playlist || selectedVideos.size === 0) return;

        // Filter the full playlist object to only include selected
        const exportData = {
            name: playlistName || 'AutoYT Playlist',
            generatedAt: new Date().toISOString(),
            topics: playlist.map(item => ({
                topic: item.topic,
                videos: item.videos.filter(v => selectedVideos.has(v.id))
            })).filter(item => item.videos.length > 0)
        };

        const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${playlistName || 'playlist'}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        URL.revokeObjectURL(url);
    };

    const fetchHistory = async () => {
        try {
            const res = await fetch('/api/history');
            const data = await res.json();
            if (data.playlists) {
                setHistory(data.playlists);
                setShowHistory(true);
            }
        } catch (err) {
            console.error('Failed to fetch history:', err);
        }
    };

    const loadFromHistory = (item) => {
        setPlaylist(item.topics);
        setPlaylistName(item.name);
        setShowHistory(false);
        setViewMode('list');
    };

    // Filter Logic & Smart 4-Video Selection
    const filteredPlaylist = useMemo(() => {
        if (!playlist) return null;

        const getSeconds = (duration) => {
            const match = duration.match(/PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?/);
            if (!match) return 0;
            const hours = parseInt(match[1] || 0);
            const minutes = parseInt(match[2] || 0);
            const seconds = parseInt(match[3] || 0);
            return (hours * 3600) + (minutes * 60) + seconds;
        };

        return playlist.map(item => {
            // 1. Filter valid candidates (> 60s)
            let candidates = item.videos.filter(v => getSeconds(v.duration) > 60);

            // 2. Select Top 4 Unique Videos based on slots
            const picked = [];
            const isPicked = (id) => picked.some(v => v.id === id);

            if (candidates.length > 0) {
                // Slot 1: Most Liked
                const byLikes = [...candidates].sort((a, b) => b.likes - a.likes);
                const pick1 = byLikes.find(v => !isPicked(v.id));
                if (pick1) picked.push(pick1);

                // Slot 2: Most Views
                const byViews = [...candidates].sort((a, b) => b.views - a.views);
                const pick2 = byViews.find(v => !isPicked(v.id));
                if (pick2) picked.push(pick2);

                // Slot 3: Smallest Duration (but > 60s)
                const byDuration = [...candidates].sort((a, b) => getSeconds(a.duration) - getSeconds(b.duration));
                const pick3 = byDuration.find(v => !isPicked(v.id));
                if (pick3) picked.push(pick3);

                // Slot 4: Newest
                const byDate = [...candidates].sort((a, b) => new Date(b.publishedAt) - new Date(a.publishedAt));
                const pick4 = byDate.find(v => !isPicked(v.id));
                if (pick4) picked.push(pick4);
            }

            // If we somehow didn't get 4 (e.g. not enough unique videos), fill with remaining best logic or leave as is.
            // But since picked is strictly distinct, we use that.
            let videos = picked;

            // 3. Apply UI Sort (Reordering the chosen 4)
            if (sortBy === 'views') {
                videos.sort((a, b) => b.views - a.views);
            } else if (sortBy === 'likes') {
                videos.sort((a, b) => b.likes - a.likes);
            } else if (sortBy === 'date') {
                videos.sort((a, b) => new Date(b.publishedAt) - new Date(a.publishedAt));
            } else if (sortBy === 'duration') {
                videos.sort((a, b) => getSeconds(b.duration) - getSeconds(a.duration));
            }

            return { ...item, videos };
        });
    }, [playlist, minLikes, sortBy]);

    // Auto-Select ONLY the Most Viewed Video from the displayed set
    useMemo(() => {
        if (!filteredPlaylist) return;

        const newSet = new Set();
        filteredPlaylist.forEach(item => {
            if (item.videos.length > 0) {
                // Find the one with maximum views among the 4 displayed
                const mostViewed = item.videos.reduce((prev, current) => {
                    return (prev.views > current.views) ? prev : current;
                });
                newSet.add(mostViewed.id);
            }
        });
        setSelectedVideos(newSet);
    }, [filteredPlaylist]);

    const formatNumber = (num) => {
        return new Intl.NumberFormat('en-US', { notation: "compact", compactDisplay: "short" }).format(num);
    };

    return (
        <main className="container">
            <VideoModal videoId={previewId} onClose={() => setPreviewId(null)} />

            <header style={{ textAlign: 'center', marginBottom: '4rem' }}>
                <h1 style={{
                    fontSize: '3.5rem',
                    fontWeight: '800',
                    marginBottom: '1rem',
                    background: 'linear-gradient(135deg, #ffffff 0%, #94a3b8 100%)',
                    WebkitBackgroundClip: 'text',
                    WebkitTextFillColor: 'transparent',
                    letterSpacing: '-2px'
                }}>
                    AutoYT Playlist
                </h1>
                <p style={{ color: '#94a3b8', fontSize: '1.2rem' }}>Transform your syllabus into a curated learning journey.</p>
                <div style={{ position: 'absolute', top: '2rem', right: '2rem', display: 'flex', gap: '1rem' }}>
                    {session ? (
                        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                            <span style={{ color: '#94a3b8', fontSize: '0.9rem' }}>{session.user.name}</span>
                            <button onClick={() => signOut()} style={{ background: 'rgba(255,255,255,0.1)', border: 'none', color: 'white', padding: '0.5rem 1rem', borderRadius: '8px', cursor: 'pointer' }}>Sign Out</button>
                        </div>
                    ) : (
                        <button onClick={() => signIn('google')} style={{ background: 'var(--primary)', border: 'none', color: 'white', padding: '0.5rem 1rem', borderRadius: '8px', cursor: 'pointer' }}>Sign In with Google</button>
                    )}

                    <button
                        onClick={fetchHistory}
                        style={{
                            background: 'transparent', border: '1px solid var(--glass-border)',
                            color: '#94a3b8', padding: '0.5rem 1rem', borderRadius: '8px',
                            cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.5rem'
                        }}
                    >
                        <HistoryIcon size={18} /> History
                    </button>
                </div>
            </header>

            {/* History Modal/Sidebar */}
            {showHistory && (
                <div style={{
                    position: 'fixed', inset: 0, zIndex: 1000,
                    background: 'rgba(0,0,0,0.8)', backdropFilter: 'blur(4px)',
                    display: 'flex', justifyContent: 'flex-end'
                }}>
                    <div className="glass-panel" style={{
                        width: '100%', maxWidth: '500px', height: '100%',
                        borderRadius: '0',
                        borderLeft: '1px solid rgba(255,255,255,0.1)',
                        borderRight: 'none', borderTop: 'none', borderBottom: 'none',
                        padding: '2rem',
                        overflowY: 'auto',
                        animation: 'slideInRight 0.3s cubic-bezier(0.16, 1, 0.3, 1)',
                        background: 'linear-gradient(135deg, rgba(255, 255, 255, 0.1), rgba(255, 255, 255, 0.01))',
                        backdropFilter: 'blur(30px)',
                        boxShadow: '-10px 0 40px rgba(0,0,0,0.5)',
                        borderLeft: '1px solid rgba(255,255,255,0.1)'
                    }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2.5rem' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.8rem' }}>
                                <HistoryIcon size={24} color="#a78bfa" />
                                <h2 style={{ fontSize: '1.8rem', fontWeight: '700', letterSpacing: '-0.5px', color: 'white' }}>History</h2>
                            </div>
                            <button
                                onClick={() => setShowHistory(false)}
                                style={{
                                    background: 'rgba(255,255,255,0.05)',
                                    border: 'none',
                                    color: '#94a3b8',
                                    width: '32px', height: '32px', borderRadius: '50%',
                                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                                    fontSize: '1.2rem', cursor: 'pointer',
                                    transition: 'all 0.2s'
                                }}
                                onMouseEnter={(e) => { e.currentTarget.style.background = 'rgba(255,255,255,0.1)'; e.currentTarget.style.color = 'white'; }}
                                onMouseLeave={(e) => { e.currentTarget.style.background = 'rgba(255,255,255,0.05)'; e.currentTarget.style.color = '#94a3b8'; }}
                            >
                                ×
                            </button>
                        </div>

                        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                            {history.length === 0 && (
                                <div style={{ textAlign: 'center', color: '#64748b', marginTop: '4rem' }}>
                                    <HistoryIcon size={48} style={{ opacity: 0.2, marginBottom: '1rem' }} />
                                    <p>No history yet</p>
                                </div>
                            )}
                            {history.map((item, i) => (
                                <div key={i}
                                    onClick={() => loadFromHistory(item)}
                                    style={{
                                        padding: '1.2rem',
                                        borderRadius: '16px',
                                        background: 'rgba(255,255,255,0.02)',
                                        border: '1px solid rgba(255,255,255,0.03)',
                                        cursor: 'pointer',
                                        transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
                                        display: 'flex', flexDirection: 'column', gap: '0.5rem',
                                        position: 'relative',
                                        overflow: 'hidden'
                                    }}
                                    onMouseEnter={(e) => {
                                        e.currentTarget.style.background = 'linear-gradient(135deg, rgba(255,255,255,0.05), rgba(255,255,255,0.02))';
                                        e.currentTarget.style.transform = 'translateY(-2px)';
                                        e.currentTarget.style.boxShadow = '0 10px 30px -10px rgba(0,0,0,0.5)';
                                        e.currentTarget.style.borderColor = 'rgba(255,255,255,0.1)';
                                    }}
                                    onMouseLeave={(e) => {
                                        e.currentTarget.style.background = 'rgba(255,255,255,0.02)';
                                        e.currentTarget.style.transform = 'translateY(0)';
                                        e.currentTarget.style.boxShadow = 'none';
                                        e.currentTarget.style.borderColor = 'rgba(255,255,255,0.03)';
                                    }}
                                >
                                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                        <div style={{ fontWeight: '600', fontSize: '1.1rem', color: '#f1f5f9', lineHeight: '1.4' }}>{item.name}</div>
                                        <div style={{
                                            background: 'rgba(139, 92, 246, 0.1)',
                                            color: '#a78bfa',
                                            fontSize: '0.7rem',
                                            fontWeight: '600',
                                            padding: '2px 8px',
                                            borderRadius: '20px',
                                            flexShrink: 0 // Prevent badge squishing
                                        }}>
                                            {item.topics.length} TOPICS
                                        </div>
                                    </div>

                                    <div style={{
                                        fontSize: '0.85rem',
                                        color: '#94a3b8',
                                        display: 'flex',
                                        alignItems: 'center',
                                        gap: '0.8rem',
                                        marginTop: '0.5rem',
                                        borderTop: '1px solid rgba(255,255,255,0.05)',
                                        paddingTop: '0.8rem'
                                    }}>
                                        <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                                            <Clock size={12} /> {new Date(item.createdAt).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}
                                        </span>
                                        {item.userName && (
                                            <>
                                                <span style={{ width: '3px', height: '3px', background: '#475569', borderRadius: '50%' }}></span>
                                                <span style={{ color: '#64748b' }}>{item.userName}</span>
                                            </>
                                        )}
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            )}

            {!playlist ? (
                <section className="glass-panel" style={{ maxWidth: '600px', margin: '0 auto', padding: '3rem' }}>
                    <form onSubmit={handleUpload} style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
                        <div style={{
                            border: '2px dashed rgba(255,255,255,0.1)',
                            padding: '4rem 2rem',
                            borderRadius: '16px',
                            textAlign: 'center',
                            cursor: 'pointer',
                            transition: 'all 0.2s'
                        }}
                            className="upload-zone"
                        >
                            <input
                                type="file"
                                accept=".pdf,.docx,.txt"
                                onChange={handleFileChange}
                                style={{ display: 'none' }}
                                id="file-upload"
                            />
                            <label htmlFor="file-upload" style={{ cursor: 'pointer', display: 'block' }}>
                                {file ? (
                                    <div style={{ color: '#22d3ee', fontSize: '1.2rem', fontWeight: '500', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem' }}>
                                        <FileText size={24} /> {file.name}
                                    </div>
                                ) : (
                                    <div style={{ color: '#94a3b8' }}>
                                        <div style={{ marginBottom: '1rem', display: 'flex', justifyContent: 'center' }}>
                                            <UploadCloud size={48} />
                                        </div>
                                        <p style={{ fontSize: '1.2rem', marginBottom: '0.5rem' }}>Click or Drop Syllabus Here</p>
                                        <p style={{ fontSize: '0.9rem', opacity: 0.5 }}>PDF, DOCX, TXT</p>
                                    </div>
                                )}
                            </label>
                        </div>

                        <button type="submit" className="btn" disabled={loading || !file} style={{ width: '100%', padding: '1rem' }}>
                            {loading ? (
                                <>
                                    <div className="loader"></div>
                                    <span>Processing Intelligence...</span>
                                </>
                            ) : (
                                <>
                                    <span>Generate Playlist</span>
                                    <Sparkles size={20} />
                                </>
                            )}
                        </button>

                        {error && <div style={{ color: '#fb7185', textAlign: 'center', background: 'rgba(251, 113, 133, 0.1)', padding: '1rem', borderRadius: '8px' }}>{error}</div>}
                    </form>
                </section>
            ) : (
                <>
                    {/* Control Bar */}
                    <div className="glass-panel" style={{
                        marginBottom: '3rem',
                        padding: '1.5rem',
                        position: 'sticky',
                        top: '20px',
                        zIndex: 100
                    }}>
                        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center', justifyContent: 'space-between' }}>
                            <input
                                type="text"
                                value={playlistName}
                                onChange={(e) => setPlaylistName(e.target.value)}
                                placeholder="Playlist Name"
                                style={{
                                    flex: 1,
                                    padding: '0.8rem 1rem',
                                    background: 'rgba(255, 255, 255, 0.03)',
                                    border: '1px solid rgba(255, 255, 255, 0.1)',
                                    borderRadius: '8px',
                                    color: 'white',
                                    outline: 'none',
                                    backdropFilter: 'blur(4px)',
                                    fontSize: '1rem',
                                    height: '46px' // Fixed height to match buttons/selects if needed
                                }}
                            />

                            <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
                                {/* Custom Sort Dropdown */}
                                <div style={{ position: 'relative', zIndex: 50 }}>
                                    <button
                                        onClick={() => setIsSortOpen(!isSortOpen)}
                                        style={{
                                            background: 'rgba(255, 255, 255, 0.03)',
                                            border: '1px solid rgba(255, 255, 255, 0.1)',
                                            borderRadius: '8px',
                                            padding: '0 1rem',
                                            color: '#e2e8f0',
                                            outline: 'none',
                                            cursor: 'pointer',
                                            height: '46px',
                                            fontSize: '0.9rem',
                                            display: 'flex',
                                            alignItems: 'center',
                                            gap: '0.8rem',
                                            minWidth: '160px',
                                            justifyContent: 'space-between',
                                            backdropFilter: 'blur(4px)'
                                        }}
                                    >
                                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                            <span style={{ color: '#94a3b8' }}>Sort:</span>
                                            <span style={{ fontWeight: '500' }}>{sortOptions[sortBy].label}</span>
                                        </div>
                                        <div style={{
                                            transform: isSortOpen ? 'rotate(180deg)' : 'rotate(0deg)',
                                            transition: 'transform 0.2s',
                                            opacity: 0.5
                                        }}>▼</div>
                                    </button>

                                    {/* Dropdown Menu */}
                                    {isSortOpen && (
                                        <>
                                            <div
                                                style={{ position: 'fixed', inset: 0, zIndex: 40 }}
                                                onClick={() => setIsSortOpen(false)}
                                            />
                                            <div style={{
                                                position: 'absolute',
                                                top: 'calc(100% + 8px)',
                                                right: 0,
                                                width: '100%',
                                                minWidth: '180px',
                                                background: 'rgba(15, 23, 42, 0.9)',
                                                backdropFilter: 'blur(12px)',
                                                border: '1px solid rgba(255,255,255,0.1)',
                                                borderRadius: '12px',
                                                padding: '0.5rem',
                                                display: 'flex',
                                                flexDirection: 'column',
                                                gap: '0.2rem',
                                                zIndex: 50,
                                                boxShadow: '0 10px 40px -10px rgba(0,0,0,0.5)',
                                                animation: 'slideIn 0.2s cubic-bezier(0.16, 1, 0.3, 1)'
                                            }}>
                                                {Object.entries(sortOptions).map(([key, { label, icon: Icon }]) => (
                                                    <div
                                                        key={key}
                                                        onClick={() => {
                                                            setSortBy(key);
                                                            setIsSortOpen(false);
                                                        }}
                                                        style={{
                                                            padding: '0.6rem 1rem',
                                                            borderRadius: '8px',
                                                            cursor: 'pointer',
                                                            display: 'flex',
                                                            alignItems: 'center',
                                                            gap: '0.8rem',
                                                            background: sortBy === key ? 'rgba(139, 92, 246, 0.15)' : 'transparent',
                                                            color: sortBy === key ? '#a78bfa' : '#94a3b8',
                                                            transition: 'all 0.1s'
                                                        }}
                                                        onMouseEnter={(e) => {
                                                            if (sortBy !== key) {
                                                                e.currentTarget.style.background = 'rgba(255,255,255,0.05)';
                                                                e.currentTarget.style.color = '#f1f5f9';
                                                            }
                                                        }}
                                                        onMouseLeave={(e) => {
                                                            if (sortBy !== key) {
                                                                e.currentTarget.style.background = 'transparent';
                                                                e.currentTarget.style.color = '#94a3b8';
                                                            }
                                                        }}
                                                    >
                                                        <Icon size={16} />
                                                        <span>{label}</span>
                                                        {sortBy === key && <div style={{ marginLeft: 'auto', width: '6px', height: '6px', borderRadius: '50%', background: '#a78bfa' }}></div>}
                                                    </div>
                                                ))}
                                            </div>
                                        </>
                                    )}
                                </div>
                                <button
                                    onClick={handleExportYouTube}
                                    disabled={selectedVideos.size === 0}
                                    style={{
                                        opacity: selectedVideos.size === 0 ? 0.5 : 1,
                                        height: '46px',
                                        display: 'flex',
                                        alignItems: 'center',
                                        gap: '0.8rem',
                                        background: 'linear-gradient(135deg, rgba(255,255,255,0.1), rgba(255,255,255,0.05))',
                                        backdropFilter: 'blur(10px)',
                                        border: '1px solid rgba(255, 255, 255, 0.1)',
                                        borderRadius: '12px',
                                        padding: '0 1.5rem',
                                        color: 'white',
                                        fontWeight: '600',
                                        cursor: 'pointer',
                                        boxShadow: '0 0 20px rgba(139, 92, 246, 0.3), inset 0 0 0 1px rgba(255,255,255,0.1)',
                                        transition: 'all 0.3s ease',
                                        fontSize: '0.95rem'
                                    }}
                                    onMouseEnter={(e) => {
                                        if (selectedVideos.size > 0) {
                                            e.currentTarget.style.boxShadow = '0 0 30px rgba(139, 92, 246, 0.5), inset 0 0 0 1px rgba(255,255,255,0.2)';
                                            e.currentTarget.style.background = 'linear-gradient(135deg, rgba(255,255,255,0.15), rgba(255,255,255,0.1))';
                                            e.currentTarget.style.transform = 'translateY(-2px)';
                                        }
                                    }}
                                    onMouseLeave={(e) => {
                                        if (selectedVideos.size > 0) {
                                            e.currentTarget.style.boxShadow = '0 0 20px rgba(139, 92, 246, 0.3), inset 0 0 0 1px rgba(255,255,255,0.1)';
                                            e.currentTarget.style.background = 'linear-gradient(135deg, rgba(255,255,255,0.1), rgba(255,255,255,0.05))';
                                            e.currentTarget.style.transform = 'translateY(0)';
                                        }
                                    }}
                                >
                                    <span>{session ? 'Save to YouTube' : 'Open in YouTube'}</span> <Youtube size={20} />
                                </button>
                            </div>
                        </div>
                    </div>

                    {filteredPlaylist.map((item, index) => (
                        <div key={index} style={{ marginBottom: '4rem' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1.5rem' }}>
                                <div style={{ width: '8px', height: '30px', background: 'linear-gradient(to bottom, #8b5cf6, #06b6d4)', borderRadius: '4px' }}></div>
                                <h2 style={{ fontSize: '1.8rem', fontWeight: '600' }}>{item.topic}</h2>
                            </div>

                            <div style={
                                viewMode === 'grid'
                                    ? { display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '2rem' }
                                    : { display: 'flex', flexDirection: 'column', gap: '1.5rem' }
                            }>
                                {item.videos.length > 0 ? (
                                    item.videos.map((video) => (
                                        <div
                                            key={video.id}
                                            className="card glass-panel"
                                            // CARD CLICK HANDLER
                                            onClick={() => {
                                                if (viewMode === 'grid') { // Only allow selection in Grid (Creation) mode
                                                    toggleSelection(video.id);
                                                }
                                            }}
                                            style={
                                                viewMode === 'grid' ? {
                                                    // GRID VIEW STYLES
                                                    border: selectedVideos.has(video.id) ? '1px solid #8b5cf6' : '1px solid rgba(255,255,255,0.15)',
                                                    transform: selectedVideos.has(video.id) ? 'scale(1.02)' : 'translateZ(0)',
                                                    boxShadow: selectedVideos.has(video.id)
                                                        ? '0 0 30px rgba(139, 92, 246, 0.4)'
                                                        : '0 4px 20px rgba(0,0,0,0.2)',
                                                    display: 'block',
                                                    background: selectedVideos.has(video.id)
                                                        ? 'linear-gradient(135deg, rgba(139, 92, 246, 0.1), rgba(139, 92, 246, 0.05))'
                                                        : 'linear-gradient(135deg, rgba(255,255,255,0.08), rgba(255,255,255,0.02))',
                                                    backdropFilter: 'blur(16px)',
                                                    transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                                                    cursor: 'pointer'
                                                } : {
                                                    // LIST VIEW STYLES (Read Only)
                                                    display: 'flex',
                                                    gap: '1.5rem',
                                                    padding: '1.2rem',
                                                    border: '1px solid rgba(255,255,255,0.1)', // Default border
                                                    borderRadius: '16px',
                                                    transform: 'translateZ(0)', // No scale effect
                                                    background: 'linear-gradient(90deg, rgba(255,255,255,0.05), rgba(255,255,255,0.01))', // Default BG
                                                    alignItems: 'flex-start',
                                                    boxShadow: '0 4px 10px rgba(0,0,0,0.1)',
                                                    backdropFilter: 'blur(16px)',
                                                    transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                                                    cursor: 'default' // Default cursor
                                                }
                                            }
                                        >
                                            {/* Interactive Areas Wrapper */}
                                            <div style={viewMode === 'list' ? { position: 'relative', width: '300px', flexShrink: 0, borderRadius: '12px', overflow: 'hidden' } : { position: 'relative' }}>
                                                {/* Checkbox (Professional Icon) - ONLY IN GRID MODE */}
                                                {viewMode === 'grid' && (
                                                    <div style={{ position: 'absolute', top: '12px', left: '12px', zIndex: 20 }}>
                                                        {selectedVideos.has(video.id) && (
                                                            <div style={{ animation: 'popIn 0.3s cubic-bezier(0.16, 1, 0.3, 1)', filter: 'drop-shadow(0 2px 4px rgba(0,0,0,0.2))' }}>
                                                                <CheckCircle
                                                                    size={32}
                                                                    color="#8b5cf6"
                                                                    strokeWidth={2.5}
                                                                />
                                                            </div>
                                                        )}
                                                    </div>
                                                )}

                                                {/* Play Button Overlay */}
                                                <div
                                                    className="play-overlay"
                                                    onClick={(e) => {
                                                        e.stopPropagation(); // Prevent toggling selection when clicking play
                                                        setPreviewId(video.id);
                                                    }}
                                                    style={{
                                                        position: 'absolute', inset: 0,
                                                        background: 'rgba(0,0,0,0.3)',
                                                        opacity: 0, transition: 'opacity 0.2s',
                                                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                                                        cursor: 'pointer'
                                                    }}
                                                    onMouseEnter={(e) => e.currentTarget.style.opacity = 1}
                                                    onMouseLeave={(e) => e.currentTarget.style.opacity = 0}
                                                >
                                                    <div style={{
                                                        background: 'rgba(255, 255, 255, 0.2)', backdropFilter: 'blur(4px)',
                                                        borderRadius: '50%',
                                                        width: viewMode === 'list' ? '48px' : '60px',
                                                        height: viewMode === 'list' ? '48px' : '60px',
                                                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                                                        border: '1px solid rgba(255,255,255,0.4)'
                                                    }}>
                                                        <Play size={viewMode === 'list' ? 24 : 32} fill="white" />
                                                    </div>
                                                </div>

                                                <img src={video.thumbnail} alt={video.title} style={{ width: '100%', aspectRatio: '16/9', objectFit: 'cover' }} />
                                                <div style={{ position: 'absolute', bottom: '8px', right: '8px', background: 'rgba(0,0,0,0.8)', padding: '2px 6px', borderRadius: '4px', fontSize: '0.7rem', fontWeight: '600' }}>
                                                    {video.duration.replace('PT', '').replace('H', ':').replace('M', ':').replace('S', '')}
                                                </div>
                                            </div>

                                            {/* Content Area */}
                                            <div style={viewMode === 'list' ? { flex: 1, padding: '0.5rem 0' } : { padding: '1.5rem' }}>
                                                <h3 style={{
                                                    fontSize: viewMode === 'list' ? '1.1rem' : '1rem',
                                                    marginBottom: '0.5rem',
                                                    lineHeight: '1.4',
                                                    fontWeight: '600',
                                                    height: viewMode === 'grid' ? '3rem' : 'auto',
                                                    overflow: 'hidden',
                                                    display: '-webkit-box',
                                                    WebkitLineClamp: 2,
                                                    WebkitBoxOrient: 'vertical'
                                                }}>
                                                    {video.title}
                                                </h3>
                                                <p style={{ fontSize: '0.9rem', color: '#94a3b8', marginBottom: '0.8rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                                    <span style={{ width: '20px', height: '20px', background: '#334155', borderRadius: '50%', display: 'inline-block' }}></span>
                                                    {video.channel}
                                                </p>
                                                {viewMode === 'list' && (
                                                    <p style={{ fontSize: '0.85rem', color: '#64748b', marginBottom: '1rem', lineHeight: '1.5', overflow: 'hidden', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical' }}>
                                                        {video.description || 'No description available for this video.'}
                                                    </p>
                                                )}
                                                <div style={{
                                                    display: 'flex', gap: '1.5rem', fontSize: '0.8rem', color: '#64748b',
                                                    borderTop: viewMode === 'grid' ? '1px solid rgba(255,255,255,0.05)' : 'none',
                                                    paddingTop: viewMode === 'grid' ? '1rem' : '0'
                                                }}>
                                                    <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}><Eye size={16} /> {formatNumber(video.views)} {viewMode === 'list' && 'views'}</span>
                                                    <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}><ThumbsUp size={16} /> {formatNumber(video.likes)} {viewMode === 'list' && 'likes'}</span>
                                                </div>
                                            </div>
                                        </div>
                                    ))
                                ) : (
                                    <p style={{ color: '#64748b', fontStyle: 'italic', gridColumn: '1/-1', textAlign: 'center', padding: '2rem' }}>
                                        No videos match your current filters. Try adjusting them.
                                    </p>
                                )}
                            </div>
                        </div>
                    ))}
                </>
            )}

            {/* Save Status Modal */}
            {saveStatus !== 'idle' && (
                <div style={{
                    position: 'fixed', inset: 0, zIndex: 2000,
                    background: 'rgba(0,0,0,0.6)', backdropFilter: 'blur(5px)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center'
                }}>
                    <div className="glass-panel" style={{
                        padding: '3rem', borderRadius: '24px',
                        textAlign: 'center', maxWidth: '400px', width: '90%',
                        animation: 'scaleIn 0.3s cubic-bezier(0.16, 1, 0.3, 1)',
                        display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1.5rem',
                        border: '1px solid rgba(255,255,255,0.1)'
                    }}>
                        {saveStatus === 'loading' && (
                            <>
                                <div className="loader" style={{ width: '48px', height: '48px', borderWidth: '4px' }}></div>
                                <h3 style={{ fontSize: '1.2rem', fontWeight: '500' }}>{saveMessage}</h3>
                            </>
                        )}
                        {saveStatus === 'success' && (
                            <>
                                <div style={{
                                    width: '64px', height: '64px', background: 'rgba(34, 197, 94, 0.2)',
                                    borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center',
                                    color: '#4ade80'
                                }}>
                                    <ThumbsUp size={32} />
                                </div>
                                <h3 style={{ fontSize: '1.2rem', fontWeight: '600', color: 'white' }}>Success!</h3>
                                <p style={{ color: '#94a3b8' }}>{saveMessage}</p>
                            </>
                        )}
                        {saveStatus === 'error' && (
                            <>
                                <div style={{
                                    width: '64px', height: '64px', background: 'rgba(239, 68, 68, 0.2)',
                                    borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center',
                                    color: '#f87171'
                                }}>
                                    <span style={{ fontSize: '2rem' }}>!</span>
                                </div>
                                <h3 style={{ fontSize: '1.2rem', fontWeight: '600', color: 'white' }}>Error</h3>
                                <p style={{ color: '#94a3b8' }}>{saveMessage}</p>
                                <button onClick={() => setSaveStatus('idle')} className="btn">Close</button>
                            </>
                        )}
                    </div>
                </div>
            )}
        </main>
    );
}
