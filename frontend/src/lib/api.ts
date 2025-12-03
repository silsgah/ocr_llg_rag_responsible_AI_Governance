import type {
  ChatRequest,
  ChatResponse,
  DocumentResponse,
  HealthResponse,
} from '@/types';

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080';

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

export async function uploadDocument(
  file: File,
  useOCR: boolean = false
): Promise<DocumentResponse> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(
    `${API_BASE}/documents/upload?use_ocr=${useOCR}`,
    {
      method: 'POST',
      headers: getAuthHeaders(),
      body: formData,
    }
  );

  return handleResponse<DocumentResponse>(response);
}

export async function sendChatMessage(
  request: ChatRequest
): Promise<ChatResponse> {
  const response = await fetch(`${API_BASE}/chat/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...getAuthHeaders(),
    },
    body: JSON.stringify(request),
  });

  return handleResponse<ChatResponse>(response);
}

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
