import React, { useState } from 'react';
import { X, Package, Check, AlertCircle } from 'lucide-react';
import { fetchApi } from '../api';

export default function PostOfferModal({ isOpen, onClose, onOfferCreated }) {
  const [formData, setFormData] = useState({
    product_name: '',
    category: 'Paper Cups',
    description: '',
    selling_price: '',
    available_quantity: '',
    minimum_order_quantity: '500',
    location: 'New Delhi',
    delivery_locations: 'Delhi NCR, Pan India, Mumbai, Bengaluru',
    status: 'ACTIVE'
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  if (!isOpen) return null;

  const categories = [
    'Paper Cups',
    'Takeaway Containers',
    'Paper Bags',
    'Meal Trays',
    'Pizza & Burger Boxes',
    'Foil & Cling Wraps',
    'Eco-Cutlery'
  ];

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const payload = {
        ...formData,
        selling_price: parseFloat(formData.selling_price),
        available_quantity: parseInt(formData.available_quantity, 10),
        minimum_order_quantity: parseInt(formData.minimum_order_quantity, 10)
      };

      const newOffer = await fetchApi('/api/offers', {
        method: 'POST',
        body: JSON.stringify(payload)
      });

      if (onOfferCreated) onOfferCreated(newOffer);
      onClose();
    } catch (err) {
      setError(err.message || 'Failed to publish offer');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay">
      <div className="modal-content" style={{ maxWidth: '640px' }}>
        <div className="modal-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{ background: 'rgba(16, 185, 129, 0.15)', padding: '8px', borderRadius: '8px', color: '#10b981' }}>
              <Package size={20} />
            </div>
            <div>
              <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#fff' }}>Post a Product Offer</h3>
              <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Publish your packaging offer and find matching shopkeepers</p>
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

            <div className="form-group" style={{ marginBottom: 0 }}>
              <label>Product Name *</label>
              <input
                type="text"
                className="form-control"
                placeholder="e.g. 250ml Ripple Wall Insulated Paper Cups"
                value={formData.product_name}
                onChange={(e) => setFormData({ ...formData, product_name: e.target.value })}
                required
              />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
              <div className="form-group" style={{ marginBottom: 0 }}>
                <label>Category *</label>
                <select
                  className="form-control"
                  value={formData.category}
                  onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                  required
                >
                  {categories.map((c) => (
                    <option key={c} value={c}>{c}</option>
                  ))}
                </select>
              </div>

              <div className="form-group" style={{ marginBottom: 0 }}>
                <label>Selling Price per Unit (₹) *</label>
                <input
                  type="number"
                  step="0.01"
                  className="form-control"
                  placeholder="e.g. 0.80"
                  value={formData.selling_price}
                  onChange={(e) => setFormData({ ...formData, selling_price: e.target.value })}
                  required
                />
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
              <div className="form-group" style={{ marginBottom: 0 }}>
                <label>Available Stock (Units) *</label>
                <input
                  type="number"
                  className="form-control"
                  placeholder="e.g. 10000"
                  value={formData.available_quantity}
                  onChange={(e) => setFormData({ ...formData, available_quantity: e.target.value })}
                  required
                />
              </div>

              <div className="form-group" style={{ marginBottom: 0 }}>
                <label>Minimum Order Quantity (MOQ) *</label>
                <input
                  type="number"
                  className="form-control"
                  placeholder="e.g. 500"
                  value={formData.minimum_order_quantity}
                  onChange={(e) => setFormData({ ...formData, minimum_order_quantity: e.target.value })}
                  required
                />
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
              <div className="form-group" style={{ marginBottom: 0 }}>
                <label>Product Warehouse / Location *</label>
                <input
                  type="text"
                  className="form-control"
                  placeholder="e.g. New Delhi"
                  value={formData.location}
                  onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                  required
                />
              </div>

              <div className="form-group" style={{ marginBottom: 0 }}>
                <label>Delivery Areas *</label>
                <input
                  type="text"
                  className="form-control"
                  placeholder="e.g. Delhi NCR, Pan India, Mumbai"
                  value={formData.delivery_locations}
                  onChange={(e) => setFormData({ ...formData, delivery_locations: e.target.value })}
                  required
                />
              </div>
            </div>

            <div className="form-group" style={{ marginBottom: 0 }}>
              <label>Description & Specifications</label>
              <textarea
                className="form-control"
                rows="2"
                placeholder="Details on material GSM, food-grade certification, thermal insulation..."
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              />
            </div>
          </div>

          <div className="modal-footer">
            <button type="button" className="btn btn-secondary" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? 'Publishing...' : 'Publish Product Offer'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
