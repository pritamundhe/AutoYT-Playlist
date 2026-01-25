import { NextResponse } from 'next/server';
import dbConnect from '../../../lib/mongodb';
import Playlist from '../../../models/Playlist';

export async function POST(req) {
    try {
        await dbConnect();
        const body = await req.json();

        const playlist = await Playlist.create(body);

        return NextResponse.json({ success: true, playlist }, { status: 201 });
    } catch (error) {
        return NextResponse.json({ error: error.message }, { status: 500 });
    }
}

export async function GET() {
    try {
        await dbConnect();
        // Fetch latest 20 playlists
        const playlists = await Playlist.find().sort({ createdAt: -1 }).limit(20);
        return NextResponse.json({ playlists });
    } catch (error) {
        return NextResponse.json({ error: error.message }, { status: 500 });
    }
}
