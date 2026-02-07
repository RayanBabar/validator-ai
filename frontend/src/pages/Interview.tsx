import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Bot, Send, Loader2, Clock, ChevronDown, ChevronUp, Sparkles } from 'lucide-react';
import { Navbar } from '@/components/Navbar';
import { FloatingOrbs } from '@/components/FloatingOrbs';
import { submitAnswer } from '@/lib/api';

interface InterviewState {
  thread_id: string;
  question: string;
  question_number: number;
  questions_remaining: number;
  answers: Array<{ question: string; answer: string }>;
  idea: string;
}

export default function Interview() {
  const { threadId } = useParams<{ threadId: string }>();
  const navigate = useNavigate();
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const [state, setState] = useState<InterviewState | null>(null);
  const [answer, setAnswer] = useState('');
  const [loading, setLoading] = useState(false);
  const [showHistory, setShowHistory] = useState(false);
  const [displayedQuestion, setDisplayedQuestion] = useState('');
  const [isTyping, setIsTyping] = useState(false);

  useEffect(() => {
    const stored = localStorage.getItem('validateai_thread');
    if (stored) {
      const parsed = JSON.parse(stored);
      if (parsed.thread_id === threadId) {
        setState(parsed);
        typewriterEffect(parsed.question);
        return;
      }
    }
    navigate('/submit');
  }, [threadId, navigate]);

  const typewriterEffect = (text: string) => {
    setIsTyping(true);
    setDisplayedQuestion('');
    let i = 0;
    const interval = setInterval(() => {
      if (i < text.length) {
        setDisplayedQuestion(text.slice(0, i + 1));
        i++;
      } else {
        clearInterval(interval);
        setIsTyping(false);
      }
    }, 20);
    return () => clearInterval(interval);
  };

  const handleSubmit = async () => {
    if (!state || answer.trim().length < 10 || loading) return;
    setLoading(true);

    try {
      const response = await submitAnswer(state.thread_id, answer, state.question_number);
      const newAnswers = [...state.answers, { question: state.question, answer }];

      if (response.status === 'free_report_ready') {
        localStorage.setItem('validateai_thread', JSON.stringify({
          ...state,
          answers: newAnswers,
          completed: true,
        }));
        navigate(`/report/${state.thread_id}?tier=free`);
        return;
      }

      const newState: InterviewState = {
        ...state,
        question: response.question || '',
        question_number: response.question_number || state.question_number + 1,
        questions_remaining: response.questions_remaining || 0,
        answers: newAnswers,
      };

      setState(newState);
      localStorage.setItem('validateai_thread', JSON.stringify(newState));
      setAnswer('');
      typewriterEffect(response.question || '');
      textareaRef.current?.focus();
    } catch (err) {
      console.error('Failed to submit answer:', err);
    } finally {
      setLoading(false);
    }
  };

  if (!state) return null;

  const progress = (state.question_number / 10) * 100;
  const estimatedMinutes = state.questions_remaining * 1;

  return (
    <div className="min-h-screen relative">
      <FloatingOrbs />
      <Navbar />

      <div className="pt-28 pb-20">
        <div className="container mx-auto px-6 max-w-3xl">
          {/* Progress */}
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-8"
          >
            <div className="flex items-center justify-between text-sm mb-3">
              <span className="font-medium">Question {state.question_number} of 10</span>
              <div className="flex items-center gap-1.5 text-muted-foreground">
                <Clock className="w-3.5 h-3.5" />
                ~{estimatedMinutes} min remaining
              </div>
            </div>
            <div className="h-2 rounded-full bg-secondary overflow-hidden">
              <motion.div
                className="h-full rounded-full"
                style={{ background: 'var(--gradient-accent)' }}
                initial={{ width: 0 }}
                animate={{ width: `${progress}%` }}
                transition={{ duration: 0.5 }}
              />
            </div>
          </motion.div>

          {/* Question Card */}
          <AnimatePresence mode="wait">
            <motion.div
              key={state.question_number}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="glass rounded-2xl p-8 mb-6"
            >
              <div className="flex items-start gap-4">
                <div className="w-10 h-10 rounded-xl bg-primary/20 flex items-center justify-center shrink-0">
                  <Bot className="w-5 h-5 text-primary" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-3">
                    <span className="text-xs font-mono text-muted-foreground bg-secondary/50 px-2 py-0.5 rounded">
                      Q{state.question_number}
                    </span>
                    <Sparkles className="w-3 h-3 text-primary" />
                  </div>
                  <p className="text-lg leading-relaxed">
                    {displayedQuestion}
                    {isTyping && <span className="animate-pulse text-primary">|</span>}
                  </p>
                </div>
              </div>
            </motion.div>
          </AnimatePresence>

          {/* Answer Input */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="glass rounded-2xl p-6"
          >
            <textarea
              ref={textareaRef}
              value={answer}
              onChange={(e) => setAnswer(e.target.value)}
              placeholder="Share your thoughts..."
              className="w-full h-32 rounded-lg bg-secondary/30 border border-border px-4 py-3 text-foreground placeholder:text-muted-foreground/50 focus:outline-none focus:ring-2 focus:ring-primary/50 resize-none transition-all"
              disabled={loading}
            />
            <div className="flex items-center justify-between mt-3">
              <p className="text-xs text-muted-foreground">
                Great answers are 50-500 characters ({answer.length})
              </p>
              <button
                onClick={handleSubmit}
                disabled={answer.trim().length < 10 || loading}
                className="flex items-center gap-2 px-5 py-2.5 rounded-lg bg-primary text-primary-foreground font-semibold text-sm disabled:opacity-50 disabled:cursor-not-allowed hover:bg-primary/90 transition-all"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    AI is processing...
                  </>
                ) : (
                  <>
                    Submit & Continue
                    <Send className="w-4 h-4" />
                  </>
                )}
              </button>
            </div>
          </motion.div>

          {/* History */}
          {state.answers.length > 0 && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="mt-6"
            >
              <button
                onClick={() => setShowHistory(!showHistory)}
                className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors"
              >
                {showHistory ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                Review previous answers ({state.answers.length})
              </button>

              <AnimatePresence>
                {showHistory && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    className="overflow-hidden"
                  >
                    <div className="space-y-4 mt-4">
                      {state.answers.map((qa, i) => (
                        <div key={i} className="glass rounded-lg p-4">
                          <p className="text-xs font-mono text-muted-foreground mb-1">Q{i + 1}</p>
                          <p className="text-sm font-medium mb-2">{qa.question}</p>
                          <p className="text-sm text-muted-foreground">{qa.answer}</p>
                        </div>
                      ))}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          )}
        </div>
      </div>
    </div>
  );
}
