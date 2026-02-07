import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Check, Star, ArrowRight, CreditCard, X, Loader2, Shield, Clock } from 'lucide-react';
import { Navbar } from '@/components/Navbar';
import { FloatingOrbs } from '@/components/FloatingOrbs';
import { Footer } from '@/components/Footer';
import { upgradeReport } from '@/lib/api';

const tiers = [
  {
    id: 'basic',
    name: 'Basic',
    price: 49,
    features: [
      'Everything in Free',
      'Business Model Canvas',
      'Executive Summary with Go/No-Go Score',
      '8 Score Dimensions',
    ],
    bestFor: 'Validating core business model',
    modules: ['mod_bmc'],
  },
  {
    id: 'standard',
    name: 'Standard',
    price: 149,
    features: [
      'Everything in Basic',
      'Full Market Analysis',
      'Competitive Intelligence',
      'Financial Projections',
      'Technical Feasibility',
      'Go-to-Market Strategy',
      'Risk Analysis',
      '90-Day Roadmap',
      'Funding Strategy',
    ],
    bestFor: 'Preparing for investor conversations',
    modules: ['mod_bmc', 'mod_market', 'mod_comp', 'mod_finance', 'mod_tech', 'mod_reg', 'mod_gtm', 'mod_risk', 'mod_roadmap', 'mod_funding'],
    recommended: true,
  },
  {
    id: 'premium',
    name: 'Premium',
    price: 299,
    features: [
      'Everything in Standard',
      'Investor Pitch Deck (PDF)',
      'Custom Module Selection',
      'Priority Processing',
    ],
    bestFor: 'Fundraising-ready founders',
    modules: ['mod_bmc', 'mod_market', 'mod_comp', 'mod_finance', 'mod_tech', 'mod_reg', 'mod_gtm', 'mod_risk', 'mod_roadmap', 'mod_funding', 'investor_pitch_deck'],
  },
];

function DemoPaymentModal({
  tier,
  price,
  onClose,
  onSuccess,
}: {
  tier: string;
  price: number;
  onClose: () => void;
  onSuccess: () => void;
}) {
  const [processing, setProcessing] = useState(false);
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setProcessing(true);
    await new Promise((r) => setTimeout(r, 2000));
    setProcessing(false);
    setSuccess(true);
    await new Promise((r) => setTimeout(r, 1500));
    onSuccess();
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-background/80 backdrop-blur-sm"
    >
      <motion.div
        initial={{ scale: 0.95, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.95, opacity: 0 }}
        className="glass-strong rounded-2xl p-8 max-w-md w-full relative"
      >
        <button onClick={onClose} className="absolute top-4 right-4 text-muted-foreground hover:text-foreground transition-colors">
          <X className="w-5 h-5" />
        </button>

        <div className="absolute top-4 left-4 px-2 py-0.5 rounded text-[10px] font-mono text-muted-foreground bg-secondary/50">
          DEMO MODE
        </div>

        {success ? (
          <div className="text-center py-8">
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ type: 'spring', stiffness: 200 }}
              className="w-16 h-16 rounded-full bg-primary/20 flex items-center justify-center mx-auto mb-4"
            >
              <Check className="w-8 h-8 text-primary" />
            </motion.div>
            <h3 className="text-xl font-bold mb-1">Payment Successful!</h3>
            <p className="text-sm text-muted-foreground">Redirecting to your report...</p>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="mt-6">
            <div className="flex items-center gap-2 mb-6">
              <CreditCard className="w-5 h-5 text-primary" />
              <h3 className="text-lg font-bold">Complete Your Purchase</h3>
            </div>

            <div className="flex items-center justify-between mb-6 glass rounded-lg p-3">
              <span className="text-sm text-muted-foreground">Plan: {tier} Tier</span>
              <span className="font-bold">${price}.00</span>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-xs font-medium mb-1.5 text-muted-foreground">Card Number</label>
                <input
                  type="text"
                  defaultValue="4242 4242 4242 4242"
                  className="w-full rounded-lg bg-secondary/50 border border-border px-3 py-2.5 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-primary/50"
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium mb-1.5 text-muted-foreground">Expiry</label>
                  <input
                    type="text"
                    defaultValue="12/28"
                    className="w-full rounded-lg bg-secondary/50 border border-border px-3 py-2.5 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-primary/50"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium mb-1.5 text-muted-foreground">CVC</label>
                  <input
                    type="text"
                    defaultValue="123"
                    className="w-full rounded-lg bg-secondary/50 border border-border px-3 py-2.5 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-primary/50"
                  />
                </div>
              </div>

              <p className="text-xs text-muted-foreground text-center">
                ⓘ Demo Mode: Use any values — no real payment will be processed.
              </p>

              <button
                type="submit"
                disabled={processing}
                className="w-full flex items-center justify-center gap-2 py-3 rounded-lg bg-primary text-primary-foreground font-semibold disabled:opacity-70 hover:bg-primary/90 transition-all"
              >
                {processing ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Processing...
                  </>
                ) : (
                  <>
                    Complete Payment
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </button>

              <div className="flex items-center justify-center gap-1.5 text-xs text-muted-foreground">
                <Shield className="w-3 h-3" />
                Secure demo checkout
              </div>
            </div>
          </form>
        )}
      </motion.div>
    </motion.div>
  );
}

export default function Upgrade() {
  const { threadId } = useParams<{ threadId: string }>();
  const navigate = useNavigate();
  const [selectedTier, setSelectedTier] = useState<typeof tiers[0] | null>(null);

  const handleUpgrade = async (tier: typeof tiers[0]) => {
    setSelectedTier(tier);
  };

  const handlePaymentSuccess = async () => {
    if (!selectedTier || !threadId) return;
    try {
      await upgradeReport(threadId, selectedTier.id, selectedTier.modules);
      localStorage.setItem('validateai_upgrade_tier', selectedTier.id);
      navigate(`/processing/${threadId}`);
    } catch {
      console.error('Upgrade failed');
    }
  };

  return (
    <div className="min-h-screen relative">
      <FloatingOrbs />
      <Navbar />

      <div className="pt-28 pb-10">
        <div className="container mx-auto px-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center mb-12"
          >
            <h1 className="text-3xl md:text-4xl font-bold mb-3">
              Unlock Your Full <span className="gradient-text">Validation Report</span>
            </h1>
            <p className="text-muted-foreground max-w-md mx-auto">
              Choose the plan that fits your stage. All plans include instant AI-powered analysis.
            </p>
          </motion.div>

          <div className="grid md:grid-cols-3 gap-6 max-w-5xl mx-auto">
            {tiers.map((tier, i) => (
              <motion.div
                key={tier.id}
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.1 }}
                className={`relative glass rounded-2xl p-6 transition-all hover:scale-[1.02] ${
                  tier.recommended ? 'ring-2 ring-primary glow-primary' : ''
                }`}
              >
                {tier.recommended && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2 flex items-center gap-1 px-3 py-1 rounded-full bg-primary text-primary-foreground text-xs font-semibold">
                    <Star className="w-3 h-3" />
                    Recommended
                  </div>
                )}

                <h3 className="text-xl font-bold mb-1">{tier.name}</h3>
                <div className="flex items-baseline gap-1 mb-1">
                  <span className="text-4xl font-extrabold">${tier.price}</span>
                  <span className="text-sm text-muted-foreground">one-time</span>
                </div>
                <p className="text-xs text-muted-foreground mb-5">{tier.bestFor}</p>

                <ul className="space-y-2.5 mb-6">
                  {tier.features.map((f) => (
                    <li key={f} className="flex items-start gap-2 text-sm">
                      <Check className="w-4 h-4 text-primary mt-0.5 shrink-0" />
                      <span className="text-muted-foreground">{f}</span>
                    </li>
                  ))}
                </ul>

                <button
                  onClick={() => handleUpgrade(tier)}
                  className={`w-full flex items-center justify-center gap-2 py-3 rounded-lg text-sm font-semibold transition-all group ${
                    tier.recommended
                      ? 'bg-primary text-primary-foreground hover:bg-primary/90'
                      : 'glass hover:bg-secondary/50'
                  }`}
                >
                  Get {tier.name} Report
                  <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                </button>
              </motion.div>
            ))}
          </div>

          {/* Trust Elements */}
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="flex flex-col sm:flex-row items-center justify-center gap-6 mt-10"
          >
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Shield className="w-4 h-4 text-primary" />
              Money-back guarantee
            </div>
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <CreditCard className="w-4 h-4 text-accent" />
              Secure payment
            </div>
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Clock className="w-4 h-4 text-primary" />
              Report in 5-10 minutes
            </div>
          </motion.div>
        </div>
      </div>

      <Footer />

      <AnimatePresence>
        {selectedTier && (
          <DemoPaymentModal
            tier={selectedTier.name}
            price={selectedTier.price}
            onClose={() => setSelectedTier(null)}
            onSuccess={handlePaymentSuccess}
          />
        )}
      </AnimatePresence>
    </div>
  );
}
