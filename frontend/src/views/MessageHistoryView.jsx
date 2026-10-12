import React, { useEffect, useState } from 'react';
import { Search, CheckCheck, Check, Clock, ArrowDownLeft, ArrowUpRight } from 'lucide-react';
import { fetchApi } from '../api';
import DeliveryStatusModal from '../components/DeliveryStatusModal';

export default function MessageHistoryView() {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedMessageId, setSelectedMessageId] = useState(null);

  useEffect(() => {
    loadMessages();
  }, []);

  const loadMessages = async () => {
    setLoading(true);
    try {
      const data = await fetchApi('/api/messages?limit=100');
      setMessages(data);
    } catch (err) {
      console.error('Failed to load message history:', err);
    } finally {
      setLoading(false);
    }
  };

  const filteredMessages = messages.filter((m) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      m.message_text.toLowerCase().includes(q) ||
      (m.shopkeeper_name && m.shopkeeper_name.toLowerCase().includes(q)) ||
      m.recipient_phone.includes(q)
    );
  });

  const getStatusBadge = (status) => {
    switch (status) {
      case 'READ': return <span style={{ color: '#53bdeb', display: 'flex', alignItems: 'center', gap: '3px' }}><CheckCheck size={13} /> Read</span>;
      case 'DELIVERED': return <span style={{ color: '#94a3b8', display: 'flex', alignItems: 'center', gap: '3px' }}><CheckCheck size={13} /> Delivered</span>;
      case 'SENT': return <span style={{ color: '#94a3b8', display: 'flex', alignItems: 'center', gap: '3px' }}><Check size={13} /> Sent</span>;
      default: return <span style={{ color: '#f59e0b', display: 'flex', alignItems: 'center', gap: '3px' }}><Clock size={13} /> {status}</span>;
    }
  };

  return (
    <div className="page-container" style={{ padding: '20px' }}>
      <DeliveryStatusModal
        isOpen={Boolean(selectedMessageId)}
        onClose={() => setSelectedMessageId(null)}
        messageId={selectedMessageId}
      />

      <div style={{ marginBottom: '16px', maxWidth: '320px' }}>
        <div className="search-input-wrapper">
          <Search size={14} />
          <input
            type="text"
            className="search-input"
            placeholder="Search messages..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{ padding: '8px 12px 8px 34px', fontSize: '0.82rem' }}
          />
        </div>
      </div>

      {loading ? (
        <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>Loading message log...</p>
      ) : filteredMessages.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '30px', background: 'var(--bg-card)', borderRadius: '10px', color: 'var(--text-muted)' }}>
          No messages found.
        </div>
      ) : (
        <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: '10px', overflow: 'hidden' }}>
          <table className="custom-table" style={{ fontSize: '0.82rem' }}>
            <thead>
              <tr>
                <th>Direction</th>
                <th>Shopkeeper & Store</th>
                <th>Message Content</th>
                <th>Reply Relationship</th>
                <th>Delivery Status</th>
                <th>Date & Time</th>
              </tr>
            </thead>
            <tbody>
              {filteredMessages.map((m) => {
                const isOutbound = m.direction === 'OUTBOUND';
                return (
                  <tr key={m.id}>
                    <td>
                      <span style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '3px',
                        fontSize: '0.72rem',
                        fontWeight: 700,
                        padding: '2px 6px',
                        borderRadius: '4px',
                        background: isOutbound ? 'rgba(16, 185, 129, 0.15)' : 'rgba(56, 189, 248, 0.15)',
                        color: isOutbound ? '#34d399' : '#38bdf8'
                      }}>
                        {isOutbound ? <ArrowUpRight size={11} /> : <ArrowDownLeft size={11} />}
                        {isOutbound ? 'Sent' : 'Received'}
                      </span>
                    </td>

                    <td>
                      <div style={{ fontWeight: 600, color: '#fff' }}>
                        {isOutbound ? m.shopkeeper_name || 'Shopkeeper' : m.shopkeeper_name}
                      </div>
                      <div style={{ fontSize: '0.72rem', color: '#34d399', fontFamily: 'var(--font-mono)' }}>
                        {m.recipient_phone}
                      </div>
                    </td>

                    <td style={{ maxWidth: '340px' }}>
                      <div style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', color: '#e2e8f0' }}>
                        "{m.message_text}"
                      </div>
                      {m.quoted_message && (
                        <div style={{ fontSize: '0.68rem', color: '#10b981', marginTop: '2px' }}>
                          ↳ Replying to: "{m.quoted_message.message_text.slice(0, 45)}..."
                        </div>
                      )}
                    </td>

                    <td>
                      {m.reply_link_type === 'EXACT' ? (
                        <span style={{ background: 'rgba(16, 185, 129, 0.15)', color: '#34d399', padding: '2px 6px', borderRadius: '4px', fontSize: '0.7rem', fontWeight: 600 }}>
                          Quoted Reply
                        </span>
                      ) : m.reply_link_type === 'INFERRED' ? (
                        <span style={{ background: 'rgba(245, 158, 11, 0.15)', color: '#fbbf24', padding: '2px 6px', borderRadius: '4px', fontSize: '0.7rem', fontWeight: 600 }}>
                          AI Inferred
                        </span>
                      ) : (
                        <span style={{ color: 'var(--text-dim)', fontSize: '0.72rem' }}>Direct</span>
                      )}
                    </td>

                    <td>
                      <button
                        onClick={() => setSelectedMessageId(m.id)}
                        style={{ background: 'transparent', border: 'none', cursor: 'pointer', padding: 0 }}
                        title="Click to view delivery details"
                      >
                        {getStatusBadge(m.delivery_status)}
                      </button>
                    </td>

                    <td>
                      <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>
                        {new Date(m.message_timestamp).toLocaleDateString()} {new Date(m.message_timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
