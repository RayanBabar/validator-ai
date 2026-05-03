import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Brain, Clock, ChevronRight, FileText, LayoutDashboard, History } from 'lucide-react';
import { Navbar } from "@/components/Navbar";
import { Footer } from "@/components/Footer";
import { FloatingOrbs } from "@/components/FloatingOrbs";
import { supabase } from "@/lib/supabase";
import { Link } from 'react-router-dom';

interface Session {
  thread_id: string;
  description: string;
  status: string;
  tier: string;
  created_at: string;
}

export default function Dashboard() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchSessions() {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) return;

      const { data, error } = await supabase
        .from('validation_sessions')
        .select('*')
        .eq('user_id', user.id)
        .order('created_at', { ascending: false });

      if (error) {
        console.error('Error fetching sessions:', error);
      } else {
        setSessions(data || []);
      }
      setLoading(false);
    }

    fetchSessions();
  }, []);

  return (
    <div className="min-h-screen relative">
      <FloatingOrbs />
      <Navbar />
      
      <div className="pt-28 pb-10 container mx-auto px-6 max-w-5xl">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold flex items-center gap-3">
              <LayoutDashboard className="w-8 h-8 text-primary" />
              Research Dashboard
            </h1>
            <p className="text-muted-foreground mt-1">Manage and track your academic validation projects</p>
          </div>
          <Link 
            to="/submit" 
            className="px-6 py-2.5 rounded-lg bg-primary text-primary-foreground font-semibold hover:bg-primary/90 transition-all flex items-center gap-2"
          >
            <Brain className="w-4 h-4" />
            New Research
          </Link>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-20">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          </div>
        ) : sessions.length === 0 ? (
          <div className="glass rounded-2xl p-12 text-center">
            <div className="w-16 h-16 bg-secondary rounded-full flex items-center justify-center mx-auto mb-4">
              <History className="w-8 h-8 text-muted-foreground" />
            </div>
            <h3 className="text-xl font-semibold mb-2">No research sessions yet</h3>
            <p className="text-muted-foreground mb-6">Start your first startup validation to see it here.</p>
            <Link 
              to="/submit" 
              className="inline-flex items-center gap-2 text-primary hover:underline font-medium"
            >
              Start new validation <ChevronRight className="w-4 h-4" />
            </Link>
          </div>
        ) : (
          <div className="grid gap-4">
            {sessions.map((session) => (
              <motion.div
                key={session.thread_id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="glass rounded-xl p-6 hover:border-primary/30 transition-all group"
              >
                <div className="flex items-center justify-between gap-6">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-3 mb-2">
                      <span className={`px-2 py-0.5 rounded-md text-[10px] font-bold uppercase tracking-wider ${
                        session.tier === 'premium' ? 'bg-primary/20 text-primary border border-primary/30' :
                        session.tier === 'standard' ? 'bg-accent/20 text-accent border border-accent/30' :
                        'bg-secondary text-muted-foreground border border-border'
                      }`}>
                        {session.tier} Research
                      </span>
                      <span className="text-xs text-muted-foreground flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {new Date(session.created_at).toLocaleDateString()}
                      </span>
                    </div>
                    <h3 className="text-lg font-semibold truncate group-hover:text-primary transition-colors">
                      {session.description}
                    </h3>
                  </div>

                  <div className="flex items-center gap-4">
                    <div className="text-right hidden sm:block">
                      <span className={`text-xs px-2 py-1 rounded-full ${
                        session.status === 'report_ready' ? 'bg-green-500/10 text-green-500' :
                        session.status === 'waiting_for_admin_approval' ? 'bg-amber-500/10 text-amber-500' :
                        'bg-blue-500/10 text-blue-500'
                      }`}>
                        {session.status.replace(/_/g, ' ')}
                      </span>
                    </div>
                    
                    <Link
                      to={session.status === 'report_ready' ? `/report/${session.thread_id}?tier=${session.tier}` : `/processing/${session.thread_id}`}
                      className="p-2 rounded-lg bg-secondary hover:bg-primary hover:text-primary-foreground transition-all"
                    >
                      {session.status === 'report_ready' ? <FileText className="w-5 h-5" /> : <ChevronRight className="w-5 h-5" />}
                    </Link>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        )}
      </div>
      <Footer />
    </div>
  );
}
