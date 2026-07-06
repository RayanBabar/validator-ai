import { saveValidationSession, saveInterviewAnswer, updateSessionStatus, getReportByThreadId, supabase } from '@/lib/supabase';

// API configuration - change this to point to your backend
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

// Use mock data when backend is unavailable (set via env var)
const USE_MOCK = import.meta.env.VITE_USE_MOCK_API === 'true';

const getHeaders = async () => {
  const { data: { session } } = await supabase.auth.getSession();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  };
  if (session?.access_token) {
    headers['Authorization'] = `Bearer ${session.access_token}`;
    headers['X-User-Id'] = session.user.id;
  }
  return headers;
};

const mockQuestions = [
  "Let's start with the core problem you're solving. Can you tell me about a specific moment when you or someone you know experienced this friction? What was the actual cost or consequence?",
  "Who are your ideal first 10 customers? Be specific about their role, company size, and the exact pain point they'd pay to solve.",
  "How are these potential customers currently solving this problem? What's their existing workflow and what are they spending?",
  "What's your unique insight or unfair advantage that competitors can't easily replicate?",
  "Walk me through your revenue model. How will you charge, and what's the customer's willingness to pay?",
  "What's your go-to-market strategy for the first 6 months? How will you find and convert your first customers?",
  "Tell me about the team. Who are the founders, what's their relevant experience, and what key hires are needed?"
];

const INTERVIEW_QUESTION_COUNT = 5;

export interface SubmitResponse {
  thread_id: string;
  status: string;
  question: string;
  question_number: number;
  questions_remaining: number;
}

export interface AnswerResponse {
  thread_id: string;
  status: 'question_pending' | 'free_report_ready';
  question?: string;
  question_number?: number;
  questions_remaining?: number;
  message?: string;
  report_endpoint?: string;
}

export interface UpgradeResponse {
  thread_id: string;
  status: string;
  tier: string;
  message: string;
}

export async function submitIdea(description: string): Promise<SubmitResponse> {
  if (USE_MOCK) {
    await new Promise(r => setTimeout(r, 1500));
    const threadId = crypto.randomUUID();
    // Save to Supabase (non-blocking)
    saveValidationSession(threadId, description).catch(console.error);
    return {
      thread_id: threadId,
      status: 'question_pending',
      question: mockQuestions[0],
      question_number: 1,
      questions_remaining: INTERVIEW_QUESTION_COUNT - 1,
    };
  }

  const res = await fetch(`${API_BASE_URL}/submit`, {
    method: 'POST',
    headers: await getHeaders(),
    body: JSON.stringify({ detailed_description: description }),
  });
  if (!res.ok) throw new Error('Failed to submit idea');
  const data = await res.json();
  
  // Save to Supabase with user association
  const { data: { session } } = await supabase.auth.getSession();
  saveValidationSession(data.thread_id, description, session?.user?.id).catch(console.error);
  
  return data;
}

export async function submitAnswer(threadId: string, answer: string, currentQuestion: number): Promise<AnswerResponse> {
  if (USE_MOCK) {
    await new Promise(r => setTimeout(r, 2000));
    const nextQ = currentQuestion + 1;
    // Save answer to Supabase
    saveInterviewAnswer(threadId, currentQuestion, mockQuestions[currentQuestion - 1], answer).catch(console.error);

    if (nextQ > INTERVIEW_QUESTION_COUNT) {
      updateSessionStatus(threadId, 'free_report_ready').catch(console.error);
      return {
        thread_id: threadId,
        status: 'free_report_ready',
        message: 'Your free viability report is ready!',
        report_endpoint: `/report/${threadId}`,
      };
    }
    return {
      thread_id: threadId,
      status: 'question_pending',
      question: mockQuestions[nextQ - 1] || mockQuestions[0],
      question_number: nextQ,
      questions_remaining: INTERVIEW_QUESTION_COUNT - nextQ,
    };
  }

  const res = await fetch(`${API_BASE_URL}/answer/${threadId}`, {
    method: 'POST',
    headers: await getHeaders(),
    body: JSON.stringify({ answer }),
  });
  if (!res.ok) throw new Error('Failed to submit answer');
  const data = await res.json();
  // Save answer to Supabase
  saveInterviewAnswer(threadId, currentQuestion, 'Question from API', answer).catch(console.error);
  if (data.status === 'free_report_ready') {
    updateSessionStatus(threadId, 'free_report_ready').catch(console.error);
  }
  return data;
}

export async function submitAnswerStream(
  threadId: string,
  answer: string,
  onToken: (token: string) => void,
  onComplete: (data: AnswerResponse) => void,
  onError: (err: any) => void
): Promise<void> {
  if (USE_MOCK) {
    // Mock streaming: delay and then return mock next question letter-by-letter
    await new Promise(r => setTimeout(r, 1000));
    const fullText = "Who are your ideal first 10 customers? Be specific about their role.";
    let currentIdx = 0;
    const interval = setInterval(() => {
      if (currentIdx < fullText.length) {
        onToken(fullText.slice(currentIdx, currentIdx + 4));
        currentIdx += 4;
      } else {
        clearInterval(interval);
        onComplete({
          thread_id: threadId,
          status: 'question_pending',
          question: fullText,
          question_number: 2,
          questions_remaining: 3,
        });
      }
    }, 60);
    return;
  }

  try {
    const headers = await getHeaders();
    const res = await fetch(`${API_BASE_URL}/answer/${threadId}/stream`, {
      method: 'POST',
      headers,
      body: JSON.stringify({ answer }),
    });

    if (!res.ok) throw new Error('Failed to submit answer stream');

    const reader = res.body?.getReader();
    if (!reader) throw new Error('No readable stream body');

    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || ''; // Keep partial line in buffer

      for (const line of lines) {
        const cleaned = line.trim();
        if (!cleaned.startsWith('data: ')) continue;
        
        try {
          const payload = JSON.parse(cleaned.slice(6));
          if (payload.token) {
            onToken(payload.token);
          } else if (payload.done) {
            onComplete({
              thread_id: threadId,
              status: payload.status === 'interview_complete' ? 'free_report_ready' : 'question_pending',
              question: payload.question || undefined,
              question_number: payload.question_number || undefined,
              questions_remaining: payload.questions_remaining || undefined,
              message: payload.status === 'interview_complete' ? 'Your free viability report is ready!' : undefined,
              report_endpoint: payload.status === 'interview_complete' ? `/report/${threadId}` : undefined,
            });
          }
        } catch (e) {
          console.error('Error parsing SSE event:', e);
        }
      }
    }
  } catch (err) {
    onError(err);
  }
}


export async function getReport(threadId: string, tier: string = 'free') {
  if (USE_MOCK) {
    await new Promise(r => setTimeout(r, 800));
    return {
      thread_id: threadId,
      tier: tier,
      report_data: { 
        title: "Mock Report (Backend Needed)", 
        go_no_go_score: 50,
        executive_summary: { problem_summary: "Enable backend to see real analysis." }
      },
      available_tiers: ['free', 'basic']
    };
  }

  const res = await fetch(`${API_BASE_URL}/report/${threadId}?tier=${tier}`, {
    headers: await getHeaders(),
  });
  if (!res.ok) throw new Error('Failed to fetch report');
  return res.json();
}

export async function upgradeReport(threadId: string, tier: string, customModules?: string[]): Promise<UpgradeResponse> {
  // Update session in Supabase
  updateSessionStatus(threadId, 'upgrade_initiated', tier).catch(console.error);

  if (USE_MOCK) {
    await new Promise(r => setTimeout(r, 2000));
    return {
      thread_id: threadId,
      status: 'upgrade_initiated',
      tier,
      message: `Deep analysis started for ${tier} tier.`,
    };
  }

  const body: Record<string, unknown> = { tier };
  if (customModules) body.custom_modules = customModules;

  const res = await fetch(`${API_BASE_URL}/upgrade/${threadId}`, {
    method: 'POST',
    headers: await getHeaders(),
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error('Failed to upgrade');
  return res.json();
}

export async function upgradeProfile(tier: string): Promise<{ status: string; tier: string }> {
  const res = await fetch(`${API_BASE_URL}/profile/upgrade`, {
    method: 'POST',
    headers: await getHeaders(),
    body: JSON.stringify({ tier }),
  });
  if (!res.ok) throw new Error('Failed to upgrade profile');
  return res.json();
}

export function getScoreColor(score: number, max: number = 100): string {
  const pct = (score / max) * 100;
  if (pct <= 40) return 'destructive';
  if (pct <= 60) return 'warning';
  if (pct <= 80) return 'primary';
  return 'info';
}

export function getScoreColorClass(score: number, max: number = 100): string {
  const pct = (score / max) * 100;
  if (pct <= 40) return 'score-red';
  if (pct <= 60) return 'score-yellow';
  if (pct <= 80) return 'score-green';
  return 'score-blue';
}

export function getScoreBgClass(score: number, max: number = 100): string {
  const pct = (score / max) * 100;
  if (pct <= 40) return 'bg-score-red';
  if (pct <= 60) return 'bg-score-yellow';
  if (pct <= 80) return 'bg-score-green';
  return 'bg-score-blue';
}

export async function adminApprove(threadId: string, editedReport?: any): Promise<{ status: string; message: string }> {
  const res = await fetch(`${API_BASE_URL}/admin/approve/${threadId}`, {
    method: 'POST',
    headers: await getHeaders(),
    body: JSON.stringify({ edited_report: editedReport }),
  });
  if (!res.ok) throw new Error('Failed to approve report');
  return res.json();
}

export async function adminSave(threadId: string, editedReport: any): Promise<{ status: string; message: string }> {
  const res = await fetch(`${API_BASE_URL}/admin/save/${threadId}`, {
    method: 'POST',
    headers: await getHeaders(),
    body: JSON.stringify({ edited_report: editedReport }),
  });
  if (!res.ok) throw new Error('Failed to save report edits');
  return res.json();
}
