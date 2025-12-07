// lib/api.ts

import type {
  ChatRequest,
  ChatResponse,
  DocumentResponse,
  HealthResponse,
  AsyncChatInitResponse,
  ChatStatusResponse,
} from '@/types';

// Trim whitespace to avoid URL errors
const API_BASE = (process.env.NEXT_PUBLIC_API_URL || 'https://adamani-ai-rag-backend.onrender.com').trim();

class APIError extends Error {
  constructor(
    message: string,
    public status?: number,
    public details?: any
  ) {
    super(message);
    this.name = 'APIError';
  }
}

// Get auth token from localStorage
function getAuthToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('auth_token');
}

// Get auth headers
function getAuthHeaders(): HeadersInit {
  const token = getAuthToken();
  const headers: HeadersInit = {};
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new APIError(
      error.detail || 'An error occurred',
      response.status,
      error
    );
  }
  return response.json();
}

// Check upload status — tolerate 404 during startup
async function checkUploadStatus(uploadId: string): Promise<any> {
  const response = await fetch(`${API_BASE}/documents/status/${uploadId}`, {
    method: 'GET',
    headers: getAuthHeaders(),
  });

  // If not found, assume still initializing
  if (response.status === 404) {
    return { status: 'processing', message: 'Upload ID not yet registered' };
  }

  if (!response.ok) {
    throw new APIError('Failed to check upload status', response.status);
  }

  return response.json();
}

export async function uploadDocument(
  file: File,
  useOCR: boolean = false
): Promise<DocumentResponse> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('use_ocr', useOCR.toString()); // ✅ Send as form field

  // Step 1: Upload file
  const uploadResponse = await fetch(`${API_BASE}/documents/upload`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: formData,
    // ⚠️ Do NOT set Content-Type — browser sets multipart boundary automatically
  });

  const uploadData = await handleResponse<any>(uploadResponse);

  if (uploadData.status !== 'processing') {
    throw new APIError(uploadData.message || 'Upload initiation failed');
  }

  const uploadId = uploadData.upload_id;

  // Step 2: Poll for completion
  const pollInterval = 2000; // 2 seconds
  const maxAttempts = 30;    // Total timeout: 60 seconds
  let attempts = 0;

  while (attempts < maxAttempts) {
    attempts++;
    await new Promise(resolve => setTimeout(resolve, pollInterval));

    try {
      const statusData = await checkUploadStatus(uploadId);

      if (statusData.status === 'success') {
        return {
          status: statusData.status,
          documents_added: statusData.documents_added,
          chunks_created: statusData.chunks_created,
          message: statusData.message,
        };
      } else if (statusData.status === 'error') {
        throw new APIError(statusData.message || 'Document processing failed');
      }
      // else: still 'processing' → continue
    } catch (err) {
      // On first attempt, 404 is normal; ignore and retry
      if (attempts === 1 && err instanceof APIError && err.status === 404) {
        continue;
      }
      // Re-throw all other errors
      throw err;
    }
  }

  throw new APIError('Upload timeout: Processing took longer than 60 seconds');
}

// ==============
// Chat Functions
// ==============

export async function checkChatStatus(
  requestId: string
): Promise<ChatStatusResponse> {
  const response = await fetch(`${API_BASE}/chat/status/${requestId}`, {
    method: 'GET',
    headers: getAuthHeaders(),
  });

  if (response.status === 404) {
    return { status: 'processing', message: 'Request not yet registered' };
  }

  return handleResponse<ChatStatusResponse>(response);
}

export async function sendChatMessageStream(
  request: ChatRequest,
  onToken: (token: string) => void,
  onSources: (sources: any[]) => void,
  onComplete: () => void,
  onError: (error: string) => void
): Promise<void> {
  try {
    const response = await fetch(`${API_BASE}/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders(),
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const errorText = await response.text().catch(() => 'Unknown error');
      throw new APIError(`Streaming failed: ${errorText}`, response.status);
    }

    const reader = response.body?.getReader();
    if (!reader) {
      throw new APIError('Streaming not supported: no response body');
    }

    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const messages = buffer.split('\n\n');
      buffer = messages.pop() || '';

      for (const msg of messages) {
        if (!msg.trim() || !msg.startsWith('data: ')) continue;

        try {
          const payload = JSON.parse(msg.slice(6)); // remove 'data: '

          switch (payload.type) {
            case 'token':
              onToken(payload.token || '');
              break;
            case 'sources':
              onSources(payload.sources || []);
              break;
            case 'end': // or 'done'
              onComplete();
              return;
            case 'error':
              onError(payload.error || 'Unknown stream error');
              return;
          }
        } catch (e) {
          console.warn('Failed to parse SSE message:', msg, e);
        }
      }
    }

    onComplete(); // in case stream ends without 'end' event
  } catch (error: any) {
    const message = error.message || 'Streaming connection failed';
    onError(message);
    throw error;
  }
}

// Legacy polling-based chat (optional)
export async function sendChatMessage(
  request: ChatRequest,
  onProgress?: (status: string) => void
): Promise<ChatResponse> {
  const initRes = await fetch(`${API_BASE}/chat/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...getAuthHeaders(),
    },
    body: JSON.stringify(request),
  });

  const initData = await handleResponse<AsyncChatInitResponse>(initRes);
  const requestId = initData.request_id;

  const pollInterval = 1000;
  const maxAttempts = 120;
  let attempts = 0;

  while (attempts < maxAttempts) {
    attempts++;
    if (onProgress) onProgress(`Processing... (${attempts}s)`);

    await new Promise(resolve => setTimeout(resolve, pollInterval));

    const statusData = await checkChatStatus(requestId);

    if (statusData.status === 'completed') {
      return {
        answer: statusData.answer!,
        sources: statusData.sources || [],
        session_id: statusData.session_id!,
      };
    } else if (statusData.status === 'error') {
      throw new APIError(statusData.message || 'Chat processing failed');
    }
  }

  throw new APIError('Chat request timed out after 2 minutes');
}

// ==============
// Other Endpoints
// ==============

export async function addTexts(
  texts: string[],
  metadatas?: Record<string, any>[]
): Promise<DocumentResponse> {
  const response = await fetch(`${API_BASE}/documents/texts`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...getAuthHeaders(),
    },
    body: JSON.stringify({ texts, metadatas }),
  });
  return handleResponse<DocumentResponse>(response);
}

export async function clearMemory(sessionId: string): Promise<void> {
  const response = await fetch(`${API_BASE}/chat/memory/${sessionId}`, {
    method: 'DELETE',
    headers: getAuthHeaders(),
  });
  await handleResponse(response);
}

export async function clearKnowledgeBase(): Promise<void> {
  const response = await fetch(`${API_BASE}/documents/clear`, {
    method: 'DELETE',
    headers: getAuthHeaders(),
  });
  await handleResponse(response);
}

export async function healthCheck(): Promise<HealthResponse> {
  const response = await fetch(`${API_BASE}/health`);
  return handleResponse<HealthResponse>(response);
}

export interface Invoice {
  id: string;
  vendor_name: string;
  invoice_number: string;
  total_amount: number;
  currency: string;
  invoice_date: string;
  due_date: string | null;
  status: 'paid' | 'unpaid';
}

export async function getUserInvoices(): Promise<Invoice[]> {
  const res = await fetch('/invoices', {
    headers: { 'Authorization': `Bearer ${localStorage.getItem('auth_token')}` }
  });
  if (!res.ok) throw new Error('Failed to fetch invoices');
  return res.json();
}