'use client';

import { useState, useEffect } from 'react';
import { FileText, MessageSquare, CheckCircle2, XCircle, LogOut, User as UserIcon } from 'lucide-react';
import { FileUploader } from '@/components/FileUploader';
import { ChatInterface } from '@/components/ChatInterface';
import { ProtectedRoute } from '@/components/ProtectedRoute';
import { healthCheck } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';

export default function Home() {
  const { user, logout } = useAuth();
  const [sessionId] = useState(() => `user_${Date.now()}`);
  const [activeTab, setActiveTab] = useState<'upload' | 'chat'>('upload');
  const [backendStatus, setBackendStatus] = useState<'checking' | 'online' | 'offline'>('checking');
  const [showUserMenu, setShowUserMenu] = useState(false);

  useEffect(() => {
    const checkBackend = async () => {
      try {
        await healthCheck();
        setBackendStatus('online');
      } catch {
        setBackendStatus('offline');
      }
    };

    checkBackend();
    const interval = setInterval(checkBackend, 30000); // Check every 30s

    return () => clearInterval(interval);
  }, []);

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-50">
        {/* Header */}
        <header className="bg-white shadow-sm">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="bg-blue-600 rounded-lg p-2">
                  <FileText className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h1 className="text-2xl font-bold text-gray-900">
                    Adamani AI RAG
                  </h1>
                  <p className="text-sm text-gray-600">
                    Invoice & PDF Processing
                  </p>
                </div>
              </div>

              <div className="flex items-center space-x-4">
                {/* Backend Status */}
                <div className="flex items-center space-x-2">
                  {backendStatus === 'online' ? (
                    <>
                      <CheckCircle2 className="w-5 h-5 text-green-500" />
                      <span className="text-sm text-gray-600">Online</span>
                    </>
                  ) : backendStatus === 'offline' ? (
                    <>
                      <XCircle className="w-5 h-5 text-red-500" />
                      <span className="text-sm text-gray-600">Offline</span>
                    </>
                  ) : (
                    <>
                      <div className="w-5 h-5 border-2 border-gray-300 border-t-blue-600 rounded-full animate-spin" />
                      <span className="text-sm text-gray-600">Checking...</span>
                    </>
                  )}
                </div>

                {/* User Menu */}
                <div className="relative">
                  <button
                    onClick={() => setShowUserMenu(!showUserMenu)}
                    className="flex items-center space-x-2 px-3 py-2 rounded-lg hover:bg-gray-100 transition-colors"
                  >
                    <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
                      <UserIcon className="w-5 h-5 text-white" />
                    </div>
                    <div className="text-left hidden md:block">
                      <p className="text-sm font-medium text-gray-900">
                        {user?.full_name || 'User'}
                      </p>
                      <p className="text-xs text-gray-500">{user?.email}</p>
                    </div>
                  </button>

                  {showUserMenu && (
                    <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-gray-200 py-1 z-10">
                      <button
                        onClick={() => {
                          logout();
                          setShowUserMenu(false);
                        }}
                        className="w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-100 flex items-center space-x-2"
                      >
                        <LogOut className="w-4 h-4" />
                        <span>Logout</span>
                      </button>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Panel - Upload */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow-lg p-6">
              <div className="flex items-center space-x-2 mb-4">
                <FileText className="w-5 h-5 text-blue-600" />
                <h2 className="text-lg font-semibold text-gray-900">
                  Upload Documents
                </h2>
              </div>

              <FileUploader
                onUploadSuccess={() => {
                  // Automatically switch to chat tab after successful upload
                  setActiveTab('chat');
                }}
              />

              <div className="mt-6 p-4 bg-blue-50 rounded-lg">
                <h3 className="text-sm font-semibold text-blue-900 mb-2">
                  Supported Documents
                </h3>
                <ul className="text-xs text-blue-800 space-y-1">
                  <li>• PDF documents (digital & scanned)</li>
                  <li>• Invoices and receipts</li>
                  <li>• Scanned images (PNG, JPG, TIFF)</li>
                  <li>• Multi-page documents</li>
                </ul>
              </div>
            </div>
          </div>

          {/* Right Panel - Chat */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-lg shadow-lg h-[calc(100vh-200px)] flex flex-col">
              <ChatInterface sessionId={sessionId} />
            </div>

            {/* Quick Questions */}
            <div className="mt-4 p-4 bg-white rounded-lg shadow">
              <h3 className="text-sm font-semibold text-gray-900 mb-3">
                💡 Example Questions
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                {[
                  'What is the total amount on the invoice?',
                  'Who is the vendor?',
                  'What is the invoice date?',
                  'List all line items',
                  'What is the tax amount?',
                  'What is the payment method?',
                ].map((question, index) => (
                  <button
                    key={index}
                    onClick={() => {
                      // You can implement click-to-fill functionality here
                      setActiveTab('chat');
                    }}
                    className="text-left text-xs p-2 bg-gray-50 hover:bg-blue-50 rounded border border-gray-200 hover:border-blue-300 transition-colors"
                  >
                    {question}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <footer className="mt-8 text-center text-sm text-gray-600">
          <p>
            Powered by{' '}
            <span className="font-semibold text-blue-600">
              Ollama + ChromaDB + LangChain
            </span>
          </p>
        </footer>
      </main>
    </div>
    </ProtectedRoute>
  );
}
