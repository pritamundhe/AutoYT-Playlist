# 🎓 AutoYT-Playlist: The Ultimate Exam Hack 🚀

**Your One-Night-Before-Exam Saviour**

[![Next.js](https://img.shields.io/badge/Next.js-14+-black.svg)](https://nextjs.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

### 🧐 What is this?

Ever realized you have an exam tomorrow morning and you haven't started studying? Yeah, we've all been there. 😅

**AutoYT-Playlist** is a fun project born out of that exact real-world problem. Instead of wasting precious hours searching for the right tutorials on YouTube, this tool puts you on the **fast track**.

Simply upload your syllabus, and boom—it automatically generates a curated YouTube playlist covering every topic you need to know. It's designed to help students speed-run their syllabus ⏱️ the night before the chaos begins.

### ✨ Why use it?

- ⚡ **Instant Playlists**: Stop searching, start studying. Get a focused playlist in seconds.
- 🧠 **Smart Matching**: It reads your syllabus (PDF, Docx, etc.) and finds the best matching videos.
- 🎯 **Topic-by-Topic**: Every part of your course is covered in order.
- 🎨 **Clean & Simple**: A straightforward interface because your brain is already stressed enough.

---

### 🚀 How to Run It

Want to run this yourself? Here is the quick setup guide.

#### Prerequisites
- Node.js 18+
- MongoDB (Local or Atlas)
- A YouTube Data API Key (It's free!)

#### 1. Clone the Repo
```bash
git clone https://github.com/pritamundhe/AutoYT-Playlist.git
cd AutoYT-Playlist
```

#### 2. Install Dependencies �
Everything is handled by the frontend now (Fullstack Next.js magic).
```bash
cd frontend
npm install
```

#### 3. Environment Setup 🔑
Create a `.env.local` file in the `frontend` folder and add your keys:
```env
GOOGLE_API_KEY=your_youtube_api_key_here
MONGODB_URI=your_mongodb_connection_string
NEXTAUTH_SECRET=your_secret_key
NEXTAUTH_URL=http://localhost:3000
```

#### 4. Run It 🏃‍♂️
Start the development server:
```bash
npm run dev
```
Open `http://localhost:3000` and start cramming! 📚

---

### 🛠️ Tech Stack
(For the curious ones)
- **Framework**: Next.js 14 (Fullstack)
- **Language**: JavaScript/Node.js
- **Database**: MongoDB (via Mongoose)
- **Document Parsing**: pdf-parse, mammoth
- **Authentication**: NextAuth.js

---

### 🤝 Contributing
Found a way to make it even faster? Pull requests are welcome! Let's help more students survive finals week.

### 📄 License
MIT License - do whatever you want with it!

---
**Built with ☕ and panic for students everywhere.**
