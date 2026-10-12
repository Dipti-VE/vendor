import React, { useEffect, useState } from 'react';
import { Package, Plus, Sparkles, HeartHandshake, MapPin, Truck, Pause, Play, Eye } from 'lucide-react';
import { fetchApi } from '../api';

export default function ProductOffersView({ onNavigate, onOpenPostOffer }) {
  const [offers, setOffers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [categoryFilter, setCategoryFilter] = useState('ALL');

  useEffect(() => {
    loadOffers();
  }, [categoryFilter]);

  const loadOffers = async () => {
    setLoading(true);
    try {
      const url = categoryFilter === 'ALL' ? '/api/offers' : `/api/offers?category=${encodeURIComponent(categoryFilter)}`;
      const data = await fetchApi(url);
      setOffers(data);
    } catch (err) {
      console.error('Failed to load offers:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleToggleStatus = async (offer) => {
    const newStatus = offer.status === 'ACTIVE' ? 'PAUSED' : 'ACTIVE';
    try {
      await fetchApi(`/api/offers/${offer.id}`, {
        method: 'PATCH',
        body: JSON.stringify({ status: newStatus })
      });
      loadOffers();
    } catch (err) {
      alert('Error updating offer status: ' + err.message);
    }
  };

  const categories = ['ALL', 'Paper Cups', 'Takeaway Containers', 'Paper Bags', 'Meal Trays'];

  return (
    <div className="page-container">
      {/* Header Bar */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <h2 style={{ fontSize: '1.3rem', fontWeight: 800, color: '#fff' }}>Vendor Product Offers</h2>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Manage wholesale packaging supplies and discover shopkeepers</p>
        </div>

        <div style={{ display: 'flex', gap: '10px' }}>
          <button className="btn btn-primary" onClick={onOpenPostOffer}>
            <Plus size={16} /> Post a Product Offer
          </button>
        </div>
      </div>

      {/* Category Pills Filter */}
      <div style={{ display: 'flex', gap: '8px', marginBottom: '20px', flexWrap: 'wrap' }}>
        {categories.map((cat) => (
          <button
            key={cat}
            className={`btn btn-sm ${categoryFilter === cat ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setCategoryFilter(cat)}
            style={{ borderRadius: '20px', padding: '6px 14px' }}
          >
            {cat}
          </button>
        ))}
      </div>

      {/* Offer Cards Grid */}
      {loading ? (
        <p style={{ color: 'var(--text-muted)' }}>Loading product offers...</p>
      ) : offers.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '40px', background: 'var(--bg-card)', borderRadius: 'var(--radius-lg)' }}>
          <Package size={48} color="var(--text-dim)" style={{ marginBottom: '12px' }} />
          <h3 style={{ color: '#fff', marginBottom: '6px' }}>No Product Offers Found</h3>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginBottom: '16px' }}>Post your first packaging offer to find retail buyers</p>
          <button className="btn btn-primary" onClick={onOpenPostOffer}>
            <Plus size={16} /> Post Offer Now
          </button>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(360px, 1fr))', gap: '18px' }}>
          {offers.map((offer) => (
            <div
              key={offer.id}
              style={{
                background: 'var(--bg-card)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-lg)',
                padding: '20px',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                transition: 'all 0.15s ease'
              }}
            >
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '10px' }}>
                  <div>
                    <span style={{ fontSize: '0.72rem', fontWeight: 600, color: '#38bdf8', background: 'rgba(56, 189, 248, 0.1)', padding: '2px 8px', borderRadius: '4px' }}>
                      {offer.category}
                    </span>
                    <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#fff', marginTop: '6px' }}>
                      {offer.product_name}
                    </h3>
                  </div>
                  <span style={{
                    fontSize: '0.72rem',
                    fontWeight: 700,
                    padding: '3px 8px',
                    borderRadius: '6px',
                    background: offer.status === 'ACTIVE' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(244, 63, 94, 0.15)',
                    color: offer.status === 'ACTIVE' ? '#34d399' : '#fb7185',
                    border: `1px solid ${offer.status === 'ACTIVE' ? 'rgba(16, 185, 129, 0.3)' : 'rgba(244, 63, 94, 0.3)'}`
                  }}>
                    {offer.status}
                  </span>
                </div>

                <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '14px', lineHeight: '1.45' }}>
                  {offer.description || 'Packaging supplies manufactured with premium quality materials.'}
                </p>

                {/* Price and Stock specs */}
                <div style={{ background: 'rgba(0, 0, 0, 0.25)', borderRadius: '8px', padding: '12px', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', marginBottom: '14px' }}>
                  <div>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)' }}>Selling Price</div>
                    <div style={{ fontSize: '1.2rem', fontWeight: 800, color: '#34d399' }}>
                      ₹{offer.selling_price.toFixed(2)}
                      <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontWeight: 400 }}> /unit</span>
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)' }}>Available Stock</div>
                    <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#fff' }}>
                      {offer.available_quantity.toLocaleString()}
                      <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontWeight: 400 }}> pcs</span>
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)' }}>Minimum Order (MOQ)</div>
                    <div style={{ fontSize: '0.85rem', fontWeight: 600, color: '#e2e8f0' }}>
                      {offer.minimum_order_quantity.toLocaleString()} units
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)' }}>Warehouse Location</div>
                    <div style={{ fontSize: '0.85rem', fontWeight: 600, color: '#e2e8f0', display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <MapPin size={12} color="#f59e0b" /> {offer.location}
                    </div>
                  </div>
                </div>

                <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '16px' }}>
                  <Truck size={14} color="#38bdf8" />
                  <span>Delivers to: <strong>{offer.delivery_locations}</strong></span>
                </div>
              </div>

              {/* Bottom Matching stats and actions */}
              <div style={{ borderTop: '1px solid var(--border-subtle)', paddingTop: '14px' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', background: 'rgba(245, 158, 11, 0.15)', color: '#fbbf24', padding: '3px 8px', borderRadius: '4px', fontSize: '0.72rem', fontWeight: 700 }}>
                      <HeartHandshake size={12} /> {offer.interested_count} Explicitly Interested
                    </span>
                    <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', background: 'rgba(59, 130, 246, 0.15)', color: '#60a5fa', padding: '3px 8px', borderRadius: '4px', fontSize: '0.72rem', fontWeight: 700 }}>
                      <Sparkles size={12} /> {offer.suggested_matches_count} Suggested
                    </span>
                  </div>

                  <button
                    onClick={() => handleToggleStatus(offer)}
                    style={{ background: 'transparent', border: 'none', color: 'var(--text-dim)', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.72rem' }}
                    title={offer.status === 'ACTIVE' ? 'Pause Offer' : 'Activate Offer'}
                  >
                    {offer.status === 'ACTIVE' ? <Pause size={14} /> : <Play size={14} />}
                    {offer.status === 'ACTIVE' ? 'Pause' : 'Activate'}
                  </button>
                </div>

                <button
                  className="btn btn-primary"
                  style={{ width: '100%', fontSize: '0.84rem' }}
                  onClick={() => onNavigate('matches', { offerId: offer.id })}
                >
                  <Eye size={14} /> View Matches & Interested Shopkeepers
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
