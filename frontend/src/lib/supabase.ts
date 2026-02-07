import { createClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

if (!supabaseUrl || !supabaseAnonKey) {
    console.warn('Supabase credentials not found. Auth and persistence will not work.');
}

export const supabase = createClient(
    supabaseUrl || 'https://placeholder.supabase.co',
    supabaseAnonKey || 'placeholder'
);

// Database helper functions
export async function saveValidationSession(threadId: string, description: string, userId?: string) {
    const { data, error } = await supabase
        .from('validation_sessions')
        .upsert({
            thread_id: threadId,
            idea_description: description,
            user_id: userId || null,
            status: 'interview_pending',
            tier: 'free',
            updated_at: new Date().toISOString(),
        }, { onConflict: 'thread_id' })
        .select()
        .single();

    if (error) console.error('Error saving session:', error);
    return data;
}

export async function saveInterviewAnswer(
    threadId: string,
    questionNumber: number,
    question: string,
    answer: string
) {
    const { data, error } = await supabase
        .from('interview_answers')
        .insert({
            thread_id: threadId,
            question_number: questionNumber,
            question,
            answer,
        })
        .select()
        .single();

    if (error) console.error('Error saving answer:', error);
    return data;
}

export async function updateSessionStatus(threadId: string, status: string, tier?: string) {
    const updates: Record<string, unknown> = {
        status,
        updated_at: new Date().toISOString(),
    };
    if (tier) updates.tier = tier;

    const { data, error } = await supabase
        .from('validation_sessions')
        .update(updates)
        .eq('thread_id', threadId)
        .select()
        .single();

    if (error) console.error('Error updating session:', error);
    return data;
}

export async function getReportByThreadId(threadId: string) {
    const { data, error } = await supabase
        .from('reports')
        .select('*')
        .eq('thread_id', threadId)
        .single();

    if (error && error.code !== 'PGRST116') {
        console.error('Error fetching report:', error);
    }
    return data;
}

export async function linkSessionToUser(threadId: string, userId: string) {
    const { data, error } = await supabase
        .from('validation_sessions')
        .update({ user_id: userId, updated_at: new Date().toISOString() })
        .eq('thread_id', threadId)
        .select()
        .single();

    if (error) console.error('Error linking session:', error);
    return data;
}

// Realtime subscription for report updates
export function subscribeToReportUpdates(
    threadId: string,
    callback: (payload: { report_score: number; tier: string; report_data: unknown }) => void
) {
    const channel = supabase
        .channel(`report-${threadId}`)
        .on(
            'postgres_changes',
            {
                event: 'INSERT',
                schema: 'public',
                table: 'reports',
                filter: `thread_id=eq.${threadId}`,
            },
            (payload) => {
                callback(payload.new as { report_score: number; tier: string; report_data: unknown });
            }
        )
        .subscribe();

    return () => {
        supabase.removeChannel(channel);
    };
}
