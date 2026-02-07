import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Mail, Lock, Loader2, ArrowRight, Sparkles } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';

interface AuthModalProps {
    isOpen: boolean;
    onClose: () => void;
    defaultMode?: 'signin' | 'signup';
}

export function AuthModal({ isOpen, onClose, defaultMode = 'signin' }: AuthModalProps) {
    const [mode, setMode] = useState<'signin' | 'signup' | 'magic'>(defaultMode);
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [magicLinkSent, setMagicLinkSent] = useState(false);

    const { signIn, signUp, signInWithMagicLink, linkCurrentSession } = useAuth();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError('');

        try {
            if (mode === 'magic') {
                const { error } = await signInWithMagicLink(email);
                if (error) throw error;
                setMagicLinkSent(true);
            } else if (mode === 'signup') {
                const { error } = await signUp(email, password);
                if (error) throw error;
                await linkCurrentSession();
                onClose();
            } else {
                const { error } = await signIn(email, password);
                if (error) throw error;
                await linkCurrentSession();
                onClose();
            }
        } catch (err) {
            setError(err instanceof Error ? err.message : 'An error occurred');
        } finally {
            setLoading(false);
        }
    };

    if (!isOpen) return null;

    return (
        <AnimatePresence>
            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-background/80 backdrop-blur-sm"
                onClick={onClose}
            >
                <motion.div
                    initial={{ scale: 0.95, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    exit={{ scale: 0.95, opacity: 0 }}
                    onClick={(e) => e.stopPropagation()}
                    className="glass-strong rounded-2xl p-8 max-w-md w-full relative"
                >
                    <button
                        onClick={onClose}
                        className="absolute top-4 right-4 text-muted-foreground hover:text-foreground transition-colors"
                    >
                        <X className="w-5 h-5" />
                    </button>

                    {magicLinkSent ? (
                        <div className="text-center py-8">
                            <motion.div
                                initial={{ scale: 0 }}
                                animate={{ scale: 1 }}
                                className="w-16 h-16 rounded-full bg-primary/20 flex items-center justify-center mx-auto mb-4"
                            >
                                <Mail className="w-8 h-8 text-primary" />
                            </motion.div>
                            <h3 className="text-xl font-bold mb-2">Check your email</h3>
                            <p className="text-sm text-muted-foreground">
                                We sent a magic link to <strong>{email}</strong>
                            </p>
                            <button
                                onClick={() => setMagicLinkSent(false)}
                                className="mt-4 text-sm text-primary hover:underline"
                            >
                                Try a different email
                            </button>
                        </div>
                    ) : (
                        <>
                            <div className="flex items-center gap-2 mb-6">
                                <Sparkles className="w-5 h-5 text-primary" />
                                <h3 className="text-lg font-bold">
                                    {mode === 'signup' ? 'Create Account' : mode === 'magic' ? 'Magic Link' : 'Welcome Back'}
                                </h3>
                            </div>

                            <form onSubmit={handleSubmit} className="space-y-4">
                                <div>
                                    <label className="block text-xs font-medium mb-1.5 text-muted-foreground">Email</label>
                                    <div className="relative">
                                        <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                                        <input
                                            type="email"
                                            value={email}
                                            onChange={(e) => setEmail(e.target.value)}
                                            placeholder="you@example.com"
                                            required
                                            className="w-full pl-10 pr-3 py-2.5 rounded-lg bg-secondary/50 border border-border text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
                                        />
                                    </div>
                                </div>

                                {mode !== 'magic' && (
                                    <div>
                                        <label className="block text-xs font-medium mb-1.5 text-muted-foreground">Password</label>
                                        <div className="relative">
                                            <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                                            <input
                                                type="password"
                                                value={password}
                                                onChange={(e) => setPassword(e.target.value)}
                                                placeholder="••••••••"
                                                required
                                                minLength={6}
                                                className="w-full pl-10 pr-3 py-2.5 rounded-lg bg-secondary/50 border border-border text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
                                            />
                                        </div>
                                    </div>
                                )}

                                {error && (
                                    <p className="text-sm text-destructive">{error}</p>
                                )}

                                <button
                                    type="submit"
                                    disabled={loading}
                                    className="w-full flex items-center justify-center gap-2 py-3 rounded-lg bg-primary text-primary-foreground font-semibold disabled:opacity-70 hover:bg-primary/90 transition-all"
                                >
                                    {loading ? (
                                        <>
                                            <Loader2 className="w-4 h-4 animate-spin" />
                                            {mode === 'magic' ? 'Sending...' : mode === 'signup' ? 'Creating...' : 'Signing in...'}
                                        </>
                                    ) : (
                                        <>
                                            {mode === 'magic' ? 'Send Magic Link' : mode === 'signup' ? 'Create Account' : 'Sign In'}
                                            <ArrowRight className="w-4 h-4" />
                                        </>
                                    )}
                                </button>
                            </form>

                            <div className="mt-4 space-y-2 text-center text-sm">
                                {mode === 'signin' && (
                                    <>
                                        <button
                                            onClick={() => setMode('magic')}
                                            className="text-muted-foreground hover:text-foreground transition-colors"
                                        >
                                            Sign in with magic link instead
                                        </button>
                                        <p className="text-muted-foreground">
                                            Don't have an account?{' '}
                                            <button onClick={() => setMode('signup')} className="text-primary hover:underline">
                                                Sign up
                                            </button>
                                        </p>
                                    </>
                                )}
                                {mode === 'signup' && (
                                    <p className="text-muted-foreground">
                                        Already have an account?{' '}
                                        <button onClick={() => setMode('signin')} className="text-primary hover:underline">
                                            Sign in
                                        </button>
                                    </p>
                                )}
                                {mode === 'magic' && (
                                    <button
                                        onClick={() => setMode('signin')}
                                        className="text-muted-foreground hover:text-foreground transition-colors"
                                    >
                                        Sign in with password instead
                                    </button>
                                )}
                            </div>
                        </>
                    )}
                </motion.div>
            </motion.div>
        </AnimatePresence>
    );
}
