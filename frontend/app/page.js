
'use client';

import { useState, useMemo } from 'react';
import VideoModal from '../components/VideoModal';

export default function Home() {
    const [file, setFile] = useState(null);
    const [loading, setLoading] = useState(false);
    const [playlist, setPlaylist] = useState(null);
    const [error, setError] = useState(null);

    // State for Features
    const [playlistName, setPlaylistName] = useState('');
    const [minViews, setMinViews] = useState(0);
    const [minLikes, setMinLikes] = useState(0);
    const [sortBy, setSortBy] = useState('relevance');

    // Preview & Export
    const [previewId, setPreviewId] = useState(null);
    const [selectedVideos, setSelectedVideos] = useState(new Set());

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
            // Removed auto-selection logic here

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

    const handleExportYouTube = () => {
        if (selectedVideos.size === 0) return;
        const ids = Array.from(selectedVideos).join(',');
        window.open(`http://www.youtube.com/watch_videos?video_ids=${ids}`, '_blank');
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
    };

    // Filter Logic
    const filteredPlaylist = useMemo(() => {
        if (!playlist) return null;

        return playlist.map(item => {
            let videos = item.videos.filter(v => (v.views >= minViews) && (v.likes >= minLikes));

            if (sortBy === 'views') {
                videos.sort((a, b) => b.views - a.views);
            } else if (sortBy === 'likes') {
                videos.sort((a, b) => b.likes - a.likes);
            } else if (sortBy === 'date') {
                videos.sort((a, b) => new Date(b.publishedAt) - new Date(a.publishedAt));
            }

            return { ...item, videos };
        });
    }, [playlist, minViews, minLikes, sortBy]);

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
            </header>

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
                                    <div style={{ color: '#22d3ee', fontSize: '1.2rem', fontWeight: '500' }}>📄 {file.name}</div>
                                ) : (
                                    <div style={{ color: '#94a3b8' }}>
                                        <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>📂</div>
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
                            ) : 'Generate Playlist ✨'}
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
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '2rem', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.5rem' }}>
                            <div style={{ display: 'flex', gap: '1.5rem', flex: 1 }}>
                                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', flex: 1 }}>
                                    <label style={{ fontSize: '0.8rem', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '1px' }}>Playlist Name</label>
                                    <input
                                        type="text"
                                        value={playlistName}
                                        onChange={(e) => setPlaylistName(e.target.value)}
                                        placeholder="My Playlist"
                                        style={{ width: '100%', padding: '0.8rem' }}
                                    />
                                </div>
                            </div>

                            <div style={{ display: 'flex', gap: '1rem' }}>
                                <button className="btn btn-secondary" onClick={handleDownloadJSON} disabled={selectedVideos.size === 0} style={{ opacity: selectedVideos.size === 0 ? 0.5 : 1 }}>
                                    Download JSON 📥
                                </button>
                                <button className="btn" onClick={handleExportYouTube} disabled={selectedVideos.size === 0} style={{ opacity: selectedVideos.size === 0 ? 0.5 : 1 }}>
                                    Open in YouTube 📺
                                </button>
                            </div>
                        </div>

                        <div style={{ display: 'flex', gap: '2rem', paddingTop: '1.5rem', borderTop: '1px solid rgba(255,255,255,0.05)' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                                <label style={{ color: '#94a3b8' }}>Sort:</label>
                                <select value={sortBy} onChange={(e) => setSortBy(e.target.value)}>
                                    <option value="relevance">Relevance</option>
                                    <option value="views">Most Views</option>
                                    <option value="likes">Most Likes</option>
                                    <option value="date">Newest</option>
                                </select>
                            </div>

                            <div style={{ flex: 1, display: 'flex', gap: '2rem' }}>
                                <div style={{ flex: 1 }}>
                                    <label style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem', fontSize: '0.8rem', color: '#94a3b8' }}>
                                        <span>Min Views</span>
                                        <span>{formatNumber(minViews)}</span>
                                    </label>
                                    <input
                                        type="range"
                                        min="0"
                                        max="1000000"
                                        step="10000"
                                        value={minViews}
                                        onChange={(e) => setMinViews(Number(e.target.value))}
                                        style={{ width: '100%', accentColor: '#8b5cf6' }}
                                    />
                                </div>
                            </div>
                        </div>
                    </div>

                    {filteredPlaylist.map((item, index) => (
                        <div key={index} style={{ marginBottom: '4rem' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1.5rem' }}>
                                <div style={{ width: '8px', height: '30px', background: 'linear-gradient(to bottom, #8b5cf6, #06b6d4)', borderRadius: '4px' }}></div>
                                <h2 style={{ fontSize: '1.8rem', fontWeight: '600' }}>{item.topic}</h2>
                            </div>

                            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '2rem' }}>
                                {item.videos.length > 0 ? (
                                    item.videos.map((video) => (
                                        <div
                                            key={video.id}
                                            className="card"
                                            style={{
                                                border: selectedVideos.has(video.id) ? '1px solid #8b5cf6' : '1px solid rgba(255,255,255,0.08)',
                                                transform: selectedVideos.has(video.id) ? 'scale(1.02)' : 'none',
                                                boxShadow: selectedVideos.has(video.id) ? '0 0 20px rgba(139, 92, 246, 0.2)' : 'none'
                                            }}
                                        >
                                            {/* Interactive Areas */}
                                            <div style={{ position: 'relative' }}>
                                                {/* Checkbox */}
                                                <div style={{ position: 'absolute', top: '12px', left: '12px', zIndex: 10 }}>
                                                    <input
                                                        type="checkbox"
                                                        checked={selectedVideos.has(video.id)}
                                                        onChange={() => toggleSelection(video.id)}
                                                        style={{
                                                            width: '24px',
                                                            height: '24px',
                                                            accentColor: '#8b5cf6',
                                                            cursor: 'pointer',
                                                            filter: 'drop-shadow(0 2px 4px rgba(0,0,0,0.5))'
                                                        }}
                                                    />
                                                </div>

                                                {/* Play Button */}
                                                <div
                                                    className="play-overlay"
                                                    onClick={() => setPreviewId(video.id)}
                                                    style={{
                                                        position: 'absolute',
                                                        top: 0, left: 0, right: 0, bottom: 0,
                                                        background: 'rgba(0,0,0,0.3)',
                                                        opacity: 0,
                                                        transition: 'opacity 0.2s',
                                                        display: 'flex',
                                                        alignItems: 'center',
                                                        justifyContent: 'center',
                                                        cursor: 'pointer'
                                                    }}
                                                    onMouseEnter={(e) => e.currentTarget.style.opacity = 1}
                                                    onMouseLeave={(e) => e.currentTarget.style.opacity = 0}
                                                >
                                                    <div style={{
                                                        background: 'rgba(255, 255, 255, 0.2)',
                                                        backdropFilter: 'blur(4px)',
                                                        borderRadius: '50%',
                                                        width: '60px',
                                                        height: '60px',
                                                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                                                        border: '1px solid rgba(255,255,255,0.4)'
                                                    }}>
                                                        <span style={{ fontSize: '24px', marginLeft: '4px' }}>▶</span>
                                                    </div>
                                                </div>

                                                <img src={video.thumbnail} alt={video.title} style={{ width: '100%', aspectRatio: '16/9', objectFit: 'cover' }} />

                                                <div style={{ position: 'absolute', bottom: '10px', right: '10px', background: 'rgba(0,0,0,0.8)', padding: '2px 8px', borderRadius: '4px', fontSize: '0.75rem', fontWeight: '600' }}>
                                                    {video.duration.replace('PT', '').replace('H', ':').replace('M', ':').replace('S', '')}
                                                </div>
                                            </div>

                                            <div style={{ padding: '1.5rem' }}>
                                                <h3 style={{ fontSize: '1rem', marginBottom: '0.8rem', lineHeight: '1.5', height: '3rem', overflow: 'hidden', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical' }}>
                                                    {video.title}
                                                </h3>
                                                <p style={{ fontSize: '0.85rem', color: '#94a3b8', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                                    <span style={{ width: '24px', height: '24px', background: '#334155', borderRadius: '50%', display: 'inline-block' }}></span>
                                                    {video.channel}
                                                </p>
                                                <div style={{ display: 'flex', gap: '1rem', fontSize: '0.8rem', color: '#64748b', borderTop: '1px solid rgba(255,255,255,0.05)', paddingTop: '1rem' }}>
                                                    <span>👁️ {formatNumber(video.views)}</span>
                                                    <span>👍 {formatNumber(video.likes)}</span>
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
        </main>
    );
}
