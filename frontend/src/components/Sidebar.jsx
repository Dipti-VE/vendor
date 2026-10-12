import React from 'react';
import { 
  MessageSquare, Sparkles, Users, FileText, Package, Globe
} from 'lucide-react';

export default function Sidebar({ currentView, onNavigate, onOpenWebhookModal, unreadCount }) {
  const navItems = [
    { key: 'inbox', label: 'WhatsApp Chat', icon: MessageSquare, badge: unreadCount },
    { key: 'matches', label: 'Offers & Matches', icon: Sparkles },
    { key: 'shopkeepers', label: 'Shopkeepers', icon: Users },
    { key: 'messages', label: 'Message History', icon: FileText }
  ];

  return (
    <aside className="app-sidebar" style={{ width: '240px' }}>
      {/* Brand Header */}
      <div className="sidebar-header" style={{ padding: '16px 18px' }}>
        <div className="logo-badge" style={{ width: '36px', height: '36px', borderRadius: '10px' }}>
          <Package size={20} />
        </div>
        <div className="logo-text">
          <h2 style={{ fontSize: '1rem' }}>GreenPack</h2>
          <span style={{ fontSize: '0.72rem' }}>
            <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#25d366', display: 'inline-block' }}></span>
            WhatsApp Vendor
          </span>
        </div>
      </div>

      {/* Nav List */}
      <nav className="sidebar-nav" style={{ padding: '14px 10px' }}>
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = currentView === item.key;
          return (
            <button
              key={item.key}
              className={`nav-link ${isActive ? 'active' : ''}`}
              onClick={() => onNavigate(item.key)}
              style={{
                width: '100%',
                textAlign: 'left',
                background: isActive ? 'rgba(16, 185, 129, 0.15)' : 'transparent',
                padding: '11px 14px',
                fontSize: '0.88rem'
              }}
            >
              <Icon size={18} />
              <span className="nav-label" style={{ fontWeight: isActive ? 700 : 500 }}>{item.label}</span>
              {item.badge > 0 && (
                <span className="nav-badge active-count">{item.badge}</span>
              )}
            </button>
          );
        })}
      </nav>

      {/* Footer / Profile */}
      <div className="sidebar-footer" style={{ padding: '14px 16px' }}>
        <div style={{ marginBottom: '10px' }}>
          <button
            className="btn btn-secondary btn-sm"
            style={{ width: '100%', fontSize: '0.72rem', justifyContent: 'flex-start', padding: '6px 10px' }}
            onClick={onOpenWebhookModal}
          >
            <Globe size={13} color="#38bdf8" />
            Meta Webhook Settings
          </button>
        </div>

        <div className="vendor-profile-card">
          <div className="vendor-avatar" style={{ width: '32px', height: '32px', fontSize: '0.8rem' }}>RS</div>
          <div className="vendor-info">
            <h4 style={{ fontSize: '0.8rem' }}>Rajesh Sharma</h4>
            <p style={{ fontSize: '0.7rem' }}>+919876543210</p>
          </div>
        </div>
      </div>
    </aside>
  );
}
