
import './globals.css'

export const metadata = {
    title: 'AutoYT-Playlist',
    description: 'Generate YouTube playlists from your syllabus',
}

export default function RootLayout({ children }) {
    return (
        <html lang="en">
            <body>{children}</body>
        </html>
    )
}
