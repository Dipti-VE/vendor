import React, { useEffect, useState, useRef } from 'react';
import { 
  Send, MessageSquare, Phone, Check, CheckCheck, Clock, 
  Sparkles, X, Zap
} from 'lucide-react';
import { fetchApi } from '../api';
import DeliveryStatusModal from '../components/DeliveryStatusModal';

import { formatTime, formatDateTime } from '../utils/dateUtils';

export default function WhatsAppInboxView({ initialShopkeeperId, initialOfferId }) {
  const [conversations, setConversations] = useState([]);
  const [selectedConv, setSelectedConv] = useState(null);
  const [messages, setMessages] = useState([]);
  const [loadingConv, setLoadingConv] = useState(true);
  const [loadingMessages, setLoadingMessages] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  
  const [inputText, setInputText] = useState('');
  const [replyingToMsg, setReplyingToMsg] = useState(null);
  const [aiDraftLoading, setAiDraftLoading] = useState(false);
  const [simLoading, setSimLoading] = useState(false);
  
  const [statusModalMsgId, setStatusModalMsgId] = useState(null);

  const messagesEndRef = useRef(null);

  useEffect(() => {
    loadConversations();
  }, []);

  const loadConversations = async () => {
    setLoadingConv(true);
    try {
      const data = await fetchApi('/api/conversations');
      setConversations(data);
      if (data.length > 0) {
        if (initialShopkeeperId) {
          const match = data.find((c) => c.shopkeeper_id === initialShopkeeperId);
          setSelectedConv(match || data[0]);
        } else if (!selectedConv) {
          setSelectedConv(data[0]);
        }
      }
    } catch (err) {
      console.error('Failed to load conversations:', err);
    } finally {
      setLoadingConv(false);
    }
  };

  useEffect(() => {
    if (selectedConv) {
      loadMessages(selectedConv.id);
    }
  }, [selectedConv]);

  const loadMessages = async (convId) => {
    setLoadingMessages(true);
    try {
      const msgs = await fetchApi(`/api/conversations/${convId}/messages`);
      setMessages(msgs);
      setTimeout(() => scrollToBottom(), 80);
    } catch (err) {
      console.error('Failed to load messages:', err);
    } finally {
      setLoadingMessages(false);
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSendMessage = async (e) => {
    e?.preventDefault();
    if (!inputText.trim() || !selectedConv) return;

    const textToSend = inputText.trim();
    setInputText('');
    const replyTarget = replyingToMsg;
    try {
      const isTemplateText = ['hello_world', 'hello world', '/template'].includes(textToSend.toLowerCase());
      const payload = {
        shopkeeper_id: selectedConv.shopkeeper_id,
        message_text: textToSend,
        product_offer_id: selectedConv.product_offer_id,
        reply_to_message_id: replyTarget ? replyTarget.id : null,
        is_simulation: false,
        is_template: isTemplateText,
        template_name: 'hello_world'
      };

      const newMsg = await fetchApi(`/api/conversations/${selectedConv.id}/messages`, {
        method: 'POST',
        body: JSON.stringify(payload)
      });

      setMessages((prev) => [...prev, newMsg]);
      setTimeout(() => scrollToBottom(), 80);
      loadConversations();
    } catch (err) {
      alert('Error sending WhatsApp message: ' + err.message);
    }
  };

  const handleSendTemplate = async () => {
    if (!selectedConv) return;
    setSimLoading(true);
    try {
      const newMsg = await fetchApi(`/api/conversations/${selectedConv.id}/initiate-template`, {
        method: 'POST'
      });
      setMessages((prev) => [...prev, newMsg]);
      setTimeout(() => scrollToBottom(), 80);
      loadConversations();
    } catch (err) {
      alert('Error sending WhatsApp template: ' + err.message);
    } finally {
      setSimLoading(false);
    }
  };

  const handleSimulateShopkeeperReply = async (replyText) => {
    if (!selectedConv) return;
    setSimLoading(true);
    try {
      const lastOutbound = messages.filter((m) => m.direction === 'OUTBOUND').slice(-1)[0];
      await fetchApi('/api/demo/simulate-inbound', {
        method: 'POST',
        body: JSON.stringify({
          shopkeeper_id: selectedConv.shopkeeper_id,
          message_text: replyText,
          product_offer_id: selectedConv.product_offer_id,
          reply_to_message_id: lastOutbound ? lastOutbound.id : null,
          use_native_reply: Boolean(lastOutbound)
        })
      });
      loadMessages(selectedConv.id);
      loadConversations();
    } catch (err) {
      alert('Error simulating reply: ' + err.message);
    } finally {
      setSimLoading(false);
    }
  };

  const handleSimulateStatus = async (status) => {
    const lastOutbound = messages.filter((m) => m.direction === 'OUTBOUND').slice(-1)[0];
    if (!lastOutbound) {
      alert("Send a message first to simulate delivery status!");
      return;
    }
    setSimLoading(true);
    try {
      await fetchApi('/api/demo/simulate-status', {
        method: 'POST',
        body: JSON.stringify({
          message_id: lastOutbound.id,
          new_status: status
        })
      });
      loadMessages(selectedConv.id);
    } catch (err) {
      alert('Error updating status: ' + err.message);
    } finally {
      setSimLoading(false);
    }
  };

  const handleRequestAiDraft = async () => {
    if (!selectedConv) return;
    setAiDraftLoading(true);
    try {
      const res = await fetchApi(`/api/conversations/${selectedConv.id}/ai-draft`, {
        method: 'POST',
        body: JSON.stringify({
          conversation_id: selectedConv.id,
          product_offer_id: selectedConv.product_offer_id,
          intent: 'initial_pitch'
        })
      });
      if (res.suggested_text) {
        setInputText(res.suggested_text);
      }
    } catch (err) {
      alert('Error drafting AI response: ' + err.message);
    } finally {
      setAiDraftLoading(false);
    }
  };

  const filteredConversations = conversations.filter((c) => {
    const q = searchQuery.toLowerCase();
    return (
      c.shopkeeper_name.toLowerCase().includes(q) ||
      c.shop_name.toLowerCase().includes(q) ||
      c.whatsapp_phone.toLowerCase().includes(q)
    );
  });

  const getStatusTick = (status) => {
    switch (status) {
      case 'PENDING': return <Clock size={12} color="#94a3b8" title="Pending" />;
      case 'SENT': return <Check size={12} color="#94a3b8" title="Sent (Single Tick)" />;
      case 'DELIVERED': return <CheckCheck size={12} color="#94a3b8" title="Delivered (Double Tick)" />;
      case 'READ': return <CheckCheck size={12} color="#53bdeb" className="tick-read" title="Read (Blue Ticks)" />;
      default: return <Clock size={12} />;
    }
  };

  return (
    <div className="inbox-container" style={{ height: 'calc(100vh - 58px)' }}>
      {/* Delivery Status Modal */}
      <DeliveryStatusModal
        isOpen={Boolean(statusModalMsgId)}
        onClose={() => setStatusModalMsgId(null)}
        messageId={statusModalMsgId}
      />

      {/* Left Column: Simple Shopkeepers Chat List */}
      <div className="inbox-conversations-list" style={{ width: '320px' }}>
        <div className="inbox-search-bar" style={{ padding: '10px 12px' }}>
          <div className="search-input-wrapper">
            <input
              type="text"
              className="search-input"
              placeholder="Search chats..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{ padding: '8px 12px', fontSize: '0.82rem' }}
            />
          </div>
        </div>

        <div style={{ flex: 1, overflowY: 'auto' }}>
          {loadingConv ? (
            <p style={{ padding: '16px', color: 'var(--text-muted)', fontSize: '0.85rem' }}>Loading chats...</p>
          ) : filteredConversations.length === 0 ? (
            <p style={{ padding: '16px', color: 'var(--text-dim)', fontSize: '0.82rem', textAlign: 'center' }}>No conversations</p>
          ) : (
            filteredConversations.map((conv) => {
              const isSelected = selectedConv?.id === conv.id;
              return (
                <div
                  key={conv.id}
                  className={`conv-item ${isSelected ? 'selected' : ''}`}
                  onClick={() => setSelectedConv(conv)}
                  style={{ padding: '12px 14px' }}
                >
                  <div className="conv-avatar" style={{ width: '38px', height: '38px', fontSize: '0.85rem' }}>
                    {conv.shopkeeper_name.slice(0, 2).toUpperCase()}
                  </div>

                  <div className="conv-body">
                    <div className="conv-top">
                      <span className="conv-name" style={{ fontSize: '0.88rem' }}>{conv.shopkeeper_name}</span>
                      <span className="conv-time">
                        {conv.latest_message ? formatTime(conv.latest_message.message_timestamp) : ''}
                      </span>
                    </div>

                    <div className="conv-shop" style={{ fontSize: '0.74rem' }}>
                      {conv.shop_name} • <span style={{ color: '#34d399', fontFamily: 'var(--font-mono)' }}>{conv.whatsapp_phone}</span>
                    </div>

                    <div className="conv-snippet" style={{ fontSize: '0.76rem', marginTop: '2px' }}>
                      {conv.latest_message ? (
                        <>
                          {conv.latest_message.direction === 'OUTBOUND' && getStatusTick(conv.latest_message.delivery_status)}
                          <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                            {conv.latest_message.message_text}
                          </span>
                        </>
                      ) : (
                        <span>Start chat</span>
                      )}
                    </div>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>

      {/* Right Column: WhatsApp Chat Area */}
      {selectedConv ? (
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', background: '#0b141a' }}>
          {/* Simple Header */}
          <div className="chat-header" style={{ height: '54px', padding: '0 16px', background: '#111b21' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <div className="conv-avatar" style={{ width: '36px', height: '36px', fontSize: '0.82rem' }}>
                {selectedConv.shopkeeper_name.slice(0, 2).toUpperCase()}
              </div>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ fontWeight: 700, color: '#fff', fontSize: '0.92rem' }}>
                    {selectedConv.shopkeeper_name}
                  </span>
                  <span style={{ fontSize: '0.74rem', color: '#38bdf8' }}>
                    ({selectedConv.shop_name})
                  </span>
                </div>
                <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <span style={{ color: '#34d399', fontFamily: 'var(--font-mono)' }}>{selectedConv.whatsapp_phone}</span>
                  <span>•</span>
                  <span>{selectedConv.shopkeeper_location}</span>
                </div>
              </div>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <button
                type="button"
                onClick={handleSendTemplate}
                disabled={simLoading}
                style={{
                  background: 'linear-gradient(135deg, #059669, #10b981)',
                  color: '#fff',
                  border: 'none',
                  borderRadius: '6px',
                  padding: '5px 11px',
                  fontSize: '0.74rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '5px',
                  boxShadow: '0 2px 6px rgba(16, 185, 129, 0.25)'
                }}
                title="Send Meta registered 'hello_world' template to unlock phone for 24 hours"
              >
                <span>⚡ Send "hello_world" Template</span>
              </button>

              {selectedConv.product_name && (
                <span style={{ background: 'rgba(16, 185, 129, 0.15)', color: '#34d399', padding: '3px 8px', borderRadius: '4px', fontSize: '0.72rem', fontWeight: 600 }}>
                  {selectedConv.product_name}
                </span>
              )}
            </div>
          </div>

          {/* Messages Feed */}
          <div className="chat-messages-scroll" style={{ flex: 1, overflowY: 'auto', padding: '16px' }}>
            {loadingMessages ? (
              <p style={{ textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.82rem' }}>Loading messages...</p>
            ) : messages.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '30px', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                <p>Send an opening message to {selectedConv.shopkeeper_name} below!</p>
              </div>
            ) : (
              messages.map((msg) => {
                const isOutbound = msg.direction === 'OUTBOUND';

                return (
                  <div key={msg.id} className={`message-bubble-row ${isOutbound ? 'outbound' : 'inbound'}`}>
                    <div className={`message-bubble ${isOutbound ? 'outbound' : 'inbound'}`}>
                      {/* Quoted Original Message */}
                      {msg.quoted_message && (
                        <div className="quoted-box">
                          <div className="quoted-box-header">
                            <span className="quoted-box-sender">
                              ↩ {msg.quoted_message.direction === 'OUTBOUND' ? 'You' : selectedConv.shopkeeper_name}
                            </span>
                            <span className="quoted-box-time">
                              {formatDateTime(msg.quoted_message.message_timestamp)}
                            </span>
                          </div>
                          <div className="quoted-box-text">
                            "{msg.quoted_message.message_text}"
                          </div>
                        </div>
                      )}

                      {/* Content */}
                      <div>{msg.message_text}</div>

                      {/* Timestamp & Status */}
                      <div className="message-meta">
                        <span title={formatDateTime(msg.message_timestamp)}>
                          {formatTime(msg.message_timestamp)}
                        </span>

                        {isOutbound && (
                          <span 
                            style={{ cursor: 'pointer', display: 'inline-flex' }}
                            onClick={() => setStatusModalMsgId(msg.id)}
                            title="Click to view delivery history"
                          >
                            {getStatusTick(msg.delivery_status)}
                          </span>
                        )}

                        <button
                          onClick={() => setReplyingToMsg(msg)}
                          style={{
                            background: 'transparent',
                            border: 'none',
                            color: 'rgba(255, 255, 255, 0.4)',
                            cursor: 'pointer',
                            padding: '0 2px',
                            marginLeft: '4px',
                            fontSize: '0.65rem'
                          }}
                          title="Reply to message"
                        >
                          Quote
                        </button>
                      </div>
                    </div>
                  </div>
                );
              })
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Quoting preview */}
          {replyingToMsg && (
            <div style={{ background: '#182229', borderLeft: '4px solid #25d366', padding: '6px 14px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div style={{ fontSize: '0.74rem' }}>
                <span style={{ color: '#25d366', fontWeight: 700 }}>
                  Replying to {replyingToMsg.direction === 'OUTBOUND' ? 'your message' : selectedConv.shopkeeper_name} • {formatDateTime(replyingToMsg.message_timestamp)}:
                </span>
                <p style={{ color: 'var(--text-muted)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  "{replyingToMsg.message_text}"
                </p>
              </div>
              <button onClick={() => setReplyingToMsg(null)} style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}>
                <X size={14} />
              </button>
            </div>
          )}

          {/* Simple, Compact 1-line Simulator Helper Bar */}
          <div style={{
            background: '#111b21',
            borderTop: '1px solid rgba(255, 255, 255, 0.06)',
            padding: '6px 14px',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            flexWrap: 'wrap'
          }}>
            <span style={{ fontSize: '0.72rem', color: '#fbbf24', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '3px' }}>
              <Zap size={12} /> Test Simulator:
            </span>

            <button
              className="btn btn-secondary btn-sm"
              onClick={() => handleSimulateShopkeeperReply("Yes, I need 2,000 pieces. Can you offer ₹0.75 per piece?")}
              disabled={simLoading}
              style={{ fontSize: '0.72rem', padding: '3px 8px' }}
            >
              Negotiate Price (₹0.75)
            </button>

            <button
              className="btn btn-secondary btn-sm"
              onClick={() => handleSimulateShopkeeperReply("Can you dispatch a sample box of 100 units first?")}
              disabled={simLoading}
              style={{ fontSize: '0.72rem', padding: '3px 8px' }}
            >
              Ask Samples
            </button>

            <button
              className="btn btn-secondary btn-sm"
              onClick={() => handleSimulateShopkeeperReply("Deal confirmed! Please send payment details.")}
              disabled={simLoading}
              style={{ fontSize: '0.72rem', padding: '3px 8px' }}
            >
              Confirm Deal
            </button>

            <button
              className="btn btn-secondary btn-sm"
              onClick={() => handleSimulateStatus('READ')}
              disabled={simLoading}
              style={{ fontSize: '0.72rem', padding: '3px 8px', color: '#53bdeb' }}
            >
              ✓✓ Mark Read
            </button>
          </div>

          {/* Input Bar */}
          <div className="chat-input-bar" style={{ padding: '10px 14px', background: '#111b21' }}>
            <div className="chat-input-main">
              <button
                type="button"
                className="btn btn-secondary btn-sm"
                onClick={handleRequestAiDraft}
                disabled={aiDraftLoading}
                style={{ padding: '8px 12px', fontSize: '0.76rem', whiteSpace: 'nowrap' }}
                title="AI drafts proposal"
              >
                <Sparkles size={13} color="#f59e0b" />
                {aiDraftLoading ? '...' : 'AI Draft'}
              </button>

              <input
                type="text"
                className="chat-text-input"
                placeholder="Type WhatsApp message to shopkeeper..."
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') handleSendMessage();
                }}
                style={{ padding: '10px 14px', fontSize: '0.86rem' }}
              />

              <button
                type="button"
                className="btn btn-whatsapp"
                onClick={handleSendMessage}
                disabled={!inputText.trim()}
                style={{ borderRadius: '50%', width: '38px', height: '38px', padding: 0 }}
              >
                <Send size={16} />
              </button>
            </div>
          </div>
        </div>
      ) : (
        <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>
          <p>Select a shopkeeper chat on the left to start messaging</p>
        </div>
      )}
    </div>
  );
}
