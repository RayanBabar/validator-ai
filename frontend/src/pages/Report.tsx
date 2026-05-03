import { useEffect, useState, useRef } from 'react';
import { useParams, useNavigate, useSearchParams, Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { BarChart3, AlertTriangle, Lightbulb, Target, Users, Lock, ArrowRight, TrendingUp, Shield, Zap, Brain, Globe, DollarSign, Building2, Briefcase, Layers, ChevronDown, ChevronUp, CheckCircle2, XCircle, Edit3, Save, CheckCircle, Code, Eye, X, Download, Star } from 'lucide-react';
import { Navbar } from '@/components/Navbar';
import { FloatingOrbs } from '@/components/FloatingOrbs';
import { Footer } from '@/components/Footer';
import { getReport, getScoreColorClass, getScoreBgClass, adminSave, adminApprove } from '@/lib/api';
import { ModuleSection, DataTable, MarketSizeCard, MetricCard, RiskBadge, BulletList, getModuleIcon, formatKey } from '@/components/ReportModules';

function AnimatedScore({ value, max }: { value: number; max: number }) {
  const [count, setCount] = useState(0);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let start = 0;
    const duration = 1500;
    const startTime = performance.now();

    const animate = (currentTime: number) => {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      start = Math.round(eased * value);
      setCount(start);
      if (progress < 1) requestAnimationFrame(animate);
    };

    requestAnimationFrame(animate);
  }, [value]);

  const pct = (count / max) * 100;
  const radius = 60;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (pct / 100) * circumference;

  return (
    <div className="relative w-40 h-40 mx-auto" ref={ref}>
      <svg className="w-full h-full -rotate-90" viewBox="0 0 140 140">
        <circle cx="70" cy="70" r={radius} stroke="hsl(var(--secondary))" strokeWidth="8" fill="none" />
        <circle
          cx="70"
          cy="70"
          r={radius}
          stroke="url(#scoreGradient)"
          strokeWidth="8"
          fill="none"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          style={{ transition: 'stroke-dashoffset 1.5s ease-out' }}
        />
        <defs>
          <linearGradient id="scoreGradient" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="hsl(var(--primary))" />
            <stop offset="100%" stopColor="hsl(var(--accent))" />
          </linearGradient>
        </defs>
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className={`text-4xl font-bold font-mono ${getScoreColorClass(count, max)}`}>{count}</span>
        <span className="text-xs text-muted-foreground">/ {max}</span>
      </div>
    </div>
  );
}

const dimensionIcons: Record<string, typeof BarChart3> = {
  problem_severity: AlertTriangle,
  market_opportunity: TrendingUp,
  competition_intensity: Shield,
  execution_complexity: Zap,
  founder_alignment: Users,
  market_demand: TrendingUp,
  financial_viability: DollarSign,
  competition_analysis: Shield,
  founder_market_fit: Users,
  technical_feasibility: Layers,
  regulatory_compliance: Building2,
  timing_assessment: Target,
  scalability_potential: Globe,
};

const dimensionLabels: Record<string, string> = {
  problem_severity: 'Problem Severity',
  market_opportunity: 'Market Opportunity',
  competition_intensity: 'Competition Intensity',
  execution_complexity: 'Execution Complexity',
  founder_alignment: 'Founder Alignment',
  market_demand: 'Market Demand',
  financial_viability: 'Financial Viability',
  competition_analysis: 'Competition Analysis',
  founder_market_fit: 'Founder-Market Fit',
  technical_feasibility: 'Technical Feasibility',
  regulatory_compliance: 'Regulatory Compliance',
  timing_assessment: 'Timing Assessment',
  scalability_potential: 'Scalability Potential',
};

// Market Analysis Module
function MarketAnalysisModule({ data }: { data: any }) {
  if (!data) return null;

  return (
    <ModuleSection title="Market Analysis" icon={Globe}>
      {/* TAM/SAM/SOM Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        {data.total_addressable_market && (
          <MarketSizeCard
            title="TAM (Total Addressable)"
            value={data.total_addressable_market.market_size || data.total_addressable_market.value}
            details={data.total_addressable_market.growth_rate || data.total_addressable_market.details}
            sources={data.total_addressable_market.drivers || data.total_addressable_market.sources}
          />
        )}
        {data.serviceable_addressable_market && (
          <MarketSizeCard
            title="SAM (Serviceable Addressable)"
            value={data.serviceable_addressable_market.market_size || data.serviceable_addressable_market.value}
            details={data.serviceable_addressable_market.growth_rate || data.serviceable_addressable_market.details}
            sources={data.serviceable_addressable_market.drivers || data.serviceable_addressable_market.sources}
          />
        )}
        {data.serviceable_obtainable_market && (
          <MarketSizeCard
            title="SOM (Serviceable Obtainable)"
            value={data.serviceable_obtainable_market.market_size || data.serviceable_obtainable_market.value}
            details={data.serviceable_obtainable_market.growth_rate || data.serviceable_obtainable_market.details}
            sources={data.serviceable_obtainable_market.drivers || data.serviceable_obtainable_market.sources}
          />
        )}
      </div>

      {/* Growth Trends */}
      {data.growth_trends && (
        <div className="mb-6">
          <h4 className="text-sm font-medium mb-3 flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-primary" /> Market Dynamics
          </h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
             <div className="bg-secondary/30 rounded-xl p-4">
                <p className="text-xs font-semibold mb-2">Growth Trajectory</p>
                <p className="text-sm text-muted-foreground">{data.growth_trends.growth_trajectory}</p>
             </div>
             <div className="bg-secondary/30 rounded-xl p-4">
                <p className="text-xs font-semibold mb-2">Key Drivers</p>
                <BulletList items={data.growth_trends.drivers} />
             </div>
          </div>
        </div>
      )}

      {/* Customer Demographics */}
      {data.customer_demographics && (
        <div className="mb-6">
          <h4 className="text-sm font-medium mb-3">Target Customer Segment</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-secondary/30 rounded-xl p-4">
               <div className="space-y-2">
                 <p className="text-xs text-muted-foreground"><span className="font-semibold text-primary">Location:</span> {data.customer_demographics.location}</p>
                 <p className="text-xs text-muted-foreground"><span className="font-semibold text-primary">Age:</span> {data.customer_demographics.age_range}</p>
                 <p className="text-xs text-muted-foreground"><span className="font-semibold text-primary">Income:</span> {data.customer_demographics.income_level}</p>
               </div>
            </div>
            <div className="bg-secondary/30 rounded-xl p-4">
               <p className="text-xs font-semibold mb-2">Psychographics & Behavior</p>
               <p className="text-xs text-muted-foreground">{data.customer_demographics.psychographics}</p>
            </div>
          </div>
        </div>
      )}
    </ModuleSection>
  );
}

// Financial Feasibility Module
function FinancialsModule({ data }: { data: any }) {
  if (!data) return null;

  return (
    <ModuleSection title="Financial Modeling" icon={DollarSign}>
      <div className="space-y-6">
        {/* 3-Year Summary */}
        {data.three_year_projections && (
          <div>
            <h4 className="text-sm font-medium mb-3">3-Year Financial Forecast</h4>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
               {[
                 { label: 'Year 1 Revenue', val: data.three_year_projections.year_1_detailed?.revenue || data.three_year_projections.year_1_revenue, color: 'text-green-400' },
                 { label: 'Year 2 Revenue', val: data.three_year_projections.year_2_detailed?.revenue || data.three_year_projections.year_2_revenue, color: 'text-green-400' },
                 { label: 'Year 3 Revenue', val: data.three_year_projections.year_3_detailed?.revenue || data.three_year_projections.year_3_revenue, color: 'text-green-400' },
               ].map((m, i) => (
                 <div key={i} className="bg-secondary/30 rounded-xl p-4 border border-white/5">
                    <p className="text-[10px] font-semibold text-muted-foreground uppercase">{m.label}</p>
                    <p className={`text-lg font-bold ${m.color}`}>{m.val || 'N/A'}</p>
                 </div>
               ))}
            </div>
          </div>
        )}

        {/* Unit Economics & Burn */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {data.unit_economics && (
            <div className="bg-secondary/30 rounded-xl p-5">
              <h4 className="text-xs font-semibold mb-3 uppercase tracking-wider text-primary">Unit Economics</h4>
              <div className="space-y-2">
                <div className="flex justify-between text-xs">
                   <span className="text-muted-foreground">Customer Acquisition Cost (CAC)</span>
                   <span className="font-bold">{data.unit_economics.cac}</span>
                </div>
                <div className="flex justify-between text-xs">
                   <span className="text-muted-foreground">Lifetime Value (LTV)</span>
                   <span className="font-bold text-green-400">{data.unit_economics.ltv}</span>
                </div>
                <div className="flex justify-between text-xs">
                   <span className="text-muted-foreground">LTV/CAC Ratio</span>
                   <span className="font-bold">{data.unit_economics.ltv_cac_ratio}</span>
                </div>
              </div>
            </div>
          )}
          {data.burn_rate_runway && (
            <div className="bg-secondary/30 rounded-xl p-5">
              <h4 className="text-xs font-semibold mb-3 uppercase tracking-wider text-primary">Burn & Runway</h4>
              <div className="space-y-2">
                <div className="flex justify-between text-xs">
                   <span className="text-muted-foreground">Monthly Burn</span>
                   <span className="font-bold text-red-400">{data.burn_rate_runway.monthly_burn_rate}</span>
                </div>
                <div className="flex justify-between text-xs">
                   <span className="text-muted-foreground">Runway</span>
                   <span className="font-bold">{data.burn_rate_runway.runway_months} months</span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Revenue Model */}
        {data.revenue_model && (
          <div className="bg-secondary/30 rounded-xl p-5">
            <h4 className="text-xs font-semibold mb-3 uppercase tracking-wider text-primary">Revenue Streams</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <p className="text-xs font-bold mb-2">Primary Model: {data.revenue_model.primary_revenue_model}</p>
                <BulletList items={data.revenue_model.revenue_streams} />
              </div>
              <div className="bg-primary/5 rounded-lg p-3">
                 <p className="text-[10px] font-semibold text-primary mb-1">Pricing Strategy</p>
                 <p className="text-xs text-muted-foreground italic">{data.revenue_model.pricing_strategy}</p>
              </div>
            </div>
          </div>
        )}
      </div>
    </ModuleSection>
  );
}

// Competitive Intelligence Module
function CompetitiveIntelligenceModule({ data }: { data: any }) {
  if (!data) return null;

  return (
    <ModuleSection title="Competitive Intelligence" icon={Shield}>
      {/* Direct Competitors */}
      {data.direct_competitors && (
        <div className="mb-6">
          <h4 className="text-sm font-medium mb-3">Direct Competitors</h4>
          <div className="space-y-3">
            {data.direct_competitors.map((comp: any, i: number) => (
              <div key={i} className="bg-secondary/30 rounded-xl p-4">
                <div className="flex justify-between items-start mb-2">
                  <div>
                    <span className="font-medium">{comp.name}</span>
                    <span className="block text-xs text-muted-foreground">{comp.hq_location}</span>
                  </div>
                  <RiskBadge level={comp.threat_score} />
                </div>
                <p className="text-xs text-muted-foreground mb-1"><strong>Position:</strong> {comp.market_position}</p>
                <p className="text-xs text-muted-foreground">{comp.threat_rationale}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Competitive Positioning */}
      {data.competitive_positioning && (
        <div className="mb-6">
          <h4 className="text-sm font-medium mb-3">Competitive Positioning Map</h4>

          {/* Quadrant Chart */}
          {data.competitive_positioning.competitor_positions && (
            <div className="bg-secondary/30 rounded-xl p-4 mb-4">
              <div className="relative w-full h-64 border border-white/10 rounded-lg">
                {/* Axes Labels */}
                <div className="absolute top-2 left-1/2 -translate-x-1/2 text-xs text-muted-foreground">
                  {data.competitive_positioning.y_axis || 'High Value'}
                </div>
                <div className="absolute bottom-2 left-1/2 -translate-x-1/2 text-xs text-muted-foreground">
                  Low
                </div>
                <div className="absolute left-2 top-1/2 -translate-y-1/2 text-xs text-muted-foreground -rotate-90">
                  {data.competitive_positioning.x_axis || 'Low Cost'}
                </div>
                <div className="absolute right-2 top-1/2 -translate-y-1/2 text-xs text-muted-foreground rotate-90">
                  High
                </div>

                {/* Center lines */}
                <div className="absolute top-0 left-1/2 h-full border-l border-dashed border-white/20" />
                <div className="absolute left-0 top-1/2 w-full border-t border-dashed border-white/20" />

                {/* Quadrant Labels */}
                <div className="absolute top-4 left-4 text-[10px] text-green-400 opacity-60">Top-Left</div>
                <div className="absolute top-4 right-4 text-[10px] text-blue-400 opacity-60">Top-Right</div>
                <div className="absolute bottom-4 left-4 text-[10px] text-red-400 opacity-60">Bottom-Left</div>
                <div className="absolute bottom-4 right-4 text-[10px] text-yellow-400 opacity-60">Bottom-Right</div>

                {/* Competitor Dots */}
                {data.competitive_positioning.competitor_positions.map((comp: any, i: number) => {
                  const getPosition = (quadrant: string) => {
                    const jitter = () => Math.random() * 15 - 7.5;
                    if (quadrant.includes('Top-Left')) return { left: 15 + jitter(), top: 20 + jitter() };
                    if (quadrant.includes('Top-Right')) return { left: 60 + jitter(), top: 20 + jitter() };
                    if (quadrant.includes('Bottom-Left')) return { left: 15 + jitter(), top: 60 + jitter() };
                    if (quadrant.includes('Bottom-Right')) return { left: 60 + jitter(), top: 60 + jitter() };
                    return { left: 40, top: 40 };
                  };
                  const getColor = (quadrant: string) => {
                    if (quadrant.includes('Top-Left')) return 'bg-green-500';
                    if (quadrant.includes('Top-Right')) return 'bg-blue-500';
                    if (quadrant.includes('Bottom-Left')) return 'bg-red-500';
                    if (quadrant.includes('Bottom-Right')) return 'bg-yellow-500';
                    return 'bg-gray-500';
                  };
                  const pos = getPosition(comp.quadrant);
                  return (
                    <div
                      key={i}
                      className={`absolute ${getColor(comp.quadrant)} w-3 h-3 rounded-full transform -translate-x-1/2 -translate-y-1/2`}
                      style={{ left: `${pos.left}%`, top: `${pos.top}%` }}
                      title={`${comp.name}: ${comp.quadrant}`}
                    >
                      <span className="absolute top-4 left-1/2 -translate-x-1/2 text-[10px] whitespace-nowrap">{comp.name}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          <div className="bg-secondary/30 rounded-xl p-4">
            <p className="text-sm"><strong>Recommended Position:</strong> {data.competitive_positioning.recommended_position}</p>
            {data.competitive_positioning.quadrant_descriptions && (
              <div className="mt-3">
                <BulletList items={data.competitive_positioning.quadrant_descriptions} />
              </div>
            )}
          </div>
        </div>
      )}

      {/* Differentiation Strategy */}
      {data.differentiation_strategy && (
        <div className="mb-6">
          <h4 className="text-sm font-medium mb-3">Differentiation Strategy</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {data.differentiation_strategy.core_differentiators && (
              <div>
                <h5 className="text-xs font-medium text-primary mb-2">Core Differentiators</h5>
                <BulletList items={data.differentiation_strategy.core_differentiators} />
              </div>
            )}
            {data.differentiation_strategy.sustainable_advantages && (
              <div>
                <h5 className="text-xs font-medium text-green-400 mb-2">Sustainable Advantages</h5>
                <BulletList items={data.differentiation_strategy.sustainable_advantages} />
              </div>
            )}
          </div>
        </div>
      )}

      {/* Indirect Alternatives */}
      {data.indirect_alternatives && (
        <div>
          <h4 className="text-sm font-medium mb-3">Indirect Alternatives</h4>
          <div className="space-y-3">
            {data.indirect_alternatives.map((alt: any, i: number) => (
              <div key={i} className="bg-secondary/30 rounded-xl p-4">
                <h5 className="font-medium text-sm text-primary mb-2">{alt.alternative}</h5>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  <div>
                    <p className="text-xs font-medium text-muted-foreground mb-1">Why Customers Use It</p>
                    <p className="text-sm">{alt.why_customers_use_it}</p>
                  </div>
                  <div>
                    <p className="text-xs font-medium text-muted-foreground mb-1">How to Win Against</p>
                    <p className="text-sm">{alt.how_to_win_against}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </ModuleSection>
  );
}

// Technical Roadmap Module
function TechnicalRoadmapModule({ data }: { data: any }) {
  if (!data) return null;

  return (
    <ModuleSection title="Technical Roadmap" icon={Layers}>

      {/* Technology Stack */}
      {data.technology_stack && (
        <div className="mb-6">
          <h4 className="text-sm font-medium mb-3">Technology Stack</h4>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            {data.technology_stack.frontend && (
              <div className="bg-secondary/30 rounded-xl p-3">
                <p className="text-xs font-semibold text-primary mb-1">Frontend</p>
                <BulletList items={Array.isArray(data.technology_stack.frontend) ? data.technology_stack.frontend : [data.technology_stack.frontend]} />
              </div>
            )}
            {data.technology_stack.backend && (
              <div className="bg-secondary/30 rounded-xl p-3">
                <p className="text-xs font-semibold text-primary mb-1">Backend</p>
                <BulletList items={Array.isArray(data.technology_stack.backend) ? data.technology_stack.backend : [data.technology_stack.backend]} />
              </div>
            )}
            {data.technology_stack.database && (
              <div className="bg-secondary/30 rounded-xl p-3">
                <p className="text-xs font-semibold text-primary mb-1">Database</p>
                <BulletList items={Array.isArray(data.technology_stack.database) ? data.technology_stack.database : [data.technology_stack.database]} />
              </div>
            )}
            {data.technology_stack.infrastructure && (
              <div className="bg-secondary/30 rounded-xl p-3">
                <p className="text-xs font-semibold text-primary mb-1">Infrastructure</p>
                <BulletList items={Array.isArray(data.technology_stack.infrastructure) ? data.technology_stack.infrastructure : [data.technology_stack.infrastructure]} />
              </div>
            )}
            {data.technology_stack.third_party_services && (
              <div className="bg-secondary/30 rounded-xl p-3">
                <p className="text-xs font-semibold text-primary mb-1">3rd Party Services</p>
                <BulletList items={Array.isArray(data.technology_stack.third_party_services) ? data.technology_stack.third_party_services : [data.technology_stack.third_party_services]} />
              </div>
            )}
          </div>
          {data.technology_stack.rationale && (
            <p className="text-xs text-muted-foreground mt-3 italic">{data.technology_stack.rationale}</p>
          )}
        </div>
      )}

      {/* Development Timeline */}
      {data.development_timeline && (
        <div className="mb-6">
          <h4 className="text-sm font-medium mb-3">Development Timeline</h4>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {data.development_timeline.mvp_phase && (
              <div className="bg-secondary/30 rounded-xl p-3">
                <p className="text-xs font-semibold text-primary mb-1">MVP Phase</p>
                <p className="text-xs text-muted-foreground">{data.development_timeline.mvp_phase.duration || data.development_timeline.mvp_phase}</p>
              </div>
            )}
            {data.development_timeline.beta_phase && (
              <div className="bg-secondary/30 rounded-xl p-3">
                <p className="text-xs font-semibold text-primary mb-1">Beta Phase</p>
                <p className="text-xs text-muted-foreground">{data.development_timeline.beta_phase.duration || data.development_timeline.beta_phase}</p>
              </div>
            )}
            {data.development_timeline.launch_phase && (
              <div className="bg-secondary/30 rounded-xl p-3">
                <p className="text-xs font-semibold text-primary mb-1">Launch Phase</p>
                <p className="text-xs text-muted-foreground">{data.development_timeline.launch_phase.duration || data.development_timeline.launch_phase}</p>
              </div>
            )}
            {data.development_timeline.total_time_to_market && (
              <div className="bg-primary/10 border border-primary/20 rounded-xl p-3">
                <p className="text-xs font-semibold text-primary mb-1">Total Time to Market</p>
                <p className="text-sm font-bold">{data.development_timeline.total_time_to_market}</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* MVP Features */}
      {(data.mvp_features || data.MVP_features) && (
        <div className="mb-6">
          <h4 className="text-sm font-medium mb-3">MVP Features</h4>
          <div className="space-y-2">
            {(data.mvp_features || data.MVP_features).map((feat: any, i: number) => (
              <div key={i} className="flex items-start gap-3 bg-secondary/30 rounded-lg p-3">
                <div className="w-6 h-6 rounded bg-primary/20 flex items-center justify-center shrink-0">
                  <span className="text-xs font-bold text-primary">{i + 1}</span>
                </div>
                <div className="flex-1">
                  <p className="text-sm font-medium">{feat.feature || feat.name || feat.title}</p>
                  {feat.priority && <span className={`text-xs px-1.5 py-0.5 rounded ${feat.priority === 'Must Have' ? 'bg-red-500/20 text-red-400' : feat.priority === 'Should Have' ? 'bg-yellow-500/20 text-yellow-400' : 'bg-green-500/20 text-green-400'}`}>{feat.priority}</span>}
                  {feat.description && <p className="text-xs text-muted-foreground mt-1">{feat.description}</p>}
                  {feat.effort && <p className="text-xs text-muted-foreground mt-0.5">Effort: {feat.effort} | Complexity: {feat.complexity}</p>}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Team Composition */}
      {data.team_composition && (
        <div className="mb-6">
          <h4 className="text-sm font-medium mb-3">Team Composition</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {data.team_composition.founding_team && (
              <div className="bg-secondary/30 rounded-xl p-3">
                <p className="text-xs font-semibold text-primary mb-1">Founding Team</p>
                <BulletList items={Array.isArray(data.team_composition.founding_team) ? data.team_composition.founding_team : [data.team_composition.founding_team]} />
              </div>
            )}
            {data.team_composition.early_hires && (
              <div className="bg-secondary/30 rounded-xl p-3">
                <p className="text-xs font-semibold text-primary mb-1">Early Hires</p>
                <BulletList items={Array.isArray(data.team_composition.early_hires) ? data.team_composition.early_hires : [data.team_composition.early_hires]} />
              </div>
            )}
          </div>
        </div>
      )}

      {/* Infrastructure Costs */}
      {data.infrastructure_costs && (
        <div className="mb-6">
          <h4 className="text-sm font-medium mb-3">Infrastructure Costs</h4>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {data.infrastructure_costs.mvp_monthly_cost && <MetricCard label="MVP Monthly" value={data.infrastructure_costs.mvp_monthly_cost} />}
            {data.infrastructure_costs.growth_monthly_cost && <MetricCard label="Growth Monthly" value={data.infrastructure_costs.growth_monthly_cost} />}
            {data.infrastructure_costs.scale_monthly_cost && <MetricCard label="Scale Monthly" value={data.infrastructure_costs.scale_monthly_cost} />}
          </div>
        </div>
      )}

      {/* Scalability Plan */}
      {data.scalability_plan && (
        <div className="mb-6">
          <h4 className="text-sm font-medium mb-3">Scalability Plan</h4>
          {data.scalability_plan.current_capacity && (
            <p className="text-xs text-muted-foreground mb-3">Current capacity: {data.scalability_plan.current_capacity}</p>
          )}
          {Array.isArray(data.scalability_plan.scaling_plan) && (
            <div className="space-y-2">
              {data.scalability_plan.scaling_plan.map((step: any, i: number) => (
                <div key={i} className="flex items-start gap-3 bg-secondary/30 rounded-lg p-3">
                  <div className="w-6 h-6 rounded bg-primary/20 flex items-center justify-center shrink-0">
                    <span className="text-xs font-bold text-primary">{i + 1}</span>
                  </div>
                  <div>
                    <p className="text-xs font-medium">Trigger: {step.trigger}</p>
                    <p className="text-xs text-muted-foreground">{step.action}</p>
                    {step.estimated_effort && <p className="text-xs text-primary">Effort: {step.estimated_effort}</p>}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Security & Compliance */}
      {Array.isArray(data.security_compliance) && data.security_compliance.length > 0 && (
        <div>
          <h4 className="text-sm font-medium mb-3">Security & Compliance</h4>
          <div className="space-y-2">
            {data.security_compliance.map((req: any, i: number) => (
              <div key={i} className="bg-secondary/30 rounded-lg p-3">
                <p className="text-sm font-medium">{req.requirement}</p>
                <p className="text-xs text-muted-foreground mt-1">{req.implementation}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </ModuleSection>
  );
}


// Risk Analysis Module
function RiskAnalysisModule({ data }: { data: any }) {
  if (!data) return null;

  return (
    <ModuleSection title="Risk Assessment & Mitigation" icon={AlertTriangle}>
      <div className="space-y-6">
        {/* Market & Technical Risks */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {data.market_risks && data.market_risks.length > 0 && (
            <div className="bg-orange-500/5 border border-orange-500/10 rounded-xl p-4">
              <h5 className="text-xs font-semibold text-orange-400 mb-3 uppercase tracking-wider">Market Risks</h5>
              <div className="space-y-3">
                {data.market_risks.map((risk: any, i: number) => (
                  <div key={i} className="bg-secondary/30 rounded-lg p-2.5">
                    <div className="flex justify-between items-center mb-1">
                      <span className="text-xs font-bold">{risk.risk_factor}</span>
                      <div className="flex gap-1">
                        <RiskBadge level={risk.impact_level} />
                      </div>
                    </div>
                    <p className="text-[10px] text-muted-foreground">{risk.mitigation_strategy}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
          {data.technical_risks && data.technical_risks.length > 0 && (
            <div className="bg-blue-500/5 border border-blue-500/10 rounded-xl p-4">
              <h5 className="text-xs font-semibold text-blue-400 mb-3 uppercase tracking-wider">Technical Risks</h5>
              <div className="space-y-3">
                {data.technical_risks.map((risk: any, i: number) => (
                  <div key={i} className="bg-secondary/30 rounded-lg p-2.5">
                    <div className="flex justify-between items-center mb-1">
                      <span className="text-xs font-bold">{risk.risk_factor}</span>
                      <div className="flex gap-1">
                        <RiskBadge level={risk.impact_level} />
                      </div>
                    </div>
                    <p className="text-[10px] text-muted-foreground">{risk.mitigation_strategy}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Operational & Financial Risks */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {data.operational_risks && data.operational_risks.length > 0 && (
            <div className="bg-secondary/30 rounded-xl p-4">
              <h5 className="text-xs font-semibold text-primary mb-3 uppercase tracking-wider">Operational Risks</h5>
              <div className="space-y-3">
                {data.operational_risks.map((risk: any, i: number) => (
                  <div key={i} className="bg-secondary/20 rounded-lg p-2.5">
                    <div className="flex justify-between items-center mb-1">
                      <span className="text-xs font-bold">{risk.risk_factor}</span>
                      <RiskBadge level={risk.impact_level} />
                    </div>
                    <p className="text-[10px] text-muted-foreground">{risk.mitigation_strategy}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
          {data.financial_risks && data.financial_risks.length > 0 && (
            <div className="bg-secondary/30 rounded-xl p-4">
              <h5 className="text-xs font-semibold text-primary mb-3 uppercase tracking-wider">Financial Risks</h5>
              <div className="space-y-3">
                {data.financial_risks.map((risk: any, i: number) => (
                  <div key={i} className="bg-secondary/20 rounded-lg p-2.5">
                    <div className="flex justify-between items-center mb-1">
                      <span className="text-xs font-bold">{risk.risk_factor}</span>
                      <RiskBadge level={risk.impact_level} />
                    </div>
                    <p className="text-[10px] text-muted-foreground">{risk.mitigation_strategy}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Contingency Plans */}
        {data.contingency_plans && data.contingency_plans.length > 0 && (
          <div className="bg-red-500/5 border border-red-500/20 rounded-xl p-4">
            <h5 className="text-xs font-semibold text-red-400 mb-3 uppercase tracking-wider">Contingency Plans</h5>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
               {data.contingency_plans.map((plan: any, i: number) => (
                 <div key={i} className="bg-red-500/5 rounded-lg p-3 border border-red-500/10">
                    <p className="text-xs font-bold text-red-400 mb-1">{plan.scenario}</p>
                    <p className="text-[10px] text-muted-foreground">{plan.action_plan}</p>
                 </div>
               ))}
            </div>
          </div>
        )}
      </div>
    </ModuleSection>
  );
}

// Go-to-Market Module
function GTMStrategyModule({ data }: { data: any }) {
  if (!data) return null;

  return (
    <ModuleSection title="Go-to-Market Strategy" icon={Target}>
      {/* Acquisition Channels */}
      {data.acquisition_channels && (
        <div className="mb-6">
          <h4 className="text-sm font-medium mb-3">Acquisition Channels</h4>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-white/10">
                  <th className="text-left py-2 px-3 text-muted-foreground">Channel</th>
                  <th className="text-center py-2 px-3 text-muted-foreground">ROI Rank</th>
                  <th className="text-right py-2 px-3 text-muted-foreground">Est. CAC</th>
                  <th className="text-left py-2 px-3 text-muted-foreground">Strategy</th>
                </tr>
              </thead>
              <tbody>
                {data.acquisition_channels.map((chan: any, i: number) => (
                  <tr key={i} className="border-b border-white/5">
                    <td className="py-2 px-3 font-medium">{chan.channel}</td>
                    <td className="text-center py-2 px-3">
                      <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-primary/20 text-primary text-xs font-bold">
                        {chan.roi_rank}
                      </span>
                    </td>
                    <td className="text-right py-2 px-3 text-green-400">{chan.estimated_cac}</td>
                    <td className="py-2 px-3 text-muted-foreground text-xs">{chan.strategy}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Launch Strategy */}
      {data.launch_strategy && (
        <div className="mb-6">
          <h4 className="text-sm font-medium mb-3">Launch Strategy</h4>
          <div className="space-y-4">
            {data.launch_strategy.week_1_4 && (
              <div className="bg-secondary/30 rounded-xl p-4">
                <h5 className="text-sm font-medium text-primary mb-2">Weeks 1-4</h5>
                <BulletList items={data.launch_strategy.week_1_4} />
              </div>
            )}
            {data.launch_strategy.week_5_8 && (
              <div className="bg-secondary/30 rounded-xl p-4">
                <h5 className="text-sm font-medium text-primary mb-2">Weeks 5-8</h5>
                <BulletList items={data.launch_strategy.week_5_8} />
              </div>
            )}
            {data.launch_strategy.week_9_12 && (
              <div className="bg-secondary/30 rounded-xl p-4">
                <h5 className="text-sm font-medium text-primary mb-2">Weeks 9-12</h5>
                <BulletList items={data.launch_strategy.week_9_12} />
              </div>
            )}
          </div>
        </div>
      )}

      {/* Marketing Budget */}
      {data.marketing_budget && (
        <div className="mb-6">
          <h4 className="text-sm font-medium mb-3">Marketing Budget</h4>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <tbody>
                {data.marketing_budget.total_monthly && (
                  <tr className="border-b border-white/10">
                    <td className="py-2 px-3 font-medium w-1/3">Total Monthly</td>
                    <td className="py-2 px-3 text-green-400">{data.marketing_budget.total_monthly}</td>
                  </tr>
                )}
                {data.marketing_budget.paid_acquisition && (
                  <tr className="border-b border-white/10">
                    <td className="py-2 px-3 font-medium">Paid Acquisition</td>
                    <td className="py-2 px-3 text-muted-foreground">{data.marketing_budget.paid_acquisition}</td>
                  </tr>
                )}
                {data.marketing_budget.content_marketing && (
                  <tr className="border-b border-white/10">
                    <td className="py-2 px-3 font-medium">Content Marketing</td>
                    <td className="py-2 px-3 text-muted-foreground">{data.marketing_budget.content_marketing}</td>
                  </tr>
                )}
                {data.marketing_budget.events_pr && (
                  <tr className="border-b border-white/10">
                    <td className="py-2 px-3 font-medium">Events & PR</td>
                    <td className="py-2 px-3 text-muted-foreground">{data.marketing_budget.events_pr}</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* GTM Phases (legacy support for other data formats) */}
      {data.phases && (
        <div className="mb-6">
          <h4 className="text-sm font-medium mb-3">Launch Phases</h4>
          <div className="space-y-3">
            {data.phases.map((phase: any, i: number) => (
              <div key={i} className="bg-secondary/30 rounded-xl p-4">
                <div className="flex items-center gap-3 mb-2">
                  <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center">
                    <span className="text-xs font-bold">{i + 1}</span>
                  </div>
                  <div>
                    <p className="font-medium">{phase.phase_name}</p>
                    <p className="text-xs text-muted-foreground">{phase.timeline}</p>
                  </div>
                </div>
                <p className="text-sm text-muted-foreground">{phase.objective}</p>
                {phase.key_activities && (
                  <div className="mt-2">
                    <BulletList items={phase.key_activities} />
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Customer Acquisition (legacy support) */}
      {data.customer_acquisition && (
        <div className="mb-6">
          <h4 className="text-sm font-medium mb-3">Customer Acquisition Strategy</h4>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <MetricCard label="Primary Channel" value={data.customer_acquisition.primary_channel || 'N/A'} />
            <MetricCard label="Target CAC" value={data.customer_acquisition.target_cac || 'N/A'} />
            <MetricCard label="Year 1 Target" value={data.customer_acquisition.year_1_customer_target || 'N/A'} />
          </div>
        </div>
      )}

      {/* Channel Strategy (legacy support) */}
      {data.channel_strategy && (
        <div>
          <h4 className="text-sm font-medium mb-3">Channel Strategy</h4>
          <BulletList items={data.channel_strategy} />
        </div>
      )}
    </ModuleSection>
  );
}

// Business Model Canvas Module
function BusinessModelCanvasModule({ data }: { data: any }) {
  if (!data) return null;

  const canvasKeys = [
    'customer_segments', 'value_propositions', 'channels', 'customer_relationships',
    'revenue_streams', 'key_resources', 'key_activities', 'key_partnerships', 'cost_structure'
  ];

  return (
    <ModuleSection title="Business Model Canvas" icon={Building2}>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {canvasKeys.map(key => {
          const items = data[key];
          if (!items || !Array.isArray(items)) return null;

          return (
            <div key={key} className="bg-secondary/30 rounded-xl p-4">
              <h5 className="text-xs font-medium text-primary uppercase tracking-wider mb-2">
                {formatKey(key)}
              </h5>
              <ul className="space-y-1">
                {items.slice(0, 5).map((item: string, i: number) => (
                  <li key={i} className="text-xs text-muted-foreground">• {item}</li>
                ))}
              </ul>
            </div>
          );
        })}
      </div>
    </ModuleSection>
  );
}

// Investor Pitch Deck Module (Premium)
function InvestorPitchDeckModule({ data }: { data: any }) {
  if (!data) return null;

  return (
    <ModuleSection title="Investor Pitch Deck" icon={Briefcase}>
      {data.slides && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {data.slides.map((slide: any, i: number) => (
            <div key={i} className="bg-secondary/30 rounded-xl p-4">
              <div className="flex items-center gap-2 mb-2">
                <div className="w-6 h-6 rounded bg-primary/20 flex items-center justify-center">
                  <span className="text-xs font-bold text-primary">{i + 1}</span>
                </div>
                <h5 className="text-sm font-medium">{slide.slide_title}</h5>
              </div>
              <p className="text-xs text-muted-foreground">{slide.key_message}</p>
              {slide.talking_points && (
                <div className="mt-2">
                  <BulletList items={slide.talking_points.slice(0, 2)} />
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {data.ask && (
        <div className="mt-6 bg-primary/10 border border-primary/30 rounded-xl p-4">
          <h5 className="text-sm font-medium text-primary mb-2">The Ask</h5>
          <p className="text-lg font-bold">{data.ask.amount}</p>
          <p className="text-sm text-muted-foreground">{data.ask.use_of_funds}</p>
        </div>
      )}
    </ModuleSection>
  );
}

const premiumSections = [
  { name: 'Business Model Canvas', tier: 'Basic+' },
  { name: 'Market Analysis', tier: 'Standard+' },
  { name: 'Competitive Intelligence', tier: 'Standard+' },
  { name: 'Financial Projections', tier: 'Standard+' },
  { name: 'Technical Roadmap', tier: 'Standard+' },
  { name: 'Go-to-Market Strategy', tier: 'Premium' },
  { name: 'Investor Pitch Deck', tier: 'Premium' },
  { name: 'Risk Analysis', tier: 'Standard+' },
];

export default function Report() {
  const { threadId } = useParams<{ threadId: string }>();
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  const tier = searchParams.get('tier') || 'free';
  const isPreview = searchParams.get('preview') === 'true';

  const [report, setReport] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [editMode, setEditMode] = useState<'visual' | 'json'>('visual');
  const [editedData, setEditedData] = useState<any>(null);
  const [saving, setSaving] = useState(false);
  const [approving, setApproving] = useState(false);
  const [isDownloading, setIsDownloading] = useState(false);
  const [jsonError, setJsonError] = useState<string | null>(null);

  const handleDownloadPDF = async () => {
    setIsDownloading(true);
    try {
      const response = await fetch(`${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/generate-html`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          tier: tier,
          title: report?.report_data?.title || 'Report',
          report_data: report?.report_data
        })
      });
      
      if (!response.ok) throw new Error('Failed to generate PDF');
      
      const htmlString = await response.text();
      
      // Create a hidden iframe, inject the HTML, and print it
      const iframe = document.createElement('iframe');
      iframe.style.visibility = 'hidden';
      iframe.style.position = 'absolute';
      iframe.style.width = '0';
      iframe.style.height = '0';
      iframe.style.border = 'none';
      document.body.appendChild(iframe);
      
      const iframeDoc = iframe.contentWindow?.document;
      if (iframeDoc) {
        iframeDoc.open();
        iframeDoc.write(htmlString);
        iframeDoc.close();
        
        // Wait for iframe resources (like charts) to load
        setTimeout(() => {
          iframe.contentWindow?.focus();
          iframe.contentWindow?.print();
          
          // Cleanup
          setTimeout(() => {
            document.body.removeChild(iframe);
          }, 1000);
        }, 1500);
      }
    } catch (error) {
      console.error('Error generating PDF:', error);
      alert('Failed to generate PDF. Please try again.');
    } finally {
      setIsDownloading(false);
    }
  };

  useEffect(() => {
    async function load() {
      try {
        const data = await getReport(threadId || '', tier);
        setReport(data);
        setEditedData(data.report_data);
      } catch (err) {
        console.error('Failed to load report', err);
        setLoadError('The report is still being generated or could not be loaded. Please try refreshing the page in a moment.');
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [threadId, tier]);

  const handleSave = async () => {
    if (!threadId) return;
    setSaving(true);
    try {
      let finalData = editedData;
      if (editMode === 'json') {
        try {
          finalData = JSON.parse(editedData);
        } catch (e) {
          setJsonError('Invalid JSON format');
          setSaving(false);
          return;
        }
      }
      await adminSave(threadId, finalData);
      setReport({ ...report, report_data: finalData });
      setIsEditing(false);
      setJsonError(null);
    } catch (err) {
      console.error('Save failed:', err);
      alert('Failed to save changes');
    } finally {
      setSaving(false);
    }
  };

  const handleApprove = async () => {
    if (!threadId) return;
    if (confirm('Are you sure you want to approve and release this report to the user?')) {
      setApproving(true);
      try {
        await adminApprove(threadId, editedData);
        navigate('/admin');
      } catch (err) {
        console.error('Approval failed:', err);
        alert('Failed to approve report');
      } finally {
        setApproving(false);
      }
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <Brain className="w-12 h-12 text-primary mx-auto mb-4 animate-pulse" />
          <p className="text-muted-foreground">Loading your report...</p>
        </div>
      </div>
    );
  }

  if (loadError || !report) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center max-w-md">
          <AlertTriangle className="w-12 h-12 text-amber-400 mx-auto mb-4" />
          <h2 className="text-xl font-bold mb-2">Report Not Ready Yet</h2>
          <p className="text-muted-foreground mb-6">{loadError || 'Your report could not be loaded. It may still be processing.'}</p>
          <button
            onClick={() => window.location.reload()}
            className="px-6 py-2 rounded-lg bg-primary text-primary-foreground text-sm font-semibold hover:bg-primary/90 transition-all"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  const rd = isEditing && editMode === 'visual' ? editedData : report.report_data;

  // Get modules if available
  const modules = rd?.modules || {};

  return (
    <div className="min-h-screen relative">
      <FloatingOrbs />
      <Navbar />

      {/* Admin Toolbar */}
      <AnimatePresence>
        {isPreview && (
          <motion.div
            initial={{ y: -100 }}
            animate={{ y: 0 }}
            className="fixed top-0 left-0 right-0 z-[60] glass border-b border-primary/20 p-3 flex items-center justify-center gap-4"
          >
            {!isEditing ? (
              <>
                <div className="flex items-center gap-2 text-xs font-semibold text-amber-500 uppercase tracking-widest px-3 py-1 bg-amber-500/10 border border-amber-500/20 rounded-full">
                  <Shield className="w-3 h-3" />
                  Researcher Review Mode
                </div>
                <button
                  onClick={() => setIsEditing(true)}
                  className="px-4 py-1.5 rounded-lg bg-secondary hover:bg-secondary/80 text-sm font-medium flex items-center gap-2 transition-all"
                >
                  <Edit3 className="w-4 h-4" />
                  Edit Report
                </button>
                <button
                  onClick={handleApprove}
                  disabled={approving}
                  className="px-4 py-1.5 rounded-lg bg-primary text-primary-foreground text-sm font-bold flex items-center gap-2 transition-all hover:scale-105"
                >
                  {approving ? <Zap className="w-4 h-4 animate-spin" /> : <CheckCircle className="w-4 h-4" />}
                  Approve & Release
                </button>
              </>
            ) : (
              <>
                <div className="flex bg-secondary/50 p-1 rounded-lg">
                  <button
                    onClick={() => setEditMode('visual')}
                    className={`px-3 py-1 rounded-md text-xs font-medium flex items-center gap-1.5 transition-all ${editMode === 'visual' ? 'bg-primary text-primary-foreground' : 'text-muted-foreground hover:text-white'}`}
                  >
                    <Eye className="w-3.5 h-3.5" />
                    Visual
                  </button>
                  <button
                    onClick={() => {
                      setEditMode('json');
                      setEditedData(JSON.stringify(editedData, null, 2));
                    }}
                    className={`px-3 py-1 rounded-md text-xs font-medium flex items-center gap-1.5 transition-all ${editMode === 'json' ? 'bg-primary text-primary-foreground' : 'text-muted-foreground hover:text-white'}`}
                  >
                    <Code className="w-3.5 h-3.5" />
                    JSON
                  </button>
                </div>
                <div className="h-6 w-px bg-white/10 mx-2" />
                <button
                  onClick={handleSave}
                  disabled={saving}
                  className="px-4 py-1.5 rounded-lg bg-green-600 text-white text-sm font-bold flex items-center gap-2 transition-all hover:bg-green-500"
                >
                  {saving ? <Zap className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                  Save Changes
                </button>
                <button
                  onClick={() => {
                    setIsEditing(false);
                    setEditedData(report.report_data);
                    setJsonError(null);
                  }}
                  className="px-4 py-1.5 rounded-lg bg-red-600/20 text-red-400 hover:bg-red-600/30 text-sm font-medium flex items-center gap-2 transition-all"
                >
                  <X className="w-4 h-4" />
                  Cancel
                </button>
              </>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      <div className={`pt-28 pb-10 ${isPreview ? 'mt-12' : ''}`}>
        <div className="container mx-auto px-6 max-w-5xl">

          {/* JSON EDITOR OVERLAY */}
          {isEditing && editMode === 'json' ? (
            <div className="glass rounded-2xl p-6 min-h-[600px] flex flex-col">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-bold flex items-center gap-2">
                  <Code className="w-5 h-5 text-primary" />
                  Raw JSON Research Data
                </h3>
                {jsonError && <span className="text-red-400 text-sm flex items-center gap-1"><AlertTriangle className="w-4 h-4" /> {jsonError}</span>}
              </div>
              <textarea
                value={editedData}
                onChange={(e) => {
                  setEditedData(e.target.value);
                  setJsonError(null);
                }}
                className="flex-1 w-full bg-black/40 border border-white/10 rounded-xl p-4 font-mono text-sm text-green-400 focus:outline-none focus:ring-1 focus:ring-primary/50 min-h-[500px]"
                spellCheck={false}
              />
            </div>
          ) : (
            <>
              {/* Report Version Switcher (Multi-tier History) */}
              {report.available_tiers && report.available_tiers.length > 1 && (
                <div className="flex flex-wrap items-center gap-2 mb-8 bg-secondary/20 p-2 rounded-xl border border-white/5">
                  <span className="text-xs font-semibold text-muted-foreground px-3 uppercase tracking-wider">Report Versions:</span>
                  {['free', 'basic', 'standard', 'premium'].map(t => {
                    if (!report.available_tiers.includes(t)) return null;
                    return (
                      <button
                        key={t}
                        onClick={() => {
                          setLoading(true);
                          getReport(threadId!, t)
                            .then(data => {
                              setReport(data);
                              setEditedData(data.report_data);
                              setSearchParams({ tier: t });
                            })
                            .catch(err => console.error(err))
                            .finally(() => setLoading(false));
                        }}
                        className={`px-4 py-1.5 rounded-lg text-xs font-bold transition-all uppercase tracking-wide ${
                          report.tier === t 
                            ? 'bg-primary text-primary-foreground shadow-lg shadow-primary/20 scale-105' 
                            : 'glass hover:bg-white/10 text-muted-foreground'
                        }`}
                      >
                        {t}
                      </button>
                    );
                  })}
                </div>
              )}

              {/* Header */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="text-center mb-10"
              >
                <div className="flex items-center justify-center gap-4 mb-4">
                  <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full glass text-xs text-muted-foreground">
                    <BarChart3 className="w-3 h-3 text-primary" />
                    Validation Report
                  </div>
                  <button
                    onClick={handleDownloadPDF}
                    disabled={isDownloading}
                    className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary/20 hover:bg-primary/30 text-primary text-xs font-semibold transition-all"
                  >
                    {isDownloading ? <Zap className="w-3 h-3 animate-spin" /> : <Download className="w-3 h-3" />}
                    Download PDF
                  </button>
                  {tier !== 'premium' && (
                    <Link
                      to={`/upgrade/${threadId}`}
                      className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-accent/20 hover:bg-accent/30 text-accent text-xs font-semibold transition-all"
                    >
                      <Star className="w-3 h-3" />
                      Upgrade Report
                    </Link>
                  )}
                </div>
                {isEditing ? (
                  <input
                    type="text"
                    value={rd?.title || ''}
                    onChange={(e) => setEditedData({ ...rd, title: e.target.value })}
                    className="text-3xl md:text-4xl font-bold mb-2 bg-transparent border-b border-primary/30 text-center w-full focus:outline-none focus:border-primary"
                  />
                ) : (
                  <h1 className="text-3xl md:text-4xl font-bold mb-2">{rd?.title}</h1>
                )}
                <p className="text-sm text-muted-foreground">Thread: {report.thread_id?.slice(0, 8)}...</p>
              </motion.div>

          {/* Viability / Go-No-Go Score */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="glass rounded-2xl p-8 text-center mb-8 relative"
          >
            <h2 className="text-sm font-medium text-muted-foreground mb-4">
              {rd?.viability_score !== undefined ? 'Viability Score' : 'Go/No-Go Score'}
            </h2>
            
            <div className="relative group">
              <AnimatedScore value={rd?.go_no_go_score || rd?.viability_score || 0} max={100} />
              {isEditing && (
                <div className="absolute top-0 right-0 flex flex-col gap-2">
                   <label className="text-[10px] text-muted-foreground uppercase">Score</label>
                   <input 
                    type="number" 
                    value={rd?.go_no_go_score || rd?.viability_score || 0} 
                    onChange={(e) => setEditedData({ ...rd, 'go_no_go_score': parseInt(e.target.value) })}
                    className="w-16 bg-secondary rounded border border-white/10 px-2 py-1 text-center font-bold"
                   />
                </div>
              )}
            </div>

            <div className={`mt-4 inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-medium ${getScoreBgClass(rd?.go_no_go_score || rd?.viability_score)}`}>
              <span className={getScoreColorClass(rd?.go_no_go_score || rd?.viability_score)}>
                {rd?.executive_summary?.recommendation?.go_no_go_verdict || rd?.gauge_status || 'Analyzed'}
              </span>
            </div>
          </motion.div>

          {/* Score Breakdown */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="mb-8"
          >
            <h2 className="text-xl font-bold mb-4">Score Breakdown</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                  {Object.entries(rd?.scores || rd?.score_breakdown || {}).map(([key, val]: [string, any]) => {
                    const Icon = dimensionIcons[key] || BarChart3;
                    const label = dimensionLabels[key] || formatKey(key);
                    const score = typeof val === 'object' ? val.score : val;
                    const reasoning = typeof val === 'object' ? val.reasoning : null;

                    return (
                      <div key={key} className="glass rounded-xl p-5 hover:bg-secondary/30 transition-all relative">
                        <div className="flex items-center gap-3 mb-3">
                          <div className="w-8 h-8 rounded-lg bg-secondary flex items-center justify-center">
                            <Icon className="w-4 h-4 text-primary" />
                          </div>
                          <span className="text-sm font-medium">{label}</span>
                        </div>
                        <div className="flex items-end gap-2 mb-2">
                          {isEditing ? (
                            <input 
                              type="number" 
                              value={score} 
                              onChange={(e) => {
                                const newScores = { ... (rd.scores || rd.score_breakdown) };
                                if (typeof val === 'object') {
                                  newScores[key] = { ...val, score: parseInt(e.target.value) };
                                } else {
                                  newScores[key] = parseInt(e.target.value);
                                }
                                setEditedData({ ...rd, [rd.scores ? 'scores' : 'score_breakdown']: newScores });
                              }}
                              className={`w-12 bg-secondary rounded border border-white/10 px-1 font-bold font-mono ${getScoreColorClass(score, 10)}`}
                            />
                          ) : (
                            <span className={`text-2xl font-bold font-mono ${getScoreColorClass(score, 10)}`}>
                              {score}
                            </span>
                          )}
                          <span className="text-xs text-muted-foreground mb-1">/ 10</span>
                        </div>
                        <div className="h-1.5 rounded-full bg-secondary overflow-hidden mb-2">
                          <div
                            className="h-full rounded-full bg-primary transition-all duration-1000"
                            style={{ width: `${(score / 10) * 100}%` }}
                          />
                        </div>
                        {isEditing && typeof val === 'object' ? (
                          <textarea 
                            value={reasoning || ''} 
                            onChange={(e) => {
                                const newScores = { ... (rd.scores || rd.score_breakdown) };
                                newScores[key] = { ...val, reasoning: e.target.value };
                                setEditedData({ ...rd, [rd.scores ? 'scores' : 'score_breakdown']: newScores });
                            }}
                            className="w-full bg-secondary/50 text-[10px] text-muted-foreground rounded p-1 h-16 resize-none focus:outline-none"
                          />
                        ) : (
                          reasoning && <p className="text-xs text-muted-foreground line-clamp-3">{reasoning}</p>
                        )}
                      </div>
                    );
                  })}
            </div>
          </motion.div>

          {/* Executive Summary */}
          {rd?.executive_summary && (
            <ModuleSection title="Executive Summary" icon={Briefcase} defaultOpen={true}>
              {rd.executive_summary.problem_summary && (
                <div className="mb-4">
                  <h4 className="text-sm font-medium text-primary mb-1">Problem Summary</h4>
                  {isEditing ? (
                    <textarea 
                      value={rd.executive_summary.problem_summary || ''} 
                      onChange={(e) => {
                        const newES = { ...rd.executive_summary, problem_summary: e.target.value };
                        setEditedData({ ...rd, executive_summary: newES });
                      }}
                      className="w-full bg-secondary/50 text-sm text-muted-foreground rounded p-3 h-32 resize-none focus:outline-none"
                    />
                  ) : (
                    <p className="text-sm text-muted-foreground leading-relaxed">{rd.executive_summary.problem_summary}</p>
                  )}
                </div>
              )}
              {rd.executive_summary.proposed_solution && (
                <div className="mb-4">
                  <h4 className="text-sm font-medium text-accent mb-1">Proposed Solution</h4>
                  {isEditing ? (
                    <textarea 
                      value={rd.executive_summary.proposed_solution || ''} 
                      onChange={(e) => {
                        const newES = { ...rd.executive_summary, proposed_solution: e.target.value };
                        setEditedData({ ...rd, executive_summary: newES });
                      }}
                      className="w-full bg-secondary/50 text-sm text-muted-foreground rounded p-3 h-32 resize-none focus:outline-none"
                    />
                  ) : (
                    <p className="text-sm text-muted-foreground leading-relaxed">{rd.executive_summary.proposed_solution}</p>
                  )}
                </div>
              )}
              {/* ... (Highlights and Recommendation followed by similar editing logic) ... */}
              {rd.executive_summary.recommendation && (
                <div className="glass rounded-lg p-4 ring-1 ring-primary/20">
                  <h4 className="text-sm font-medium mb-2">
                    Verdict: <span className={getScoreColorClass(rd?.go_no_go_score)}>{rd.executive_summary.recommendation.go_no_go_verdict}</span>
                  </h4>
                  {isEditing ? (
                    <textarea 
                      value={rd.executive_summary.recommendation.rating_justification || ''} 
                      onChange={(e) => {
                        const newRec = { ...rd.executive_summary.recommendation, rating_justification: e.target.value };
                        const newES = { ...rd.executive_summary, recommendation: newRec };
                        setEditedData({ ...rd, executive_summary: newES });
                      }}
                      className="w-full bg-secondary/50 text-xs text-muted-foreground rounded p-3 h-32 resize-none focus:outline-none"
                    />
                  ) : (
                    <p className="text-xs text-muted-foreground mb-3">{rd.executive_summary.recommendation.rating_justification}</p>
                  )}
                </div>
              )}
            </ModuleSection>
          )}
          
          {/* Free Tier Details */}
          {rd?.value_proposition && (
            <ModuleSection title="Viability Analysis" icon={Brain} defaultOpen={true}>
              <div className="space-y-6">
                <div>
                  <h4 className="text-sm font-medium text-primary mb-1">Killer Value Proposition</h4>
                  {isEditing ? (
                    <textarea 
                      value={rd.value_proposition || ''} 
                      onChange={(e) => setEditedData({ ...rd, value_proposition: e.target.value })}
                      className="w-full bg-secondary/50 text-sm text-muted-foreground rounded p-3 h-20 resize-none focus:outline-none"
                    />
                  ) : (
                    <p className="text-sm text-muted-foreground leading-relaxed">{rd.value_proposition}</p>
                  )}
                </div>
                <div>
                  <h4 className="text-sm font-medium text-primary mb-1">Ideal Customer Profile</h4>
                  {isEditing ? (
                    <textarea 
                      value={rd.customer_profile || ''} 
                      onChange={(e) => setEditedData({ ...rd, customer_profile: e.target.value })}
                      className="w-full bg-secondary/50 text-sm text-muted-foreground rounded p-3 h-24 resize-none focus:outline-none"
                    />
                  ) : (
                    <p className="text-sm text-muted-foreground leading-relaxed">{rd.customer_profile}</p>
                  )}
                </div>
                <div>
                  <h4 className="text-sm font-medium text-primary mb-1">What-If / Pivot Scenario</h4>
                  {isEditing ? (
                    <textarea 
                      value={rd.what_if_scenario || ''} 
                      onChange={(e) => setEditedData({ ...rd, what_if_scenario: e.target.value })}
                      className="w-full bg-secondary/50 text-sm text-muted-foreground rounded p-3 h-24 resize-none focus:outline-none"
                    />
                  ) : (
                    <p className="text-sm text-muted-foreground leading-relaxed">{rd.what_if_scenario}</p>
                  )}
                </div>
                <div>
                  <h4 className="text-sm font-medium text-primary mb-1">Recommended Next Step</h4>
                  {isEditing ? (
                    <textarea 
                      value={rd.personalized_next_step || ''} 
                      onChange={(e) => setEditedData({ ...rd, personalized_next_step: e.target.value })}
                      className="w-full bg-secondary/50 text-sm text-muted-foreground rounded p-3 h-20 resize-none focus:outline-none"
                    />
                  ) : (
                    <p className="text-sm text-muted-foreground leading-relaxed">{rd.personalized_next_step}</p>
                  )}
                </div>
              </div>
            </ModuleSection>
          )}

          {/* Business Model Canvas */}
          {(rd?.business_model_canvas || modules.business_model_canvas) && (
            <BusinessModelCanvasModule data={rd?.business_model_canvas || modules.business_model_canvas} />
          )}

          <MarketAnalysisModule data={modules.market_analysis} />
          <FinancialsModule data={modules.financial_feasibility || modules.financials} />
          <CompetitiveIntelligenceModule data={modules.competitive_intelligence} />
          <TechnicalRoadmapModule data={modules.technical_requirements || modules.technical_roadmap} />
          <GTMStrategyModule data={modules.gtm_strategy || modules.go_to_market_strategy} />
          <RiskAnalysisModule data={modules.risks || modules.risk_analysis} />

          {/* Regulatory Compliance */}
          {modules.regulatory && (
            <ModuleSection title="Regulatory Compliance" icon={Shield}>
              <div className="space-y-6">
                {/* Data Privacy */}
                {modules.regulatory.data_privacy_compliance && (
                  <div className="bg-secondary/30 rounded-xl p-4">
                    <h4 className="text-sm font-medium text-primary mb-2 flex items-center gap-2">
                      <Lock className="w-4 h-4" /> Data Privacy: {modules.regulatory.data_privacy_compliance.applicable_regulation}
                    </h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <p className="text-xs font-semibold mb-1">Data Categories</p>
                        <BulletList items={modules.regulatory.data_privacy_compliance.data_categories} />
                      </div>
                      <div>
                        <p className="text-xs font-semibold mb-1">Legal Basis</p>
                        <p className="text-xs text-muted-foreground">{modules.regulatory.data_privacy_compliance.legal_basis}</p>
                      </div>
                    </div>
                  </div>
                )}

                {/* Country & Industry Regulations */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {modules.regulatory.country_regulations && modules.regulatory.country_regulations.length > 0 && (
                    <div>
                      <h5 className="text-xs font-semibold mb-2">Country Specific</h5>
                      <div className="space-y-2">
                        {modules.regulatory.country_regulations.map((req: any, i: number) => (
                          <div key={i} className="bg-secondary/20 rounded-lg p-2">
                            <p className="text-xs font-medium">{req.regulation || req.requirement}</p>
                            <p className="text-[10px] text-muted-foreground">{req.action_required || req.implementation}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  {modules.regulatory.industry_compliance && modules.regulatory.industry_compliance.length > 0 && (
                    <div>
                      <h5 className="text-xs font-semibold mb-2">Industry Specific</h5>
                      <div className="space-y-2">
                        {modules.regulatory.industry_compliance.map((req: any, i: number) => (
                          <div key={i} className="bg-secondary/20 rounded-lg p-2">
                            <p className="text-xs font-medium">{req.regulation || req.requirement}</p>
                            <p className="text-[10px] text-muted-foreground">{req.action_required || req.implementation}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                {/* IP & Permits */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {modules.regulatory.intellectual_property && modules.regulatory.intellectual_property.length > 0 && (
                    <div className="bg-secondary/30 rounded-xl p-4">
                      <h5 className="text-xs font-semibold mb-2">Intellectual Property</h5>
                      <BulletList items={modules.regulatory.intellectual_property} />
                    </div>
                  )}
                  {modules.regulatory.licensing_permits && modules.regulatory.licensing_permits.length > 0 && (
                    <div className="bg-secondary/30 rounded-xl p-4">
                      <h5 className="text-xs font-semibold mb-2">Licensing & Permits</h5>
                      <BulletList items={modules.regulatory.licensing_permits} />
                    </div>
                  )}
                </div>

                {/* Costs & Policies */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                   {modules.regulatory.compliance_costs && (
                     <div className="bg-primary/5 border border-primary/20 rounded-xl p-3">
                        <p className="text-[10px] font-semibold text-primary mb-1">Compliance Costs</p>
                        <p className="text-xs font-bold">{modules.regulatory.compliance_costs.setup_costs || 'Varies'}</p>
                        <p className="text-[9px] text-muted-foreground">Ongoing: {modules.regulatory.compliance_costs.ongoing_costs || 'N/A'}</p>
                     </div>
                   )}
                   {modules.regulatory.terms_of_service_requirements && (
                     <div className="bg-secondary/30 rounded-xl p-3 col-span-2">
                        <p className="text-[10px] font-semibold mb-1">ToS & Privacy Requirements</p>
                        <BulletList items={[...(modules.regulatory.terms_of_service_requirements || []), ...(modules.regulatory.privacy_policy_requirements || [])].slice(0, 4)} />
                     </div>
                   )}
                </div>
              </div>
            </ModuleSection>
          )}

          {/* Funding Strategy */}
          {modules.funding && (
            <ModuleSection title="Funding Strategy" icon={DollarSign}>
              <div className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                   <div className="bg-primary/10 border border-primary/20 rounded-xl p-5">
                      <h4 className="text-xs font-semibold text-primary mb-2 uppercase tracking-wider">Capital Requirements</h4>
                      <p className="text-xl font-bold mb-2">{modules.funding.funding_requirements}</p>
                      <p className="text-xs text-muted-foreground italic">Target for next 12-18 months</p>
                   </div>
                   <div className="bg-secondary/30 rounded-xl p-5">
                      <h4 className="text-xs font-semibold mb-3 uppercase tracking-wider">Suggested Sources</h4>
                      <BulletList items={modules.funding.suggested_funding_sources} />
                   </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                   <div className="bg-secondary/30 rounded-xl p-4">
                      <h4 className="text-xs font-semibold mb-2 flex items-center gap-2">
                        <Users className="w-3.5 h-3.5 text-primary" /> Investor Profile
                      </h4>
                      <p className="text-xs text-muted-foreground leading-relaxed">{modules.funding.investor_profile}</p>
                   </div>
                   <div className="bg-secondary/30 rounded-xl p-4">
                      <h4 className="text-xs font-semibold mb-2 flex items-center gap-2">
                        <TrendingUp className="w-3.5 h-3.5 text-primary" /> Exit Strategy
                      </h4>
                      <p className="text-xs text-muted-foreground leading-relaxed">{modules.funding.exit_strategy}</p>
                   </div>
                </div>
              </div>
            </ModuleSection>
          )}

          {/* Implementation Roadmap */}
          {modules.roadmap && (
            <ModuleSection title="Implementation Roadmap" icon={Target}>
              <div className="space-y-6">
                {/* Phases */}
                {modules.roadmap.phases && (
                  <div className="space-y-3">
                    {modules.roadmap.phases.map((phase: any, i: number) => (
                      <div key={i} className="flex items-start gap-4 bg-secondary/30 rounded-xl p-4 border border-secondary">
                        <div className="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center shrink-0 border border-primary/30">
                          <span className="text-sm font-bold text-primary">{i + 1}</span>
                        </div>
                        <div className="flex-1">
                          <div className="flex justify-between items-center mb-1">
                            <h5 className="text-sm font-bold">{phase.phase_name}</h5>
                            <span className="text-[10px] bg-primary/20 text-primary px-2 py-0.5 rounded-full font-semibold">{phase.duration}</span>
                          </div>
                          <p className="text-xs text-muted-foreground mb-2">{phase.description}</p>
                          <div className="flex flex-wrap gap-1.5">
                            {Array.isArray(phase.key_milestones) && phase.key_milestones.map((m: string, j: number) => (
                              <span key={j} className="text-[9px] bg-secondary/50 px-2 py-0.5 rounded border border-white/5">{m}</span>
                            ))}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {/* Goals & Vision */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="bg-secondary/30 rounded-xl p-4">
                    <h5 className="text-xs font-semibold text-primary mb-3 uppercase tracking-wider">Short-Term Goals (0-3 Months)</h5>
                    <BulletList items={modules.roadmap.short_term_goals} />
                  </div>
                  <div className="bg-secondary/30 rounded-xl p-4">
                    <h5 className="text-xs font-semibold text-primary mb-3 uppercase tracking-wider">Long-Term Vision (3-5 Years)</h5>
                    <p className="text-xs text-muted-foreground leading-relaxed italic">"{modules.roadmap.long_term_vision}"</p>
                  </div>
                </div>

                {/* Roadmap Risks */}
                {modules.roadmap.key_risks && (
                  <div className="bg-red-500/5 border border-red-500/10 rounded-xl p-4">
                    <h5 className="text-xs font-semibold text-red-400 mb-2">Execution Risks & Blockers</h5>
                    <BulletList items={modules.roadmap.key_risks} />
                  </div>
                )}
              </div>
            </ModuleSection>
          )}


          {/* Investor Pitch Deck */}
          {modules.investor_pitch_deck && (
            <InvestorPitchDeckModule data={modules.investor_pitch_deck} />
          )}

          {/* Upgrade Call to Action for Free Tier */}
          {tier === 'free' && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5 }}
              className="mt-16 mb-12 p-10 glass rounded-3xl text-center relative overflow-hidden"
            >
              <div className="absolute top-0 right-0 p-4 opacity-10">
                <Star className="w-24 h-24 text-accent" />
              </div>
              
              <h2 className="text-3xl font-bold mb-4">
                Unlock <span className="gradient-text">Advanced Research</span>
              </h2>
              <p className="text-muted-foreground max-w-xl mx-auto mb-10">
                Your free viability assessment is just the beginning. Upgrade to generate a comprehensive 50-page academic validation report with market intelligence, financial models, and an investor-ready pitch deck.
              </p>

              <div className="grid md:grid-cols-3 gap-6 mb-10">
                {[
                  { name: 'Basic', desc: 'Core business model validation', icon: Briefcase },
                  { name: 'Standard', desc: 'In-depth market & competition', icon: BarChart3 },
                  { name: 'Premium', desc: 'Investor-ready validation suite', icon: Star }
                ].map((t) => (
                  <div key={t.name} className="glass p-5 rounded-2xl flex flex-col items-center text-center">
                    <div className="w-10 h-10 rounded-xl bg-secondary flex items-center justify-center mb-3">
                      <t.icon className="w-5 h-5 text-primary" />
                    </div>
                    <h3 className="font-bold mb-1">{t.name}</h3>
                    <p className="text-xs text-muted-foreground leading-relaxed">{t.desc}</p>
                  </div>
                ))}
              </div>

              <Link
                to={`/upgrade/${threadId}`}
                className="inline-flex items-center gap-3 px-8 py-4 rounded-xl bg-primary text-primary-foreground font-bold text-lg hover:bg-primary/90 transition-all glow-pulse group"
              >
                Explore Upgrade Options
                <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
              </Link>
            </motion.div>
          )}
        </>
      )}
    </div>
  </div>

      <Footer />
    </div>
  );
}
