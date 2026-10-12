import React, { useState } from 'react';
import { X, Store, AlertCircle } from 'lucide-react';
import { fetchApi } from '../api';

export default function RegisterShopkeeperModal({ isOpen, onClose, onShopkeeperRegistered }) {
  const [formData, setFormData] = useState({
    shopkeeper_name: '',
    shop_name: '',
    whatsapp_phone: '+919064148052',
    location: '',
    preferred_delivery_location: '',
    req_product_name: 'Paper Cups',
    req_category: 'Paper Cups',
    req_quantity: '5000',
    req_target_price: '0.85'
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const payload = {
        shopkeeper_name: formData.shopkeeper_name,
        shop_name: formData.shop_name,
        whatsapp_phone: formData.whatsapp_phone.trim(),
        location: formData.location,
        preferred_delivery_location: formData.preferred_delivery_location || formData.location,
        lead_status: 'INTERESTED',
        requirements: [
          {
            product_name: formData.req_product_name,
            category: formData.req_category,
            required_quantity: parseInt(formData.req_quantity, 10),
            target_price: parseFloat(formData.req_target_price),
            delivery_location: formData.preferred_delivery_location || formData.location
          }
        ]
      };

      const newShopkeeper = await fetchApi('/api/shopkeepers', {
        method: 'POST',
        body: JSON.stringify(payload)
      });

      if (onShopkeeperRegistered) onShopkeeperRegistered(newShopkeeper);
      onClose();
    } catch (err) {
      setError(err.message || 'Failed to register shopkeeper');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay">
      <div className="modal-content" style={{ maxWidth: '600px' }}>
        <div className="modal-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{ background: 'rgba(59, 130, 246, 0.15)', padding: '8px', borderRadius: '8px', color: '#60a5fa' }}>
              <Store size={20} />
            </div>
            <div>
              <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#fff' }}>Register New Shopkeeper</h3>
              <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Add retail shopkeeper and their packaging requirements</p>
            </div>
          </div>
          <button onClick={onClose} style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}>
            <X size={20} />
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="modal-body" style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            {error && (
              <div style={{ background: 'rgba(244, 63, 94, 0.15)', border: '1px solid rgba(244, 63, 94, 0.3)', padding: '10px 14px', borderRadius: '8px', color: '#fb7185', fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <AlertCircle size={16} />
                <span>{error}</span>
              </div>
            )}

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
              <div className="form-group" style={{ marginBottom: 0 }}>
                <label>Shopkeeper Name *</label>
                <input
                  type="text"
                  className="form-control"
                  placeholder="e.g. Rahul Sharma"
                  value={formData.shopkeeper_name}
                  onChange={(e) => setFormData({ ...formData, shopkeeper_name: e.target.value })}
                  required
                />
              </div>

              <div className="form-group" style={{ marginBottom: 0 }}>
                <label>Shop / Outlet Name *</label>
                <input
                  type="text"
                  className="form-control"
                  placeholder="e.g. Chai Junction"
                  value={formData.shop_name}
                  onChange={(e) => setFormData({ ...formData, shop_name: e.target.value })}
                  required
                />
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
              <div className="form-group" style={{ marginBottom: 0 }}>
                <label>WhatsApp Phone Number *</label>
                <input
                  type="text"
                  className="form-control"
                  placeholder="+9198XXXXXXXX"
                  value={formData.whatsapp_phone}
                  onChange={(e) => setFormData({ ...formData, whatsapp_phone: e.target.value })}
                  required
                />
              </div>

              <div className="form-group" style={{ marginBottom: 0 }}>
                <label>City & Location *</label>
                <input
                  type="text"
                  className="form-control"
                  placeholder="e.g. South Delhi"
                  value={formData.location}
                  onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                  required
                />
              </div>
            </div>

            <div style={{ padding: '12px', background: 'rgba(255, 255, 255, 0.03)', borderRadius: '8px', border: '1px dashed var(--border-light)' }}>
              <h4 style={{ fontSize: '0.82rem', fontWeight: 700, color: '#38bdf8', marginBottom: '10px' }}>Primary Purchasing Requirement</h4>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', marginBottom: '10px' }}>
                <div>
                  <label style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>Required Product</label>
                  <input
                    type="text"
                    className="form-control"
                    placeholder="e.g. 250ml Ripple Paper Cups"
                    value={formData.req_product_name}
                    onChange={(e) => setFormData({ ...formData, req_product_name: e.target.value })}
                    required
                  />
                </div>
                <div>
                  <label style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>Category</label>
                  <select
                    className="form-control"
                    value={formData.req_category}
                    onChange={(e) => setFormData({ ...formData, req_category: e.target.value })}
                  >
                    <option value="Paper Cups">Paper Cups</option>
                    <option value="Takeaway Containers">Takeaway Containers</option>
                    <option value="Paper Bags">Paper Bags</option>
                    <option value="Meal Trays">Meal Trays</option>
                  </select>
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                <div>
                  <label style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>Required Quantity (units)</label>
                  <input
                    type="number"
                    className="form-control"
                    value={formData.req_quantity}
                    onChange={(e) => setFormData({ ...formData, req_quantity: e.target.value })}
                    required
                  />
                </div>
                <div>
                  <label style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>Target Budget (₹/unit)</label>
                  <input
                    type="number"
                    step="0.01"
                    className="form-control"
                    value={formData.req_target_price}
                    onChange={(e) => setFormData({ ...formData, req_target_price: e.target.value })}
                    required
                  />
                </div>
              </div>
            </div>
          </div>

          <div className="modal-footer">
            <button type="button" className="btn btn-secondary" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? 'Registering...' : 'Register Shopkeeper'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
