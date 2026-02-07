import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ArrowRight, Shield, Clock, Zap, Sparkles, Loader2 } from 'lucide-react';
import { Navbar } from '@/components/Navbar';
import { FloatingOrbs } from '@/components/FloatingOrbs';
import { submitIdea } from '@/lib/api';

export default function Submit() {
  const navigate = useNavigate();
  const [description, setDescription] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const charCount = description.length;
  const isValid = charCount >= 100 && charCount <= 2000;

  const handleSubmit = async () => {
    if (!isValid) return;
    setLoading(true);
    setError('');

    try {
      const response = await submitIdea(description);
      // Store interview state
      localStorage.setItem('validateai_thread', JSON.stringify({
        thread_id: response.thread_id,
        question: response.question,
        question_number: response.question_number,
        questions_remaining: response.questions_remaining,
        answers: [],
        idea: description,
      }));
      navigate(`/interview/${response.thread_id}`);
    } catch (err) {
      setError('Something went wrong. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen relative">
      <FloatingOrbs />
      <Navbar />

      <div className="pt-28 pb-20">
        <div className="container mx-auto px-6 max-w-2xl">
          {/* Progress */}
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex items-center gap-3 mb-8"
          >
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <div className="w-6 h-6 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-xs font-bold">1</div>
              <span className="font-medium text-foreground">Tell Us About Your Idea</span>
            </div>
            <div className="h-px flex-1 bg-border" />
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <div className="w-6 h-6 rounded-full bg-secondary flex items-center justify-center text-xs">2</div>
              <span>AI Interview</span>
            </div>
          </motion.div>

          {/* Main Card */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="glass rounded-2xl p-8"
          >
            <div className="flex items-center gap-2 mb-2">
              <Sparkles className="w-5 h-5 text-primary" />
              <h1 className="text-2xl font-bold">Let's Validate Your Vision</h1>
            </div>
            <p className="text-muted-foreground mb-6">
              The more detail you provide, the smarter our AI interview will be
            </p>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">Describe your startup idea</label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Example: An AI-driven platform that helps founders validate their startup ideas through automated market research, competitor analysis, and viability scoring..."
                  className="w-full h-48 rounded-lg bg-secondary/50 border border-border px-4 py-3 text-foreground placeholder:text-muted-foreground/50 focus:outline-none focus:ring-2 focus:ring-primary/50 resize-none transition-all"
                  maxLength={2000}
                />
                <div className="flex items-center justify-between mt-2">
                  <p className="text-xs text-muted-foreground">
                    Include: Problem you're solving, target audience, unique approach
                  </p>
                  <span className={`text-xs font-mono ${
                    charCount < 100 ? 'text-destructive' : charCount > 1800 ? 'text-warning' : 'text-muted-foreground'
                  }`}>
                    {charCount}/2000
                  </span>
                </div>
              </div>

              {error && (
                <div className="text-sm text-destructive bg-destructive/10 rounded-lg px-4 py-2">
                  {error}
                </div>
              )}

              <button
                onClick={handleSubmit}
                disabled={!isValid || loading}
                className="w-full flex items-center justify-center gap-2 py-3 rounded-lg bg-primary text-primary-foreground font-semibold disabled:opacity-50 disabled:cursor-not-allowed hover:bg-primary/90 transition-all group"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Preparing your personalized questions...
                  </>
                ) : (
                  <>
                    Start AI Interview
                    <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                  </>
                )}
              </button>
            </div>
          </motion.div>

          {/* Trust Elements */}
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="flex flex-col sm:flex-row items-center justify-center gap-6 mt-8"
          >
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Shield className="w-4 h-4 text-primary" />
              Your idea is encrypted and never shared
            </div>
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Clock className="w-4 h-4 text-accent" />
              Interview takes ~10 minutes
            </div>
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Zap className="w-4 h-4 text-primary" />
              Free viability report included
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  );
}
