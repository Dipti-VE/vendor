import React, { useState } from 'react';
import { X, Globe, Shield, Terminal, RefreshCw, CheckCircle2, Copy } from 'lucide-react';
import { fetchApi } from '../api';

export default function WebhookConfigModal({ isOpen, onClose, onResetDemoData }) {
  const [copied, setCopied] = useState(false);
  const [resetting, setResetting] = useState(false);
  const [testResult, setTestResult] = useState(null);

  if (!isOpen) return null;

  const webhookVerifyToken = "smart_vendor_marketplace_secure_token_2026";
  const webhookUrl = `${window.location.origin}/webhooks/whatsapp`;

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleTestVerify = async () => {
    try {
      const res = await fetch(`/webhooks/whatsapp?hub.mode=subscribe&hub.challenge=test_challenge_8899&hub.verify_token=${webhookVerifyToken}`);
      const text = await res.text();
      if (res.status === 200 && text === 'test_challenge_8899') {
        setTestResult({ success: true, message: 'Verification endpoint verified! Returned challenge matching Meta standards.' });
      } else {
        setTestResult({ success: false, message: `Unexpected response: ${text}` });
      }
    } catch (e) {
      setTestResult({ success: false, message: `Error testing endpoint: ${e.message}` });
    }
  };

  const handleResetData = async () => {
    if (!window.confirm("Reset the packaging marketplace database with fresh demo seed data?")) return;
    setResetting(true);
    try {
      await fetchApi('/api/demo/reset-seed', { method: 'POST' });
      if (onResetDemoData) onResetDemoData();
      alert("Database reset successfully!");
      onClose();
    } catch (e) {
      alert("Error resetting database: " + e.message);
    } finally {
      setResetting(false);
    }
  };

  return (
    <div className="modal-overlay">
      <div className="modal-content" style={{ maxWidth: '640px' }}>
        <div className="modal-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{ background: 'rgba(59, 130, 246, 0.15)', padding: '8px', borderRadius: '8px', color: '#60a5fa' }}>
              <Globe size={20} />
            </div>
            <div>
              <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#fff' }}>Meta WhatsApp Webhook Configuration</h3>
              <p style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>Official WhatsApp Business API integration specs</p>
            </div>
          </div>
          <button onClick={onClose} style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}>
            <X size={20} />
          </button>
        </div>

        <div className="modal-body" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div style={{ background: 'rgba(0, 0, 0, 0.25)', padding: '14px', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
              <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)' }}>Webhook Callback URL (Meta Developers Portal):</span>
              <button 
                className="btn btn-secondary btn-sm" 
                onClick={() => copyToClipboard(webhookUrl)}
                style={{ fontSize: '0.72rem', padding: '3px 8px' }}
              >
                {copied ? <CheckCircle2 size={12} color="#10b981" /> : <Copy size={12} />}
                {copied ? 'Copied' : 'Copy URL'}
              </button>
            </div>
            <code style={{ display: 'block', background: 'rgba(0,0,0,0.4)', padding: '8px 10px', borderRadius: '6px', fontSize: '0.78rem', color: '#38bdf8', fontFamily: 'var(--font-mono)', wordBreak: 'break-all' }}>
              {webhookUrl}
            </code>
          </div>

          <div style={{ background: 'rgba(0, 0, 0, 0.25)', padding: '14px', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
              <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)' }}>Verification Token (`hub.verify_token`):</span>
              <button 
                className="btn btn-secondary btn-sm" 
                onClick={() => copyToClipboard(webhookVerifyToken)}
                style={{ fontSize: '0.72rem', padding: '3px 8px' }}
              >
                <Copy size={12} /> Copy Token
              </button>
            </div>
            <code style={{ display: 'block', background: 'rgba(0,0,0,0.4)', padding: '8px 10px', borderRadius: '6px', fontSize: '0.78rem', color: '#34d399', fontFamily: 'var(--font-mono)' }}>
              {webhookVerifyToken}
            </code>
          </div>

          <div style={{ padding: '12px', background: 'rgba(16, 185, 129, 0.08)', borderRadius: '8px', border: '1px solid rgba(16, 185, 129, 0.2)', fontSize: '0.8rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontWeight: 700, color: '#34d399', marginBottom: '6px' }}>
              <Shield size={16} />
              <span>Supported Meta Subscription Events</span>
            </div>
            <ul style={{ paddingLeft: '18px', color: 'var(--text-muted)', lineHeight: '1.6' }}>
              <li><strong>messages:</strong> Incoming text replies with sender phone & native <code>context.id</code> quote metadata.</li>
              <li><strong>statuses:</strong> Outgoing delivery milestones (<code>sent</code>, <code>delivered</code>, <code>read</code>, <code>failed</code>).</li>
            </ul>
          </div>

          {testResult && (
            <div style={{ padding: '10px 14px', borderRadius: '8px', background: testResult.success ? 'rgba(16, 185, 129, 0.15)' : 'rgba(244, 63, 94, 0.15)', color: testResult.success ? '#34d399' : '#fb7185', fontSize: '0.82rem' }}>
              {testResult.message}
            </div>
          )}

          <div style={{ display: 'flex', gap: '10px' }}>
            <button type="button" className="btn btn-secondary btn-sm" onClick={handleTestVerify} style={{ flex: 1 }}>
              <Terminal size={14} /> Test Verification Handshake (GET)
            </button>
            <button type="button" className="btn btn-secondary btn-sm" onClick={handleResetData} disabled={resetting} style={{ flex: 1, color: '#f59e0b' }}>
              <RefreshCw size={14} /> {resetting ? 'Resetting...' : 'Reset Demo Seed Data'}
            </button>
          </div>
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
