
import './globals.css'
import { Providers } from '../components/Providers';

export const metadata = {
    title: 'AutoYT-Playlist',
    description: 'Generate YouTube playlists from your syllabus',
}

export default function RootLayout({ children }) {
    return (
        <html lang="en">
            <body>
                <Providers>{children}</Providers>
            </body>
        </html>
    )
}
