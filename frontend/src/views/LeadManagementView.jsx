import React, { useEffect, useState } from 'react';
import { 
  TrendingUp, MessageSquare, Phone, Store, ArrowRight, CheckCircle2, ChevronRight
} from 'lucide-react';
import { fetchApi } from '../api';
import confetti from 'canvas-confetti';

export default function LeadManagementView({ onNavigate }) {
  const [pipeline, setPipeline] = useState({
    INTERESTED: [],
    CONTACTED: [],
    NEGOTIATING: [],
    CONVERTED: [],
    NOT_INTERESTED: []
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadPipeline();
  }, []);

  const loadPipeline = async () => {
    setLoading(true);
    try {
      const data = await fetchApi('/api/leads/pipeline');
      setPipeline(data);
    } catch (err) {
      console.error('Failed to load lead pipeline:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleMoveStage = async (convId, nextStage) => {
    try {
      await fetchApi(`/api/conversations/${convId}/status`, {
        method: 'PATCH',
        body: JSON.stringify({ lead_status: nextStage })
      });
      if (nextStage === 'CONVERTED') {
        confetti({
          particleCount: 80,
          spread: 60,
          origin: { y: 0.6 }
        });
      }
      loadPipeline();
    } catch (err) {
      alert('Error updating lead stage: ' + err.message);
    }
  };

  const stages = [
    { key: 'INTERESTED', title: 'Interested', color: '#60a5fa', desc: 'New leads & inquiries' },
    { key: 'CONTACTED', title: 'Contacted', color: '#fbbf24', desc: 'Outbound pitch delivered' },
    { key: 'NEGOTIATING', title: 'Negotiating', color: '#a78bfa', desc: 'Price / quantity discussions' },
    { key: 'CONVERTED', title: 'Converted 🎉', color: '#34d399', desc: 'Deal closed & orders placed' },
    { key: 'NOT_INTERESTED', title: 'Not Interested', color: '#fb7185', desc: 'Uninterested or closed' }
  ];

  return (
    <div className="page-container">
      {/* Top Header */}
      <div style={{ marginBottom: '20px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
          <span style={{ background: 'rgba(16, 185, 129, 0.15)', color: '#10b981', fontSize: '0.72rem', fontWeight: 800, padding: '2px 8px', borderRadius: '4px' }}>
            SALES PIPELINE
          </span>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Lead conversion funnel & negotiation stages</span>
        </div>
        <h2 style={{ fontSize: '1.3rem', fontWeight: 800, color: '#fff' }}>Shopkeeper Lead Management</h2>
      </div>

      {/* Kanban Board */}
      {loading ? (
        <p style={{ color: 'var(--text-muted)' }}>Loading lead pipeline...</p>
      ) : (
        <div className="kanban-board">
          {stages.map((stage) => {
            const cards = pipeline[stage.key] || [];

            return (
              <div key={stage.key} className="kanban-col">
                <div className="kanban-col-header" style={{ borderTop: `3px solid ${stage.color}` }}>
                  <div>
                    <span style={{ color: stage.color }}>{stage.title}</span>
                    <p style={{ fontSize: '0.68rem', color: 'var(--text-dim)', fontWeight: 400 }}>{stage.desc}</p>
                  </div>
                  <span style={{ background: 'rgba(255,255,255,0.08)', padding: '2px 8px', borderRadius: '10px', fontSize: '0.72rem', color: '#fff' }}>
                    {cards.length}
                  </span>
                </div>

                <div className="kanban-cards-wrapper">
                  {cards.length === 0 ? (
                    <div style={{ padding: '20px', textAlign: 'center', color: 'var(--text-dim)', fontSize: '0.76rem' }}>
                      No shopkeepers in this stage
                    </div>
                  ) : (
                    cards.map((item) => (
                      <div key={item.conversation_id} className="kanban-card">
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '6px' }}>
                          <h4 style={{ fontSize: '0.86rem', fontWeight: 700, color: '#fff' }}>
                            {item.shopkeeper_name}
                          </h4>
                        </div>

                        <div style={{ fontSize: '0.74rem', color: '#38bdf8', marginBottom: '4px' }}>
                          {item.shop_name} • {item.location}
                        </div>

                        {item.product_name && (
                          <div style={{ fontSize: '0.72rem', color: '#34d399', background: 'rgba(16, 185, 129, 0.1)', padding: '2px 6px', borderRadius: '4px', marginBottom: '8px', display: 'inline-block' }}>
                            {item.product_name}
                          </div>
                        )}

                        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', background: 'rgba(0,0,0,0.25)', padding: '6px 8px', borderRadius: '4px', marginBottom: '10px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                          "{item.last_message_preview}"
                        </div>

                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderTop: '1px solid rgba(255,255,255,0.05)', paddingTop: '8px' }}>
                          <button
                            className="btn btn-whatsapp btn-sm"
                            style={{ padding: '3px 8px', fontSize: '0.72rem' }}
                            onClick={() => onNavigate('inbox', { shopkeeperId: item.shopkeeper_id })}
                          >
                            <MessageSquare size={12} /> Chat
                          </button>

                          {/* Move stage dropdown or next button */}
                          <div style={{ display: 'flex', gap: '4px' }}>
                            {stage.key !== 'CONVERTED' && (
                              <button
                                className="btn btn-secondary btn-sm"
                                style={{ padding: '3px 8px', fontSize: '0.7rem' }}
                                onClick={() => {
                                  const nextIdx = stages.findIndex(s => s.key === stage.key) + 1;
                                  if (nextIdx < stages.length) {
                                    handleMoveStage(item.conversation_id, stages[nextIdx].key);
                                  }
                                }}
                                title="Move to next stage"
                              >
                                Next <ChevronRight size={11} />
                              </button>
                            )}
                          </div>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
