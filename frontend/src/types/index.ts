export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

export interface ChatRequest {
  question: string;
  session_id: string;
  k?: number;
}

export interface SourceDocument {
  content: string;
  metadata: {
    source?: string;
    filename?: string;
    page?: number;
    [key: string]: any;
  };
}

export interface ChatResponse {
  answer: string;
  sources: SourceDocument[];
  session_id: string;
}

export interface AsyncChatInitResponse {
  status: 'processing';
  request_id: string;
  message: string;
}

export interface ChatStatusResponse {
  status: 'processing' | 'completed' | 'error';
  message?: string;
  answer?: string;
  sources?: SourceDocument[];
  session_id?: string;
}

export interface DocumentResponse {
  status: string;
  documents_added: number;
  chunks_created: number;
  message: string;
}

export interface HealthResponse {
  status: string;
  version: string;
  services: {
    llm: string;
    embeddings: string;
    vectorstore: string;
    memory: string;
    ocr: string;
  };
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