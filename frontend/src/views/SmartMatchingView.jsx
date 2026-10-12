import React, { useEffect, useState } from 'react';
import { 
  Sparkles, HeartHandshake, Phone, MessageSquare, Plus, Package
} from 'lucide-react';
import { fetchApi } from '../api';

export default function SmartMatchingView({ selectedOfferId, onNavigate, onOpenPostOffer }) {
  const [offers, setOffers] = useState([]);
  const [currentOfferId, setCurrentOfferId] = useState(selectedOfferId || null);
  const [matchData, setMatchData] = useState(null);
  const [activeTab, setActiveTab] = useState('interested');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadOffers();
  }, []);

  useEffect(() => {
    if (currentOfferId) {
      loadMatches(currentOfferId);
    }
  }, [currentOfferId]);

  const loadOffers = async () => {
    try {
      const data = await fetchApi('/api/offers');
      setOffers(data);
      if (data.length > 0) {
        const targetId = selectedOfferId || data[0].id;
        setCurrentOfferId(targetId);
      }
    } catch (err) {
      console.error('Failed to load offers:', err);
    }
  };

  const loadMatches = async (offerId) => {
    setLoading(true);
    try {
      const res = await fetchApi(`/api/offers/${offerId}/matches`);
      setMatchData(res);
      if (res.interested_shopkeepers.length === 0 && res.suggested_matches.length > 0) {
        setActiveTab('suggested');
      } else {
        setActiveTab('interested');
      }
    } catch (err) {
      console.error('Failed to load matches:', err);
    } finally {
      setLoading(false);
    }
  };

  const currentOffer = offers.find((o) => o.id === currentOfferId);

  const handleConnectWhatsApp = async (item) => {
    try {
      await fetchApi(`/api/conversations?shopkeeper_id=${item.shopkeeper_id}&product_offer_id=${currentOfferId}`, {
        method: 'POST'
      });
      onNavigate('inbox', { shopkeeperId: item.shopkeeper_id, offerId: currentOfferId });
    } catch (err) {
      onNavigate('inbox', { shopkeeperId: item.shopkeeper_id, offerId: currentOfferId });
    }
  };

  return (
    <div className="page-container" style={{ padding: '20px' }}>
      {/* Offer Cards Selector */}
      <div style={{ marginBottom: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
          <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: '#fff' }}>1. Select Product Offer</h3>
          <button className="btn btn-secondary btn-sm" onClick={onOpenPostOffer} style={{ fontSize: '0.74rem' }}>
            <Plus size={12} /> Post New Offer
          </button>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: '12px' }}>
          {offers.map((offer) => {
            const isSelected = offer.id === currentOfferId;
            return (
              <div
                key={offer.id}
                onClick={() => setCurrentOfferId(offer.id)}
                style={{
                  background: isSelected ? 'rgba(16, 185, 129, 0.12)' : 'var(--bg-card)',
                  border: `1px solid ${isSelected ? '#10b981' : 'var(--border-subtle)'}`,
                  borderRadius: '10px',
                  padding: '14px',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease'
                }}
              >
                <div style={{ fontWeight: 700, fontSize: '0.88rem', color: '#fff', marginBottom: '4px' }}>
                  {offer.product_name}
                </div>
                <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                  Price: <strong style={{ color: '#34d399' }}>₹{offer.selling_price.toFixed(2)}</strong> • Stock: {offer.available_quantity.toLocaleString()} pcs
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Tabs for Interested vs Matches */}
      <div style={{ marginBottom: '12px', display: 'flex', gap: '8px' }}>
        <button
          className={`btn ${activeTab === 'interested' ? 'btn-primary' : 'btn-secondary'}`}
          onClick={() => setActiveTab('interested')}
          style={{ padding: '7px 14px', borderRadius: '18px', fontSize: '0.82rem' }}
        >
          <HeartHandshake size={14} /> Explicit Inquiries ({matchData?.interested_shopkeepers?.length || 0})
        </button>
        <button
          className={`btn ${activeTab === 'suggested' ? 'btn-primary' : 'btn-secondary'}`}
          onClick={() => setActiveTab('suggested')}
          style={{ padding: '7px 14px', borderRadius: '18px', fontSize: '0.82rem' }}
        >
          <Sparkles size={14} /> Suggested Matches ({matchData?.suggested_matches?.length || 0})
        </button>
      </div>

      {/* Matching Table */}
      {loading ? (
        <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>Loading matched shopkeepers...</p>
      ) : (
        (() => {
          const items = activeTab === 'interested' 
            ? matchData?.interested_shopkeepers || []
            : matchData?.suggested_matches || [];

          if (items.length === 0) {
            return (
              <div style={{ textAlign: 'center', padding: '30px', background: 'var(--bg-card)', borderRadius: '10px', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                No shopkeepers found in this section.
              </div>
            );
          }

          return (
            <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: '10px', overflow: 'hidden' }}>
              <table className="custom-table" style={{ fontSize: '0.82rem' }}>
                <thead>
                  <tr>
                    <th>Shopkeeper</th>
                    <th>WhatsApp Phone</th>
                    <th>Required Qty & Target Price</th>
                    <th>Match Reason</th>
                    <th style={{ textAlign: 'right' }}>WhatsApp</th>
                  </tr>
                </thead>
                <tbody>
                  {items.map((item) => (
                    <tr key={item.shopkeeper_id}>
                      <td>
                        <div style={{ fontWeight: 700, color: '#fff' }}>{item.shopkeeper_name}</div>
                        <div style={{ fontSize: '0.74rem', color: '#38bdf8' }}>{item.shop_name} • {item.location}</div>
                      </td>

                      <td>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '4px', color: '#34d399', fontFamily: 'var(--font-mono)' }}>
                          <Phone size={12} />
                          <span>{item.whatsapp_phone}</span>
                        </div>
                      </td>

                      <td>
                        <div>Requires: <strong>{item.required_quantity.toLocaleString()} pcs</strong></div>
                        <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>
                          Budget: <strong style={{ color: '#fbbf24' }}>₹{item.target_price.toFixed(2)}</strong> (Vendor: ₹{item.vendor_price.toFixed(2)})
                        </div>
                      </td>

                      <td>
                        <span style={{ fontSize: '0.74rem', color: item.is_explicitly_interested ? '#fbbf24' : 'var(--text-muted)' }}>
                          {item.match_reasons[0] || 'Compatible product requirement'}
                        </span>
                      </td>

                      <td style={{ textAlign: 'right' }}>
                        <button
                          className="btn btn-whatsapp btn-sm"
                          onClick={() => handleConnectWhatsApp(item)}
                          style={{ padding: '5px 10px', fontSize: '0.76rem' }}
                        >
                          <MessageSquare size={12} /> Chat on WhatsApp
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          );
        })()
      )}
    </div>
  );
}
