import React, { useEffect, useState } from 'react';
import { 
  Package, Users, HeartHandshake, Sparkles, Send, MessageSquare, 
  CheckCheck, ArrowUpRight, Plus, ExternalLink, ShieldAlert, TrendingUp
} from 'lucide-react';
import { fetchApi } from '../api';
import { formatTime, formatDateTime } from '../utils/dateUtils';

export default function OverviewDashboard({ onNavigate, onOpenPostOffer, onOpenSimulator }) {
  const [metrics, setMetrics] = useState(null);
  const [offers, setOffers] = useState([]);
  const [recentMessages, setRecentMessages] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      const [m, off, msgs] = await Promise.all([
        fetchApi('/api/vendors/metrics'),
        fetchApi('/api/offers'),
        fetchApi('/api/messages?limit=6')
      ]);
      setMetrics(m);
      setOffers(off);
      setRecentMessages(msgs);
    } catch (err) {
      console.error('Failed to load dashboard metrics:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="page-container"><p style={{ color: 'var(--text-muted)' }}>Loading marketplace analytics...</p></div>;
  }

  return (
    <div className="page-container">
      {/* Top Banner */}
      <div style={{
        background: 'linear-gradient(135deg, rgba(7, 94, 84, 0.4) 0%, rgba(18, 140, 126, 0.2) 100%)',
        border: '1px solid rgba(37, 211, 102, 0.25)',
        borderRadius: 'var(--radius-lg)',
        padding: '24px 28px',
        marginBottom: '24px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '16px'
      }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
            <span style={{ background: '#25d366', color: '#064e3b', fontWeight: 800, fontSize: '0.72rem', padding: '2px 8px', borderRadius: '4px' }}>
              META WHATSAPP AUTOMATION ACTIVE
            </span>
            <span style={{ color: 'var(--text-muted)', fontSize: '0.78rem' }}>Cloud API v19.0</span>
          </div>
          <h2 style={{ fontSize: '1.4rem', fontWeight: 800, color: '#fff', marginBottom: '4px' }}>
            Packaging Supplies Vendor Marketplace
          </h2>
          <p style={{ fontSize: '0.86rem', color: '#cbd5e1', maxWidth: '680px' }}>
            Publish offers at wholesale prices, automatically discover interested retail shopkeepers, and communicate with 100% traceable WhatsApp messaging.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '10px' }}>
          <button className="btn btn-secondary" onClick={() => onNavigate('inbox')}>
            <MessageSquare size={16} /> Open WhatsApp Inbox
          </button>
          <button className="btn btn-primary" onClick={onOpenPostOffer}>
            <Plus size={16} /> Post Product Offer
          </button>
        </div>
      </div>

      {/* KPI Stats Grid */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon" style={{ background: 'rgba(16, 185, 129, 0.15)', color: '#10b981' }}>
            <Package size={20} />
          </div>
          <span className="stat-label">Active Product Offers</span>
          <span className="stat-value">{metrics?.active_offers || 0}</span>
          <span className="stat-sub">{metrics?.total_offers || 0} total published offers</span>
        </div>

        <div className="stat-card">
          <div className="stat-icon" style={{ background: 'rgba(59, 130, 246, 0.15)', color: '#3b82f6' }}>
            <Users size={20} />
          </div>
          <span className="stat-label">Registered Shopkeepers</span>
          <span className="stat-value">{metrics?.total_shopkeepers || 0}</span>
          <span className="stat-sub">Retail & restaurant buyers</span>
        </div>

        <div className="stat-card">
          <div className="stat-icon" style={{ background: 'rgba(245, 158, 11, 0.15)', color: '#f59e0b' }}>
            <HeartHandshake size={20} />
          </div>
          <span className="stat-label">Explicit Interest Leads</span>
          <span className="stat-value" style={{ color: '#fbbf24' }}>{metrics?.explicit_interests || 0}</span>
          <span className="stat-sub">Direct quote inquiries</span>
        </div>

        <div className="stat-card">
          <div className="stat-icon" style={{ background: 'rgba(37, 211, 102, 0.15)', color: '#25d366' }}>
            <Send size={20} />
          </div>
          <span className="stat-label">WhatsApp Outbound</span>
          <span className="stat-value">{metrics?.outgoing_messages || 0}</span>
          <span className="stat-sub">Delivery Rate: {metrics?.delivery_rate || 100}%</span>
        </div>

        <div className="stat-card">
          <div className="stat-icon" style={{ background: 'rgba(139, 92, 246, 0.15)', color: '#8b5cf6' }}>
            <MessageSquare size={20} />
          </div>
          <span className="stat-label">Incoming Replies</span>
          <span className="stat-value" style={{ color: '#a78bfa' }}>{metrics?.incoming_messages || 0}</span>
          <span className="stat-sub">Webhook captured responses</span>
        </div>

        <div className="stat-card">
          <div className="stat-icon" style={{ background: 'rgba(16, 185, 129, 0.15)', color: '#10b981' }}>
            <TrendingUp size={20} />
          </div>
          <span className="stat-label">Converted Orders</span>
          <span className="stat-value" style={{ color: '#34d399' }}>{metrics?.converted_leads || 0}</span>
          <span className="stat-sub">Negotiations closed</span>
        </div>
      </div>

      {/* Two Column Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(420px, 1fr))', gap: '20px' }}>
        {/* Active Product Offers Breakdown */}
        <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-lg)', padding: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
            <div>
              <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#fff' }}>Current Product Offers</h3>
              <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Packaging catalog available for shopkeeper matching</p>
            </div>
            <button className="btn btn-secondary btn-sm" onClick={() => onNavigate('offers')}>
              View All Offers <ArrowUpRight size={14} />
            </button>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {offers.slice(0, 4).map((offer) => (
              <div 
                key={offer.id} 
                style={{ 
                  background: 'rgba(0, 0, 0, 0.2)', 
                  border: '1px solid var(--border-subtle)', 
                  borderRadius: 'var(--radius-md)', 
                  padding: '14px 16px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  gap: '12px'
                }}
              >
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                    <span style={{ fontWeight: 700, fontSize: '0.88rem', color: '#fff' }}>{offer.product_name}</span>
                    <span style={{ background: 'rgba(255,255,255,0.08)', fontSize: '0.68rem', padding: '1px 6px', borderRadius: '4px', color: 'var(--text-muted)' }}>
                      {offer.category}
                    </span>
                  </div>
                  <div style={{ fontSize: '0.76rem', color: 'var(--text-muted)' }}>
                    Selling Price: <strong style={{ color: '#34d399' }}>₹{offer.selling_price.toFixed(2)}</strong>/unit • Stock: {offer.available_quantity.toLocaleString()} pcs • MOQ: {offer.minimum_order_quantity}
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <button 
                    className="btn btn-secondary btn-sm"
                    onClick={() => {
                      onNavigate('matches', { offerId: offer.id });
                    }}
                    style={{ whiteSpace: 'nowrap' }}
                  >
                    <Sparkles size={13} color="#f59e0b" />
                    Matches ({offer.interested_count + offer.suggested_matches_count})
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Recent Traceable WhatsApp Activity */}
        <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-lg)', padding: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
            <div>
              <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#fff' }}>Recent WhatsApp Message Flow</h3>
              <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Live audit stream of incoming and outgoing events</p>
            </div>
            <button className="btn btn-secondary btn-sm" onClick={() => onNavigate('messages')}>
              Audit Trail <ArrowUpRight size={14} />
            </button>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {recentMessages.map((msg) => (
              <div 
                key={msg.id}
                style={{
                  background: msg.direction === 'OUTBOUND' ? 'rgba(0, 92, 75, 0.25)' : 'rgba(32, 44, 51, 0.4)',
                  borderLeft: `4px solid ${msg.direction === 'OUTBOUND' ? '#10b981' : '#38bdf8'}`,
                  borderRadius: '6px',
                  padding: '10px 14px',
                  fontSize: '0.82rem'
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <span style={{ fontWeight: 700, color: '#fff' }}>
                      {msg.direction === 'OUTBOUND' ? 'Vendor → ' + (msg.shopkeeper_name || msg.recipient_phone) : (msg.shopkeeper_name || msg.sender_phone) + ' → Vendor'}
                    </span>
                    {msg.reply_link_type === 'EXACT' && (
                      <span style={{ background: 'rgba(16, 185, 129, 0.2)', color: '#34d399', fontSize: '0.64rem', padding: '1px 5px', borderRadius: '3px', fontWeight: 600 }}>
                        Quoted Reply
                      </span>
                    )}
                    {msg.reply_link_type === 'INFERRED' && (
                      <span style={{ background: 'rgba(245, 158, 11, 0.2)', color: '#fbbf24', fontSize: '0.64rem', padding: '1px 5px', borderRadius: '3px', fontWeight: 600 }}>
                        AI Inferred Context
                      </span>
                    )}
                  </div>
                  <span style={{ fontSize: '0.7rem', color: 'var(--text-dim)' }} title={formatDateTime(msg.message_timestamp)}>
                    {formatTime(msg.message_timestamp)}
                  </span>
                </div>

                <p style={{ color: 'var(--text-muted)', fontSize: '0.78rem', marginBottom: '4px', overflow: 'hidden', textOverflow: 'ellipsis', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical' }}>
                  "{msg.message_text}"
                </p>

                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.68rem', color: 'var(--text-dim)' }}>
                  <span>ID: {msg.whatsapp_message_id?.slice(0, 18)}...</span>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '3px', color: msg.delivery_status === 'READ' ? '#53bdeb' : 'inherit' }}>
                    <CheckCheck size={12} /> {msg.delivery_status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
