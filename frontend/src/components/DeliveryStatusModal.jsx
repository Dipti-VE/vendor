import React, { useEffect, useState } from 'react';
import { X, Check, CheckCheck, Clock, AlertTriangle, ShieldCheck } from 'lucide-react';
import { fetchApi } from '../api';

export default function DeliveryStatusModal({ isOpen, onClose, messageId }) {
  const [history, setHistory] = useState([]);
  const [message, setMessage] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isOpen && messageId) {
      loadDetails();
    }
  }, [isOpen, messageId]);

  const loadDetails = async () => {
    setLoading(true);
    try {
      const [msgData, histData] = await Promise.all([
        fetchApi(`/api/messages/${messageId}`),
        fetchApi(`/api/messages/${messageId}/status-history`)
      ]);
      setMessage(msgData);
      setHistory(histData);
    } catch (err) {
      console.error('Failed to load message status history:', err);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  const getStatusIcon = (st) => {
    switch (st) {
      case 'PENDING': return <Clock size={16} color="#94a3b8" />;
      case 'SENT': return <Check size={16} color="#94a3b8" />;
      case 'DELIVERED': return <CheckCheck size={16} color="#94a3b8" />;
      case 'READ': return <CheckCheck size={16} color="#53bdeb" />;
      case 'FAILED': return <AlertTriangle size={16} color="#f43f5e" />;
      default: return <Clock size={16} />;
    }
  };

  return (
    <div className="modal-overlay">
      <div className="modal-content" style={{ maxWidth: '560px' }}>
        <div className="modal-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{ background: 'rgba(37, 211, 102, 0.15)', padding: '8px', borderRadius: '8px', color: '#25d366' }}>
              <ShieldCheck size={20} />
            </div>
            <div>
              <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#fff' }}>WhatsApp Delivery Audit Trail</h3>
              <p style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>Status event progression & provider timestamps</p>
            </div>
          </div>
          <button onClick={onClose} style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}>
            <X size={20} />
          </button>
        </div>

        <div className="modal-body">
          {loading ? (
            <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>Loading status history...</p>
          ) : message ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div style={{ padding: '12px', background: 'rgba(0, 0, 0, 0.25)', borderRadius: '8px', fontSize: '0.8rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Internal Message ID:</span>
                  <span style={{ fontWeight: 600, color: '#fff' }}>#{message.id}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                  <span style={{ color: 'var(--text-muted)' }}>WhatsApp Provider ID:</span>
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.74rem', color: '#38bdf8' }}>{message.whatsapp_message_id || 'Pending Meta generation'}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Direction / Route:</span>
                  <span style={{ fontWeight: 600, color: message.direction === 'OUTBOUND' ? '#34d399' : '#60a5fa' }}>
                    {message.direction} ({message.sender_phone} → {message.recipient_phone})
                  </span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Reply Link Type:</span>
                  <span style={{ fontWeight: 700, color: message.reply_link_type === 'EXACT' ? '#10b981' : message.reply_link_type === 'INFERRED' ? '#fbbf24' : '#94a3b8' }}>
                    {message.reply_link_type} {message.reply_to_message_id ? `(Parent Msg #${message.reply_to_message_id})` : ''}
                  </span>
                </div>
              </div>

              <div>
                <h4 style={{ fontSize: '0.82rem', fontWeight: 700, color: 'var(--text-muted)', marginBottom: '12px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  Status Event Timeline
                </h4>
                
                {history.length === 0 ? (
                  <p style={{ color: 'var(--text-dim)', fontSize: '0.8rem' }}>No status events logged yet.</p>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', position: 'relative', paddingLeft: '24px' }}>
                    <div style={{ position: 'absolute', left: '7px', top: '8px', bottom: '8px', width: '2px', background: 'rgba(255, 255, 255, 0.1)' }}></div>
                    {history.map((h, idx) => (
                      <div key={h.id || idx} style={{ display: 'flex', alignItems: 'flex-start', gap: '10px', position: 'relative' }}>
                        <div style={{ position: 'absolute', left: '-24px', width: '16px', height: '16px', borderRadius: '50%', background: 'var(--bg-card)', border: '2px solid #10b981', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                          <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#10b981' }}></div>
                        </div>
                        <div style={{ flex: 1, background: 'rgba(255, 255, 255, 0.03)', padding: '8px 12px', borderRadius: '6px', border: '1px solid var(--border-subtle)' }}>
                          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '3px' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontWeight: 700, fontSize: '0.82rem', color: '#fff' }}>
                              {getStatusIcon(h.status)}
                              <span>{h.status}</span>
                            </div>
                            <span style={{ fontSize: '0.72rem', color: 'var(--text-dim)' }}>
                              {new Date(h.status_timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                            </span>
                          </div>
                          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                            Date: {new Date(h.status_timestamp).toLocaleDateString()} | Event ID: {h.provider_event_id || 'internal_ack'}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ) : (
            <p style={{ color: 'var(--text-muted)' }}>Message details not found.</p>
          )}
        </div>

        <div className="modal-footer">
          <button type="button" className="btn btn-secondary" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
