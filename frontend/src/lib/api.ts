import freeReportData from '@/data/free_report.json';
import basicReportData from '@/data/basic_report.json';
import standardReportData from '@/data/standard_report.json';
import premiumReportData from '@/data/premium_report.json';
import { saveValidationSession, saveInterviewAnswer, updateSessionStatus, getReportByThreadId } from '@/lib/supabase';

// API configuration - change this to point to your backend
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

// Use mock data when backend is unavailable (set via env var)
const USE_MOCK = import.meta.env.VITE_USE_MOCK_API === 'true';

const mockQuestions = [
  "Let's start with the core problem you're solving. Can you tell me about a specific moment when you or someone you know experienced this friction? What was the actual cost or consequence?",
  "Who are your ideal first 10 customers? Be specific about their role, company size, and the exact pain point they'd pay to solve.",
  "How are these potential customers currently solving this problem? What's their existing workflow and what are they spending?",
  "What's your unique insight or unfair advantage that competitors can't easily replicate?",
  "Walk me through your revenue model. How will you charge, and what's the customer's willingness to pay?",
  "What's your go-to-market strategy for the first 6 months? How will you find and convert your first customers?",
  "Tell me about the team. Who are the founders, what's their relevant experience, and what key hires are needed?",
  "What's your technical approach? How long to build an MVP, and what are the biggest technical risks?",
  "What regulatory, legal, or compliance challenges do you anticipate?",
  "If this idea fails, what would be the most likely reason? What's your biggest fear about this venture?"
];

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
      questions_remaining: 9,
    };
  }

  const res = await fetch(`${API_BASE_URL}/submit`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
    body: JSON.stringify({ detailed_description: description }),
  });
  if (!res.ok) throw new Error('Failed to submit idea');
  const data = await res.json();
  // Save to Supabase
  saveValidationSession(data.thread_id, description).catch(console.error);
  return data;
}

export async function submitAnswer(threadId: string, answer: string, currentQuestion: number): Promise<AnswerResponse> {
  if (USE_MOCK) {
    await new Promise(r => setTimeout(r, 2000));
    const nextQ = currentQuestion + 1;
    // Save answer to Supabase
    saveInterviewAnswer(threadId, currentQuestion, mockQuestions[currentQuestion - 1], answer).catch(console.error);

    if (nextQ > 10) {
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
      questions_remaining: 10 - nextQ,
    };
  }

  const res = await fetch(`${API_BASE_URL}/answer/${threadId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
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

export async function getReport(threadId: string, tier: string = 'free') {
  // First check Supabase for persisted report (from webhook)
  const supabaseReport = await getReportByThreadId(threadId);
  if (supabaseReport && supabaseReport.report_data) {
    return {
      thread_id: threadId,
      tier: supabaseReport.tier,
      report_data: supabaseReport.report_data,
    };
  }

  if (USE_MOCK) {
    await new Promise(r => setTimeout(r, 800));
    if (tier === 'premium') return premiumReportData;
    if (tier === 'standard') return standardReportData;
    if (tier === 'basic') return basicReportData;
    return freeReportData;
  }

  // Pass tier as query param to backend so it knows which report to return
  const res = await fetch(`${API_BASE_URL}/report/${threadId}?tier=${tier}`, {
    headers: { 'Accept': 'application/json' },
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
    headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error('Failed to upgrade');
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
