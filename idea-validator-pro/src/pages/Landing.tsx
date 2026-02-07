import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { ArrowRight, Rocket, Bot, BarChart3, Gem, Shield, Clock, Zap, Star, ChevronLeft, ChevronRight, Lock } from 'lucide-react';
import { Navbar } from '@/components/Navbar';
import { Footer } from '@/components/Footer';
import { FloatingOrbs } from '@/components/FloatingOrbs';
import heroBrain from '@/assets/hero-brain.jpg';
import { useState } from 'react';

const fadeUp = {
  hidden: { opacity: 0, y: 30 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { delay: i * 0.15, duration: 0.6, ease: [0.25, 0.46, 0.45, 0.94] as const },
  }),
};

const steps = [
  { icon: Rocket, title: 'Submit Your Idea', desc: 'Describe your startup in detail', color: 'text-primary' },
  { icon: Bot, title: 'AI Interview', desc: 'Answer 10 smart questions from our AI', color: 'text-accent' },
  { icon: BarChart3, title: 'Free Report', desc: 'Get your viability score instantly', color: 'text-primary' },
  { icon: Gem, title: 'Deep Dive', desc: 'Unlock premium analysis & pitch deck', color: 'text-accent' },
];

const tiers = [
  {
    name: 'Free',
    price: '$0',
    features: ['Viability Score', '5 Score Dimensions', 'Value Proposition', 'Customer Profile', 'Next Step'],
    highlight: false,
  },
  {
    name: 'Basic',
    price: '$49',
    features: ['Everything in Free', 'Business Model Canvas', 'Executive Summary', 'Go/No-Go Score'],
    highlight: false,
  },
  {
    name: 'Standard',
    price: '$149',
    features: ['Everything in Basic', 'Full Market Analysis', 'Competitive Intelligence', 'Financial Projections', 'Go-to-Market Strategy'],
    highlight: true,
    badge: 'Most Popular',
  },
  {
    name: 'Premium',
    price: '$299',
    features: ['Everything in Standard', 'Investor Pitch Deck', 'Custom Module Selection', 'Priority Processing'],
    highlight: false,
  },
];

const testimonials = [
  {
    name: 'Sarah Chen',
    role: 'CEO, FinFlow',
    text: "ValidateAI saved us months of guesswork. The market analysis alone was worth 10x the price. We raised our seed round using their insights.",
    avatar: 'SC',
  },
  {
    name: 'Marcus Williams',
    role: 'CTO, HealthBridge',
    text: "The AI interview asked questions we hadn't even considered. The competitive intelligence section revealed blind spots that shaped our entire strategy.",
    avatar: 'MW',
  },
  {
    name: 'Priya Patel',
    role: 'Founder, DataSync',
    text: "I was skeptical about AI validation, but the depth of analysis was incredible. The financial projections were more thorough than what our advisors provided.",
    avatar: 'PP',
  },
];

const sampleSections = [
  'Market Analysis',
  'Competitive Intel',
  'Financial Projections',
  'Go-to-Market Strategy',
  'Risk Analysis',
  'Technical Roadmap',
];

export default function Landing() {
  const [activeTestimonial, setActiveTestimonial] = useState(0);

  return (
    <div className="min-h-screen relative">
      <FloatingOrbs />
      <Navbar />

      {/* Hero Section */}
      <section className="relative pt-32 pb-20 overflow-hidden">
        <div className="container mx-auto px-6">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <motion.div
              initial="hidden"
              animate="visible"
              className="relative z-10"
            >
              <motion.div custom={0} variants={fadeUp} className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full glass text-xs text-muted-foreground mb-6">
                <Zap className="w-3 h-3 text-primary" />
                100+ Startups Validated • Backed by YC Founders
              </motion.div>

              <motion.h1 custom={1} variants={fadeUp} className="text-4xl md:text-5xl lg:text-6xl font-extrabold leading-tight mb-6">
                Validate Your Startup Idea in{' '}
                <span className="gradient-text">Minutes</span>
                , Not Months
              </motion.h1>

              <motion.p custom={2} variants={fadeUp} className="text-lg text-muted-foreground mb-8 max-w-lg">
                AI-powered deep analysis. Get investor-grade insights before you invest a single dollar.
              </motion.p>

              <motion.div custom={3} variants={fadeUp} className="flex flex-col sm:flex-row gap-4">
                <Link
                  to="/submit"
                  className="inline-flex items-center justify-center gap-2 px-6 py-3 rounded-lg bg-primary text-primary-foreground font-semibold hover:bg-primary/90 transition-all glow-pulse group"
                >
                  Get Your Free Viability Report
                  <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                </Link>
                <a
                  href="#how-it-works"
                  className="inline-flex items-center justify-center gap-2 px-6 py-3 rounded-lg glass text-foreground font-medium hover:bg-secondary/50 transition-all"
                >
                  See How It Works
                </a>
              </motion.div>

              <motion.div custom={4} variants={fadeUp} className="flex items-center gap-6 mt-8 text-xs text-muted-foreground">
                <div className="flex items-center gap-1.5">
                  <Shield className="w-3.5 h-3.5 text-primary" />
                  Encrypted & Secure
                </div>
                <div className="flex items-center gap-1.5">
                  <Clock className="w-3.5 h-3.5 text-accent" />
                  ~10 Minutes
                </div>
                <div className="flex items-center gap-1.5">
                  <Zap className="w-3.5 h-3.5 text-primary" />
                  Instant Results
                </div>
              </motion.div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.4, duration: 0.8 }}
              className="relative hidden lg:block"
            >
              <div className="relative rounded-2xl overflow-hidden glow-primary">
                <img src={heroBrain} alt="AI-powered startup validation visualization" className="w-full h-auto rounded-2xl" />
                <div className="absolute inset-0 bg-gradient-to-t from-background/80 to-transparent" />
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section id="how-it-works" className="py-20">
        <div className="container mx-auto px-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <h2 className="text-3xl md:text-4xl font-bold mb-4">
              How It <span className="gradient-text">Works</span>
            </h2>
            <p className="text-muted-foreground max-w-md mx-auto">
              From idea to investor-grade insights in four simple steps
            </p>
          </motion.div>

          <div className="grid md:grid-cols-4 gap-6 relative">
            <div className="hidden md:block absolute top-1/2 left-0 right-0 h-px bg-gradient-to-r from-transparent via-border to-transparent -translate-y-1/2" />
            {steps.map((step, i) => (
              <motion.div
                key={step.title}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.15 }}
                className="relative glass rounded-xl p-6 text-center hover:bg-secondary/30 transition-all group"
              >
                <div className="w-12 h-12 rounded-xl bg-secondary flex items-center justify-center mx-auto mb-4 group-hover:scale-110 transition-transform">
                  <step.icon className={`w-6 h-6 ${step.color}`} />
                </div>
                <div className="text-xs font-mono text-muted-foreground mb-2">Step {i + 1}</div>
                <h3 className="font-semibold mb-2">{step.title}</h3>
                <p className="text-sm text-muted-foreground">{step.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Sample Report Preview */}
      <section className="py-20">
        <div className="container mx-auto px-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-12"
          >
            <h2 className="text-3xl md:text-4xl font-bold mb-4">
              See What You'll <span className="gradient-text">Get</span>
            </h2>
            <p className="text-muted-foreground max-w-md mx-auto">
              A comprehensive analysis covering every angle of your startup
            </p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="max-w-3xl mx-auto glass rounded-2xl p-8 relative overflow-hidden group"
          >
            <div className="absolute inset-0 bg-gradient-to-b from-transparent to-background/90 z-10 pointer-events-none" />
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4 blur-[2px] group-hover:blur-[1px] transition-all duration-500">
              {sampleSections.map((section, i) => (
                <div key={section} className="glass rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <Lock className="w-3.5 h-3.5 text-muted-foreground" />
                    <span className="text-sm font-medium">{section}</span>
                  </div>
                  <div className="space-y-1.5">
                    <div className="h-2 rounded bg-secondary w-full" />
                    <div className="h-2 rounded bg-secondary w-3/4" />
                    <div className="h-2 rounded bg-secondary w-1/2" />
                  </div>
                </div>
              ))}
            </div>
            <div className="absolute bottom-8 left-0 right-0 z-20 text-center">
              <Link
                to="/submit"
                className="inline-flex items-center gap-2 px-6 py-3 rounded-lg bg-primary text-primary-foreground font-semibold hover:bg-primary/90 transition-all"
              >
                Unlock Your Report
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Pricing */}
      <section id="pricing" className="py-20">
        <div className="container mx-auto px-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <h2 className="text-3xl md:text-4xl font-bold mb-4">
              Simple, Transparent <span className="gradient-text">Pricing</span>
            </h2>
            <p className="text-muted-foreground max-w-md mx-auto">
              Start free, upgrade when you need deeper insights
            </p>
          </motion.div>

          <div className="grid md:grid-cols-4 gap-6 max-w-5xl mx-auto">
            {tiers.map((tier, i) => (
              <motion.div
                key={tier.name}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1 }}
                className={`relative glass rounded-xl p-6 transition-all hover:scale-[1.02] ${
                  tier.highlight ? 'ring-2 ring-primary glow-primary' : ''
                }`}
              >
                {tier.badge && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-1 rounded-full bg-primary text-primary-foreground text-xs font-semibold whitespace-nowrap">
                    {tier.badge}
                  </div>
                )}
                <h3 className="text-lg font-semibold mb-1">{tier.name}</h3>
                <div className="text-3xl font-bold mb-4">{tier.price}</div>
                <ul className="space-y-2 mb-6">
                  {tier.features.map((f) => (
                    <li key={f} className="flex items-start gap-2 text-sm text-muted-foreground">
                      <div className="w-1.5 h-1.5 rounded-full bg-primary mt-1.5 shrink-0" />
                      {f}
                    </li>
                  ))}
                </ul>
                <Link
                  to="/submit"
                  className={`block text-center py-2.5 rounded-lg text-sm font-semibold transition-all ${
                    tier.highlight
                      ? 'bg-primary text-primary-foreground hover:bg-primary/90'
                      : 'glass hover:bg-secondary/50 text-foreground'
                  }`}
                >
                  {tier.price === '$0' ? 'Start Free' : `Get ${tier.name}`}
                </Link>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Testimonials */}
      <section id="testimonials" className="py-20">
        <div className="container mx-auto px-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-12"
          >
            <h2 className="text-3xl md:text-4xl font-bold mb-4">
              Trusted by <span className="gradient-text">Founders</span>
            </h2>
          </motion.div>

          <div className="max-w-2xl mx-auto">
            <motion.div
              key={activeTestimonial}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="glass rounded-2xl p-8 text-center"
            >
              <div className="flex justify-center mb-4 gap-1">
                {[...Array(5)].map((_, i) => (
                  <Star key={i} className="w-4 h-4 fill-primary text-primary" />
                ))}
              </div>
              <p className="text-lg mb-6 leading-relaxed">
                "{testimonials[activeTestimonial].text}"
              </p>
              <div className="flex items-center justify-center gap-3">
                <div className="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center text-sm font-bold text-primary">
                  {testimonials[activeTestimonial].avatar}
                </div>
                <div className="text-left">
                  <div className="font-semibold text-sm">{testimonials[activeTestimonial].name}</div>
                  <div className="text-xs text-muted-foreground">{testimonials[activeTestimonial].role}</div>
                </div>
              </div>
            </motion.div>

            <div className="flex items-center justify-center gap-4 mt-6">
              <button
                onClick={() => setActiveTestimonial((prev) => (prev === 0 ? testimonials.length - 1 : prev - 1))}
                className="w-8 h-8 rounded-full glass flex items-center justify-center hover:bg-secondary/50 transition-colors"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <div className="flex gap-2">
                {testimonials.map((_, i) => (
                  <button
                    key={i}
                    onClick={() => setActiveTestimonial(i)}
                    className={`w-2 h-2 rounded-full transition-all ${
                      i === activeTestimonial ? 'bg-primary w-6' : 'bg-muted-foreground/30'
                    }`}
                  />
                ))}
              </div>
              <button
                onClick={() => setActiveTestimonial((prev) => (prev === testimonials.length - 1 ? 0 : prev + 1))}
                className="w-8 h-8 rounded-full glass flex items-center justify-center hover:bg-secondary/50 transition-colors"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* Final CTA */}
      <section className="py-20">
        <div className="container mx-auto px-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="max-w-2xl mx-auto text-center glass rounded-2xl p-12"
          >
            <h2 className="text-3xl font-bold mb-4">
              Ready to <span className="gradient-text">Validate</span> Your Idea?
            </h2>
            <p className="text-muted-foreground mb-8">
              Join 100+ founders who've used AI-powered insights to make smarter decisions.
            </p>
            <Link
              to="/submit"
              className="inline-flex items-center gap-2 px-8 py-4 rounded-lg bg-primary text-primary-foreground font-bold text-lg hover:bg-primary/90 transition-all glow-pulse group"
            >
              Start Your Free Analysis
              <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
            </Link>
          </motion.div>
        </div>
      </section>

      <Footer />
    </div>
  );
}
