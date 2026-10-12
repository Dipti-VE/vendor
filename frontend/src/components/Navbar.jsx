import React from 'react';
import { Plus, Phone } from 'lucide-react';

export default function Navbar({ 
  currentView, 
  wsConnected, 
  onOpenPostOffer, 
  onOpenWebhookModal,
  onNavigate 
}) {
  const titles = {
    inbox: { title: 'WhatsApp Chat', desc: 'Chat directly with retail shopkeepers on WhatsApp (+919064148052)' },
    matches: { title: 'Packaging Offers & Matching', desc: 'Publish wholesale offers and connect with interested shopkeepers' },
    shopkeepers: { title: 'Shopkeepers Directory', desc: 'Registered retail stores and their purchase requirements' },
    messages: { title: 'Message History', desc: 'Searchable log of all incoming and outgoing WhatsApp messages' }
  };

  const current = titles[currentView] || titles.inbox;

  return (
    <header className="app-header" style={{ height: '58px', padding: '0 20px' }}>
      <div className="header-title-block">
        <h1 style={{ fontSize: '1.15rem' }}>{current.title}</h1>
        <p style={{ fontSize: '0.74rem' }}>{current.desc}</p>
      </div>

      <div className="header-actions">
        {/* Direct number badge */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
          background: 'rgba(37, 211, 102, 0.12)',
          border: '1px solid rgba(37, 211, 102, 0.3)',
          color: '#34d399',
          padding: '4px 10px',
          borderRadius: '16px',
          fontSize: '0.75rem',
          fontWeight: 600
        }}>
          <Phone size={12} />
          <span>Shopkeeper WhatsApp: <strong>+91 90641 48052</strong></span>
        </div>

        {/* Quick Post Offer Button */}
        <button className="btn btn-primary btn-sm" onClick={onOpenPostOffer} style={{ padding: '6px 12px', fontSize: '0.8rem' }}>
          <Plus size={14} /> Post Offer
        </button>
      </div>
    </header>
  );
}
