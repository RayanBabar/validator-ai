import { useEffect, useState, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Brain, Search, BarChart3, Target, FileText, Mail, Bookmark, Loader2, CheckCircle } from 'lucide-react';
import { Navbar } from '@/components/Navbar';
import { FloatingOrbs } from '@/components/FloatingOrbs';
import { subscribeToReportUpdates, getReportByThreadId } from '@/lib/supabase';
import { getReport } from '@/lib/api';

const statusMessages = [
  { icon: Search, text: 'Analyzing market data...' },
  { icon: BarChart3, text: 'Building financial models...' },
  { icon: Target, text: 'Identifying competitors...' },
  { icon: FileText, text: 'Generating insights...' },
  { icon: Brain, text: 'Running AI deep analysis...' },
  { icon: Search, text: 'Scanning regulatory landscape...' },
  { icon: BarChart3, text: 'Calculating projections...' },
  { icon: Target, text: 'Crafting recommendations...' },
];

const USE_MOCK = import.meta.env.VITE_USE_MOCK_API === 'true';

export default function Processing() {
  const { threadId } = useParams<{ threadId: string }>();
  const navigate = useNavigate();
  const [currentStatus, setCurrentStatus] = useState(0);
  const [email, setEmail] = useState('');
  const [emailSubmitted, setEmailSubmitted] = useState(false);
  const [reportReady, setReportReady] = useState(false);

  const tier = localStorage.getItem('validateai_upgrade_tier') || 'standard';

  const handleReportReady = useCallback((reportTier: string) => {
    setReportReady(true);
    setTimeout(() => {
      navigate(`/report/${threadId}?tier=${reportTier}`);
    }, 2000);
  }, [navigate, threadId]);

  useEffect(() => {
    // Cycle through status messages
    const interval = setInterval(() => {
      setCurrentStatus((prev) => (prev + 1) % statusMessages.length);
    }, 3000);

    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (!threadId) return;

    if (USE_MOCK) {
      // Mock mode: auto-redirect after 15 seconds
      const timeout = setTimeout(() => {
        handleReportReady(tier);
      }, 15000);
      return () => clearTimeout(timeout);
    }

    // Real mode: Subscribe to Supabase realtime updates
    const unsubscribe = subscribeToReportUpdates(threadId, (payload) => {
      console.log('Report ready via realtime:', payload);
      handleReportReady(payload.tier);
    });

    // Also poll every 10 seconds as a fallback
    const pollInterval = setInterval(async () => {
      try {
        // Check Supabase directly
        const supabaseReport = await getReportByThreadId(threadId);
        if (supabaseReport) {
          handleReportReady(supabaseReport.tier);
          clearInterval(pollInterval);
          return;
        }

        // Also check backend API
        const report = await getReport(threadId, tier);
        if (report && report.report_data) {
          handleReportReady(tier);
          clearInterval(pollInterval);
        }
      } catch (err) {
        // Report not ready yet, continue polling
        console.log('Report not ready yet, continuing to poll...');
      }
    }, 10000);

    return () => {
      unsubscribe();
      clearInterval(pollInterval);
    };
  }, [threadId, tier, handleReportReady]);

  const StatusIcon = statusMessages[currentStatus].icon;

  return (
    <div className="min-h-screen relative">
      <FloatingOrbs />
      <Navbar />

      <div className="pt-28 pb-20">
        <div className="container mx-auto px-6 max-w-lg">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center"
          >
            {/* Animated Brain */}
            <div className="relative w-32 h-32 mx-auto mb-8">
              <motion.div
                className="absolute inset-0 rounded-full"
                style={{ background: 'var(--gradient-glow)' }}
                animate={{ scale: [1, 1.2, 1], opacity: [0.5, 0.8, 0.5] }}
                transition={{ duration: 3, repeat: Infinity }}
              />
              <div className="absolute inset-0 flex items-center justify-center">
                <motion.div
                  animate={{ rotate: 360 }}
                  transition={{ duration: 8, repeat: Infinity, ease: 'linear' }}
                  className="w-20 h-20 rounded-full border-2 border-dashed border-primary/30"
                />
              </div>
              <div className="absolute inset-0 flex items-center justify-center">
                {reportReady ? (
                  <CheckCircle className="w-10 h-10 text-primary" />
                ) : (
                  <Brain className="w-10 h-10 text-primary" />
                )}
              </div>
            </div>

            <h1 className="text-2xl font-bold mb-3">
              {reportReady ? 'Your Report is Ready!' : 'Generating Your Premium Report'}
            </h1>

            {/* Animated Status */}
            {!reportReady && (
              <div className="h-8 mb-6">
                <AnimatePresence mode="wait">
                  <motion.div
                    key={currentStatus}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    className="flex items-center justify-center gap-2 text-muted-foreground"
                  >
                    <StatusIcon className="w-4 h-4 text-primary" />
                    <span className="text-sm">{statusMessages[currentStatus].text}</span>
                  </motion.div>
                </AnimatePresence>
              </div>
            )}

            {reportReady ? (
              <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                className="glass rounded-xl p-6 mb-6"
              >
                <div className="flex items-center justify-center gap-2 text-primary">
                  <CheckCircle className="w-5 h-5" />
                  <span className="font-medium">Redirecting to your report...</span>
                </div>
              </motion.div>
            ) : (
              <>
                {/* Progress */}
                <div className="glass rounded-xl p-6 mb-6">
                  <div className="flex items-center justify-center gap-2 mb-3">
                    <Loader2 className="w-4 h-4 animate-spin text-primary" />
                    <span className="text-sm font-medium">Processing...</span>
                  </div>
                  <div className="h-2 rounded-full bg-secondary overflow-hidden mb-3">
                    <motion.div
                      className="h-full rounded-full"
                      style={{ background: 'var(--gradient-accent)' }}
                      animate={{ width: ['0%', '30%', '50%', '65%', '80%', '90%'] }}
                      transition={{ duration: 60, ease: 'easeOut' }}
                    />
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Your <span className="capitalize">{tier}</span> report will be ready in ~5-10 minutes
                  </p>
                </div>

                {/* Email notification */}
                {!emailSubmitted ? (
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.3 }}
                    className="glass rounded-xl p-6 mb-6"
                  >
                    <div className="flex items-center justify-center gap-2 mb-3">
                      <Mail className="w-4 h-4 text-accent" />
                      <span className="text-sm font-medium">Get notified when ready</span>
                    </div>
                    <div className="flex gap-2">
                      <input
                        type="email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        placeholder="your@email.com"
                        className="flex-1 rounded-lg bg-secondary/50 border border-border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
                      />
                      <button
                        onClick={() => setEmailSubmitted(true)}
                        className="px-4 py-2 rounded-lg bg-primary text-primary-foreground text-sm font-semibold hover:bg-primary/90 transition-all"
                      >
                        Notify Me
                      </button>
                    </div>
                  </motion.div>
                ) : (
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="glass rounded-xl p-4 mb-6 text-sm text-primary"
                  >
                    ✓ We'll notify you at {email} when your report is ready!
                  </motion.div>
                )}

                {/* While you wait */}
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.5 }}
                  className="glass rounded-xl p-6"
                >
                  <h3 className="text-sm font-medium mb-3">While you wait...</h3>
                  <ul className="space-y-3 text-left">
                    <li className="flex items-start gap-3 text-sm text-muted-foreground">
                      <Bookmark className="w-4 h-4 text-primary mt-0.5 shrink-0" />
                      <span>Bookmark this page to come back anytime</span>
                    </li>
                    <li className="flex items-start gap-3 text-sm text-muted-foreground">
                      <FileText className="w-4 h-4 text-accent mt-0.5 shrink-0" />
                      <span>Prepare your pitch deck outline based on the free report insights</span>
                    </li>
                    <li className="flex items-start gap-3 text-sm text-muted-foreground">
                      <Target className="w-4 h-4 text-primary mt-0.5 shrink-0" />
                      <span>Start listing potential early adopters in your target market</span>
                    </li>
                  </ul>
                </motion.div>
              </>
            )}
          </motion.div>
        </div>
      </div>
    </div>
  );
}
