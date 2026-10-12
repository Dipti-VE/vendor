import React, { useState } from 'react';
import { Play, Sparkles, MessageSquareQuote, CheckCheck, Send, Zap } from 'lucide-react';
import { fetchApi } from '../api';

export default function WhatsAppSimulatorDrawer({
  selectedConversation,
  lastOutboundMessage,
  onSimulationSuccess
}) {
  const [customReply, setCustomReply] = useState('');
  const [useNativeQuote, setUseNativeQuote] = useState(true);
  const [loading, setLoading] = useState(false);

  if (!selectedConversation) return null;

  const quickReplies = [
    {
      title: "Negotiate Price (₹0.75)",
      text: "Yes, I need 2,000 pieces. Can you offer ₹0.75 per piece?",
      quote: true
    },
    {
      title: "Ask for Samples",
      text: "Can you dispatch a sample box of 100 units to our shop before we place the full order?",
      quote: true
    },
    {
      title: "Confirm Order",
      text: "Deal confirmed! Please share the dispatch schedule and invoice.",
      quote: true
    },
    {
      title: "Inquire Other Item",
      text: "Do you also supply burger wrapping paper and delivery bags?",
      quote: false
    }
  ];

  const handleSimulateReply = async (replyText, quoteParent) => {
    setLoading(true);
    try {
      const payload = {
        shopkeeper_id: selectedConversation.shopkeeper_id,
        message_text: replyText,
        product_offer_id: selectedConversation.product_offer_id,
        reply_to_message_id: quoteParent && lastOutboundMessage ? lastOutboundMessage.id : null,
        use_native_reply: quoteParent && Boolean(lastOutboundMessage)
      };

      await fetchApi('/api/demo/simulate-inbound', {
        method: 'POST',
        body: JSON.stringify(payload)
      });

      setCustomReply('');
      if (onSimulationSuccess) onSimulationSuccess();
    } catch (err) {
      alert('Error simulating inbound reply: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleAdvanceStatus = async (newStatus) => {
    if (!lastOutboundMessage) {
      alert("No outbound message found in this conversation to update status for!");
      return;
    }
    setLoading(true);
    try {
      await fetchApi('/api/demo/simulate-status', {
        method: 'POST',
        body: JSON.stringify({
          message_id: lastOutboundMessage.id,
          new_status: newStatus
        })
      });
      if (onSimulationSuccess) onSimulationSuccess();
    } catch (err) {
      alert('Error updating status: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      background: 'rgba(15, 23, 42, 0.95)',
      borderTop: '1px solid rgba(245, 158, 11, 0.3)',
      padding: '12px 18px',
      display: 'flex',
      flexDirection: 'column',
      gap: '8px'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.8rem', fontWeight: 700, color: '#fbbf24' }}>
          <Zap size={16} />
          <span>Interactive WhatsApp Simulator (Demo Mode)</span>
          <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontWeight: 400 }}>
            Simulate shopkeeper response & status webhooks for {selectedConversation.shopkeeper_name}
          </span>
        </div>

        {lastOutboundMessage && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ fontSize: '0.72rem', color: 'var(--text-dim)' }}>Status Webhook:</span>
            <button
              className="btn btn-secondary btn-sm"
              onClick={() => handleAdvanceStatus('DELIVERED')}
              disabled={loading}
              style={{ fontSize: '0.72rem', padding: '3px 8px' }}
            >
              <CheckCheck size={12} color="#94a3b8" /> Mark Delivered
            </button>
            <button
              className="btn btn-secondary btn-sm"
              onClick={() => handleAdvanceStatus('READ')}
              disabled={loading}
              style={{ fontSize: '0.72rem', padding: '3px 8px' }}
            >
              <CheckCheck size={12} color="#53bdeb" /> Mark Read
            </button>
          </div>
        )}
      </div>

      <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', alignItems: 'center' }}>
        <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Quick Simulate Reply:</span>
        {quickReplies.map((qr, idx) => (
          <button
            key={idx}
            className="btn btn-secondary btn-sm"
            onClick={() => handleSimulateReply(qr.text, qr.quote)}
            disabled={loading}
            style={{ fontSize: '0.74rem', padding: '4px 9px' }}
          >
            {qr.quote ? <MessageSquareQuote size={12} color="#10b981" /> : <Play size={12} />}
            {qr.title}
          </button>
        ))}
      </div>

      <div style={{ display: 'flex', gap: '8px', alignItems: 'center', marginTop: '2px' }}>
        <input
          type="text"
          className="form-control"
          style={{ padding: '6px 12px', fontSize: '0.8rem', flex: 1 }}
          placeholder="Or type custom simulated reply from shopkeeper..."
          value={customReply}
          onChange={(e) => setCustomReply(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && customReply.trim()) {
              handleSimulateReply(customReply, useNativeQuote);
            }
          }}
        />
        <label style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.72rem', color: 'var(--text-muted)', cursor: 'pointer', whiteSpace: 'nowrap' }}>
          <input
            type="checkbox"
            checked={useNativeQuote}
            onChange={(e) => setUseNativeQuote(e.target.checked)}
          />
          Quote Vendor Msg (EXACT)
        </label>
        <button
          className="btn btn-primary btn-sm"
          onClick={() => handleSimulateReply(customReply, useNativeQuote)}
          disabled={loading || !customReply.trim()}
          style={{ padding: '6px 12px', fontSize: '0.78rem' }}
        >
          <Send size={12} /> Simulate Send
        </button>
      </div>
    </div>
  );
}
