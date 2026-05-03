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
    name: 'Basic Research',
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
    name: 'Standard Analysis',
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
    bestFor: 'In-depth academic validation',
    modules: ['mod_bmc', 'mod_market', 'mod_comp', 'mod_finance', 'mod_tech', 'mod_reg', 'mod_gtm', 'mod_risk', 'mod_roadmap', 'mod_funding'],
    recommended: true,
  },
  {
    id: 'premium',
    name: 'Premium Validation',
    features: [
      'Everything in Standard',
      'Investor Pitch Deck (PDF)',
      'Custom Module Selection',
      'Priority Research Processing',
    ],
    bestFor: 'Final project submission standard',
    modules: ['mod_bmc', 'mod_market', 'mod_comp', 'mod_finance', 'mod_tech', 'mod_reg', 'mod_gtm', 'mod_risk', 'mod_roadmap', 'mod_funding', 'investor_pitch_deck'],
  },
];

export default function Upgrade() {
  const { threadId } = useParams<{ threadId: string }>();
  const navigate = useNavigate();
  const [upgrading, setUpgrading] = useState(false);

  const handleUpgrade = async (tier: typeof tiers[0]) => {
    if (!threadId) return;
    setUpgrading(true);
    try {
      await upgradeReport(threadId, tier.id, tier.modules);
      localStorage.setItem('validateai_upgrade_tier', tier.id);
      navigate(`/processing/${threadId}`);
    } catch {
      console.error('Upgrade failed');
    } finally {
      setUpgrading(false);
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
              Upgrade Your <span className="gradient-text">Analysis Depth</span>
            </h1>
            <p className="text-muted-foreground max-w-md mx-auto">
              Select an advanced research tier to generate a comprehensive multi-agent validation report.
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

                <h3 className="text-xl font-bold mb-3">{tier.name}</h3>
                <p className="text-xs text-muted-foreground mb-5 italic">{tier.bestFor}</p>

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
                  disabled={upgrading}
                  className={`w-full flex items-center justify-center gap-2 py-3 rounded-lg text-sm font-semibold transition-all group ${
                    tier.recommended
                      ? 'bg-primary text-primary-foreground hover:bg-primary/90'
                      : 'glass hover:bg-secondary/50'
                  }`}
                >
                  {upgrading ? <Loader2 className="w-4 h-4 animate-spin" /> : <>Request {tier.name}</>}
                  <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                </button>
              </motion.div>
            ))}
          </div>

          {/* Academic Trust Elements */}
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="flex flex-col sm:flex-row items-center justify-center gap-6 mt-10"
          >
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Shield className="w-4 h-4 text-primary" />
              Verified AI Framework
            </div>
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Clock className="w-4 h-4 text-primary" />
              Comprehensive analysis in 5-10 minutes
            </div>
          </motion.div>
        </div>
      </div>

      <Footer />
    </div>
  );
}
