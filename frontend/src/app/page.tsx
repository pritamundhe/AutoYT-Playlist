'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Upload, FileText, Sparkles } from 'lucide-react';
import { documentAPI, topicAPI } from '@/services/api';
import { useAppStore } from '@/lib/store';

export default function Home() {
    const router = useRouter();
    const { setCurrentDocument, setIsLoading, setError } = useAppStore();
    const [file, setFile] = useState<File | null>(null);
    const [isDragging, setIsDragging] = useState(false);

    const handleFileSelect = (selectedFile: File) => {
        const allowedTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain'];

        if (!allowedTypes.includes(selectedFile.type)) {
            setError('Please upload a PDF, DOCX, or TXT file');
            return;
        }

        setFile(selectedFile);
        setError(null);
    };

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(false);

        const droppedFile = e.dataTransfer.files[0];
        if (droppedFile) {
            handleFileSelect(droppedFile);
        }
    };

    const handleUpload = async () => {
        if (!file) return;

        setIsLoading(true);
        setError(null);

        try {
            // Upload document
            const document = await documentAPI.upload(file);
            setCurrentDocument(document);

            // Start topic extraction
            await topicAPI.extract(document.id);

            // Navigate to topics page
            router.push(`/topics?id=${document.id}`);
        } catch (error: any) {
            setError(error.response?.data?.detail || 'Failed to upload document');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <main className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
            {/* Header */}
            <header className="bg-white/80 backdrop-blur-sm border-b border-gray-200 sticky top-0 z-10">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-3">
                            <Sparkles className="w-8 h-8 text-primary-600" />
                            <h1 className="text-2xl font-bold text-gray-900">
                                YouTube Playlist Generator
                            </h1>
                        </div>
                        <div className="text-sm text-gray-600">
                            AI-Powered Academic Learning
                        </div>
                    </div>
                </div>
            </header>

            {/* Main Content */}
            <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
                <div className="text-center mb-12 animate-fade-in">
                    <h2 className="text-4xl font-bold text-gray-900 mb-4">
                        Transform Your Syllabus into a Learning Playlist
                    </h2>
                    <p className="text-xl text-gray-600 max-w-2xl mx-auto">
                        Upload your academic syllabus and let AI generate a curated YouTube playlist
                        using advanced NLP and multi-criteria ranking
                    </p>
                </div>

                {/* Upload Area */}
                <div className="bg-white rounded-2xl shadow-xl p-8 mb-8 animate-slide-up">
                    <div
                        className={`border-3 border-dashed rounded-xl p-12 text-center transition-all ${isDragging
                                ? 'border-primary-500 bg-primary-50'
                                : 'border-gray-300 hover:border-primary-400'
                            }`}
                        onDragOver={(e) => {
                            e.preventDefault();
                            setIsDragging(true);
                        }}
                        onDragLeave={() => setIsDragging(false)}
                        onDrop={handleDrop}
                    >
                        <Upload className="w-16 h-16 text-gray-400 mx-auto mb-4" />

                        {file ? (
                            <div className="space-y-4">
                                <div className="flex items-center justify-center space-x-3 text-primary-600">
                                    <FileText className="w-6 h-6" />
                                    <span className="font-medium">{file.name}</span>
                                </div>
                                <button
                                    onClick={handleUpload}
                                    className="px-8 py-3 bg-primary-600 text-white rounded-lg font-medium hover:bg-primary-700 transition-colors"
                                >
                                    Process Syllabus
                                </button>
                            </div>
                        ) : (
                            <>
                                <p className="text-lg text-gray-700 mb-2">
                                    Drag and drop your syllabus here
                                </p>
                                <p className="text-sm text-gray-500 mb-4">
                                    or click to browse (PDF, DOCX, TXT)
                                </p>
                                <label className="inline-block px-6 py-3 bg-primary-600 text-white rounded-lg font-medium cursor-pointer hover:bg-primary-700 transition-colors">
                                    Choose File
                                    <input
                                        type="file"
                                        className="hidden"
                                        accept=".pdf,.docx,.txt"
                                        onChange={(e) => {
                                            const selectedFile = e.target.files?.[0];
                                            if (selectedFile) handleFileSelect(selectedFile);
                                        }}
                                    />
                                </label>
                            </>
                        )}
                    </div>
                </div>

                {/* Features */}
                <div className="grid md:grid-cols-3 gap-6">
                    <div className="bg-white rounded-xl p-6 shadow-md">
                        <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-4">
                            <FileText className="w-6 h-6 text-blue-600" />
                        </div>
                        <h3 className="font-semibold text-gray-900 mb-2">Smart Extraction</h3>
                        <p className="text-sm text-gray-600">
                            Advanced NLP extracts topics, units, and keywords from your syllabus
                        </p>
                    </div>

                    <div className="bg-white rounded-xl p-6 shadow-md">
                        <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mb-4">
                            <Sparkles className="w-6 h-6 text-purple-600" />
                        </div>
                        <h3 className="font-semibold text-gray-900 mb-2">AI Ranking</h3>
                        <p className="text-sm text-gray-600">
                            Multi-criteria ranking ensures the best educational videos
                        </p>
                    </div>

                    <div className="bg-white rounded-xl p-6 shadow-md">
                        <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mb-4">
                            <Upload className="w-6 h-6 text-green-600" />
                        </div>
                        <h3 className="font-semibold text-gray-900 mb-2">Easy Export</h3>
                        <p className="text-sm text-gray-600">
                            Export to YouTube, JSON, or CSV with one click
                        </p>
                    </div>
                </div>
            </div>
        </main>
    );
}
