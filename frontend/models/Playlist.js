import mongoose from 'mongoose';

const PlaylistSchema = new mongoose.Schema({
    name: { type: String, required: true },
    userName: String,
    topics: [{
        topic: String,
        videos: [{
            id: String,
            title: String,
            thumbnail: String,
            channel: String,
            views: Number,
            likes: Number,
            duration: String,
            url: String
        }]
    }],
    createdAt: { type: Date, default: Date.now }
});

export default mongoose.models.Playlist || mongoose.model('Playlist', PlaylistSchema);
