import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Shield, CheckCircle, Search, AlertCircle, ExternalLink, Users, History } from 'lucide-react';
import { Navbar } from "@/components/Navbar";
import { Footer } from "@/components/Footer";
import { FloatingOrbs } from "@/components/FloatingOrbs";
import { supabase } from "@/lib/supabase";
import { adminApprove } from "@/lib/api";
import { Link } from 'react-router-dom';

interface Session {
  thread_id: string;
  idea_description: string;
  status: string;
  tier: string;
  user_id: string;
  created_at: string;
  reports?: any;
}

export default function AdminDashboard() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [loading, setLoading] = useState(true);
  const [approving, setApproving] = useState<string | null>(null);

  useEffect(() => {
    async function fetchPendingSessions() {
      const { data, error } = await supabase
        .from('validation_sessions')
        .select(`
          *,
          reports!reports_thread_id_fkey (
            report_data,
            tier
          )
        `)
        .in('status', ['waiting_for_admin', 'waiting_for_admin_approval'])
        .order('created_at', { ascending: true });

      if (error) {
        console.error('Error fetching sessions:', error);
      } else {
        setSessions(data || []);
      }
      setLoading(false);
    }

    fetchPendingSessions();
    
    // Subscribe to updates
    const channel = supabase
      .channel('admin-updates')
      .on('postgres_changes', { event: '*', schema: 'public', table: 'validation_sessions' }, () => {
        fetchPendingSessions();
      })
      .subscribe();

    return () => {
      supabase.removeChannel(channel);
    };
  }, []);

  const handleApprove = async (threadId: string) => {
    setApproving(threadId);
    try {
      await adminApprove(threadId);
      // Update local state
      setSessions(prev => prev.filter(s => s.thread_id !== threadId));
    } catch (err) {
      console.error('Approval failed:', err);
      alert('Failed to approve report. Check console for details.');
    } finally {
      setApproving(null);
    }
  };

  return (
    <div className="min-h-screen relative">
      <FloatingOrbs />
      <Navbar />
      
      <div className="pt-28 pb-10 container mx-auto px-6 max-w-6xl">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold flex items-center gap-3">
              <Shield className="w-8 h-8 text-primary" />
              Academic Admin Oversight
            </h1>
            <p className="text-muted-foreground mt-1">Review and approve AI-generated research reports</p>
          </div>
          <div className="flex gap-4">
            <div className="glass px-4 py-2 rounded-lg flex items-center gap-2">
              <Users className="w-4 h-4 text-primary" />
              <span className="text-sm font-semibold">{sessions.length} Pending Approval</span>
            </div>
          </div>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-20">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          </div>
        ) : sessions.length === 0 ? (
          <div className="glass rounded-2xl p-12 text-center border-dashed border-2 border-border">
            <div className="w-16 h-16 bg-secondary rounded-full flex items-center justify-center mx-auto mb-4">
              <CheckCircle className="w-8 h-8 text-green-500" />
            </div>
            <h3 className="text-xl font-semibold mb-2">Queue Clear!</h3>
            <p className="text-muted-foreground">All premium research reports have been reviewed and released.</p>
          </div>
        ) : (
          <div className="grid gap-4">
            {sessions.map((session) => (
              <motion.div
                key={session.thread_id}
                initial={{ opacity: 0, scale: 0.98 }}
                animate={{ opacity: 1, scale: 1 }}
                className="glass rounded-xl p-6 border-l-4 border-l-amber-500"
              >
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-3 mb-2">
                      <span className="px-2 py-0.5 rounded-md bg-amber-500/20 text-amber-500 text-[10px] font-bold uppercase tracking-wider border border-amber-500/30">
                        Needs Review: {session.tier}
                      </span>
                      <span className="text-xs text-muted-foreground flex items-center gap-1">
                        <History className="w-3 h-3" />
                        Requested {new Date(session.created_at).toLocaleString()}
                      </span>
                    </div>
                    <h3 className="text-xl font-bold mb-1 text-foreground">
                      {(() => {
                        const reports = Array.isArray(session.reports) ? session.reports : (session.reports ? [session.reports] : []);
                        const currentReport = reports.find((r: any) => r.tier === session.tier);
                        return currentReport?.report_data?.title || (session.idea_description?.length > 100 ? session.idea_description.substring(0, 100) + '...' : session.idea_description);
                      })()}
                    </h3>
                    <p className="text-xs text-muted-foreground font-mono truncate">
                      Thread ID: {session.thread_id} | User ID: {session.user_id}
                    </p>
                  </div>

                  <div className="flex items-center gap-3">
                    <Link
                      to={`/report/${session.thread_id}?tier=${session.tier}&preview=true`}
                      className="p-2.5 rounded-lg bg-secondary hover:bg-secondary/80 transition-all flex items-center gap-2 text-sm font-medium"
                      title="Preview Report"
                    >
                      <Search className="w-4 h-4" />
                      Preview
                    </Link>
                    
                    <button
                      onClick={() => handleApprove(session.thread_id)}
                      disabled={approving === session.thread_id}
                      className="px-6 py-2.5 rounded-lg bg-primary text-primary-foreground font-semibold hover:bg-primary/90 transition-all flex items-center gap-2 disabled:opacity-50"
                    >
                      {approving === session.thread_id ? (
                        <>
                          <AlertCircle className="w-4 h-4 animate-spin" />
                          Finalizing...
                        </>
                      ) : (
                        <>
                          <CheckCircle className="w-4 h-4" />
                          Approve & Release
                        </>
                      )}
                    </button>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        )}

        <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="glass p-6 rounded-xl">
            <h3 className="font-semibold mb-2 flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-amber-500" />
              Pre-Approval Checks
            </h3>
            <ul className="text-xs text-muted-foreground space-y-2">
              <li>• Verify market data consistency</li>
              <li>• Check financial projection logic</li>
              <li>• Ensure executive summary tone</li>
            </ul>
          </div>
          <div className="glass p-6 rounded-xl">
            <h3 className="font-semibold mb-2 flex items-center gap-2">
              <ExternalLink className="w-4 h-4 text-blue-500" />
              Quick Links
            </h3>
            <ul className="text-xs text-muted-foreground space-y-2">
              <li className="hover:text-primary cursor-pointer">Supabase Dashboard</li>
              <li className="hover:text-primary cursor-pointer">Tavily Research Logs</li>
              <li className="hover:text-primary cursor-pointer">API Documentation</li>
            </ul>
          </div>
          <div className="glass p-6 rounded-xl">
            <h3 className="font-semibold mb-2 flex items-center gap-2">
              <Users className="w-4 h-4 text-primary" />
              Admin Roles
            </h3>
            <p className="text-xs text-muted-foreground">
              You are logged in as a <strong>Senior Researcher</strong>. Your approvals are final and will notify the user via email.
            </p>
          </div>
        </div>
      </div>
      <Footer />
    </div>
  );
}
