
import { NextResponse } from 'next/server';
import { searchVideos } from '../../../lib/youtube';
import pdf from 'pdf-parse';
import mammoth from 'mammoth';

export async function POST(request) {
    try {
        const data = await request.formData();
        const file = data.get('file');

        if (!file) {
            return NextResponse.json({ error: 'No file uploaded' }, { status: 400 });
        }

        const bytes = await file.arrayBuffer();
        const buffer = Buffer.from(bytes);

        let text = '';

        if (file.name.endsWith('.pdf')) {
            const data = await pdf(buffer);
            text = data.text;
        } else if (file.name.endsWith('.docx') || file.name.endsWith('.doc')) {
            const result = await mammoth.extractRawText({ buffer });
            text = result.value;
        } else if (file.name.endsWith('.txt')) {
            text = buffer.toString('utf-8');
        } else {
            return NextResponse.json({ error: 'Unsupported file type' }, { status: 400 });
        }

        // Simple topic extraction (split by lines, filter short lines)
        // In a real app, this would use NLP
        const lines = text.split('\n')
            .map(line => line.trim())
            .filter(line => line.length > 5 && line.length < 100);

        // Take top 5 lines as "topics" for demo purposes to avoid quota usage
        const topics = lines.slice(0, 5);

        const results = [];
        for (const topic of topics) {
            const videos = await searchVideos(topic + ' tutorial', 3);
            if (videos.length > 0) {
                results.push({
                    topic,
                    videos
                });
            }
        }

        return NextResponse.json({
            playlist: results,
            rawText: text.substring(0, 500) + '...'
        });

    } catch (error) {
        console.error('Upload Error:', error);
        return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
    }
}
