// Reusable report component types and utilities
import { motion } from 'framer-motion';
import { ChevronDown, ChevronUp, TrendingUp, TrendingDown, DollarSign, Users, Target, AlertTriangle, Shield, Zap, Globe, Building2, Briefcase, LineChart, PieChart, Layers } from 'lucide-react';
import { useState } from 'react';

// Module section wrapper
export function ModuleSection({
    title,
    icon: Icon,
    children,
    defaultOpen = true
}: {
    title: string;
    icon?: any;
    children: React.ReactNode;
    defaultOpen?: boolean;
}) {
    const [isOpen, setIsOpen] = useState(defaultOpen);

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="glass rounded-2xl overflow-hidden mb-6"
        >
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="w-full p-6 flex items-center justify-between hover:bg-secondary/20 transition-colors"
            >
                <div className="flex items-center gap-3">
                    {Icon && <Icon className="w-5 h-5 text-primary" />}
                    <h3 className="text-lg font-semibold">{title}</h3>
                </div>
                {isOpen ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
            </button>
            {isOpen && <div className="px-6 pb-6">{children}</div>}
        </motion.div>
    );
}

// Data table component
export function DataTable({
    headers,
    rows,
    className = ''
}: {
    headers: string[];
    rows: (string | React.ReactNode)[][];
    className?: string;
}) {
    return (
        <div className={`overflow-x-auto ${className}`}>
            <table className="w-full text-sm">
                <thead>
                    <tr className="border-b border-white/10">
                        {headers.map((header, i) => (
                            <th key={i} className="text-left py-3 px-4 text-muted-foreground font-medium">{header}</th>
                        ))}
                    </tr>
                </thead>
                <tbody>
                    {rows.map((row, i) => (
                        <tr key={i} className="border-b border-white/5 hover:bg-secondary/20 transition-colors">
                            {row.map((cell, j) => (
                                <td key={j} className="py-3 px-4">{cell}</td>
                            ))}
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}

// Market size card (TAM/SAM/SOM)
export function MarketSizeCard({
    title,
    value,
    details,
    sources
}: {
    title: string;
    value: string;
    details?: { definition?: string; estimation_method?: string; cross_check?: string };
    sources?: string[];
}) {
    const [showDetails, setShowDetails] = useState(false);

    return (
        <div className="bg-secondary/30 rounded-xl p-5 hover:bg-secondary/40 transition-colors">
            <div className="flex items-center justify-between mb-3">
                <span className="text-xs uppercase tracking-wider text-muted-foreground">{title}</span>
                <Globe className="w-4 h-4 text-primary" />
            </div>
            <p className="text-2xl font-bold text-primary mb-2">{value}</p>

            {details?.definition && (
                <>
                    <button
                        onClick={() => setShowDetails(!showDetails)}
                        className="text-xs text-muted-foreground hover:text-primary flex items-center gap-1"
                    >
                        {showDetails ? 'Hide' : 'Show'} details
                        {showDetails ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                    </button>

                    {showDetails && (
                        <div className="mt-3 space-y-2 text-xs text-muted-foreground">
                            <p><strong>Definition:</strong> {details.definition}</p>
                            {details.estimation_method && <p><strong>Method:</strong> {details.estimation_method}</p>}
                            {details.cross_check && <p><strong>Validation:</strong> {details.cross_check}</p>}
                            {sources && sources.length > 0 && (
                                <div>
                                    <strong>Sources:</strong>
                                    <ul className="list-disc list-inside mt-1">
                                        {sources.slice(0, 3).map((s, i) => <li key={i}>{s}</li>)}
                                    </ul>
                                </div>
                            )}
                        </div>
                    )}
                </>
            )}
        </div>
    );
}

// Key metric card
export function MetricCard({
    label,
    value,
    subtext,
    trend
}: {
    label: string;
    value: string | number;
    subtext?: string;
    trend?: 'up' | 'down' | 'neutral';
}) {
    return (
        <div className="bg-secondary/30 rounded-xl p-4">
            <p className="text-xs text-muted-foreground mb-1">{label}</p>
            <div className="flex items-center gap-2">
                <span className="text-xl font-bold">{value}</span>
                {trend === 'up' && <TrendingUp className="w-4 h-4 text-green-500" />}
                {trend === 'down' && <TrendingDown className="w-4 h-4 text-red-500" />}
            </div>
            {subtext && <p className="text-xs text-muted-foreground mt-1">{subtext}</p>}
        </div>
    );
}

// Risk badge
export function RiskBadge({ level }: { level: string }) {
    const colors: Record<string, string> = {
        high: 'bg-red-500/20 text-red-400 border-red-500/30',
        medium: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
        low: 'bg-green-500/20 text-green-400 border-green-500/30',
    };
    const icons: Record<string, string> = {
        high: '🔴',
        medium: '🟡',
        low: '🟢',
    };

    const lowerLevel = level.toLowerCase();

    return (
        <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs border ${colors[lowerLevel] || colors.medium}`}>
            {icons[lowerLevel] || icons.medium} {level}
        </span>
    );
}

// List with bullets
export function BulletList({ items, className = '' }: { items: string[]; className?: string }) {
    return (
        <ul className={`space-y-2 ${className}`}>
            {items.map((item, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-muted-foreground">
                    <div className="w-1.5 h-1.5 rounded-full bg-primary mt-2 shrink-0" />
                    <span>{item}</span>
                </li>
            ))}
        </ul>
    );
}

// Get icon for module
export function getModuleIcon(moduleKey: string) {
    const icons: Record<string, any> = {
        market_analysis: Globe,
        financial_feasibility: DollarSign,
        financials: DollarSign,
        competitive_intelligence: Shield,
        technical_roadmap: Layers,
        go_to_market_strategy: Target,
        gtm_strategy: Target,
        risk_analysis: AlertTriangle,
        investor_pitch_deck: Briefcase,
        business_model_canvas: Building2,
    };
    return icons[moduleKey] || Zap;
}

// Format key to title
export function formatKey(key: string): string {
    return key
        .replace(/_/g, ' ')
        .replace(/\b\w/g, c => c.toUpperCase());
}
