import React, { useEffect, useState } from 'react';
import { Users, Phone, MapPin, Plus, MessageSquare, Search } from 'lucide-react';
import { fetchApi } from '../api';

export default function ShopkeepersView({ onNavigate, onOpenRegisterShopkeeper }) {
  const [shopkeepers, setShopkeepers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    loadShopkeepers();
  }, []);

  const loadShopkeepers = async () => {
    setLoading(true);
    try {
      const data = await fetchApi('/api/shopkeepers');
      setShopkeepers(data);
    } catch (err) {
      console.error('Failed to load shopkeepers:', err);
    } finally {
      setLoading(false);
    }
  };

  const filteredShopkeepers = shopkeepers.filter((sk) => {
    const q = searchQuery.toLowerCase();
    return (
      sk.shopkeeper_name.toLowerCase().includes(q) ||
      sk.shop_name.toLowerCase().includes(q) ||
      sk.location.toLowerCase().includes(q)
    );
  });

  return (
    <div className="page-container" style={{ padding: '20px' }}>
      {/* Top Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px', flexWrap: 'wrap', gap: '10px' }}>
        <div style={{ maxWidth: '320px', flex: 1 }}>
          <div className="search-input-wrapper">
            <Search size={14} />
            <input
              type="text"
              className="search-input"
              placeholder="Search shopkeepers..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{ padding: '8px 12px 8px 34px', fontSize: '0.82rem' }}
            />
          </div>
        </div>

        <button className="btn btn-primary btn-sm" onClick={onOpenRegisterShopkeeper} style={{ padding: '7px 14px', fontSize: '0.8rem' }}>
          <Plus size={14} /> Add Shopkeeper
        </button>
      </div>

      {/* Shopkeepers Table */}
      {loading ? (
        <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>Loading shopkeepers...</p>
      ) : filteredShopkeepers.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '30px', background: 'var(--bg-card)', borderRadius: '10px', color: 'var(--text-muted)' }}>
          No shopkeepers found.
        </div>
      ) : (
        <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: '10px', overflow: 'hidden' }}>
          <table className="custom-table" style={{ fontSize: '0.82rem' }}>
            <thead>
              <tr>
                <th>Shopkeeper & Store</th>
                <th>WhatsApp Phone</th>
                <th>Location</th>
                <th>Requirement & Target Price</th>
                <th style={{ textAlign: 'right' }}>WhatsApp</th>
              </tr>
            </thead>
            <tbody>
              {filteredShopkeepers.map((sk) => (
                <tr key={sk.id}>
                  <td>
                    <div style={{ fontWeight: 700, color: '#fff' }}>{sk.shopkeeper_name}</div>
                    <div style={{ fontSize: '0.74rem', color: '#38bdf8' }}>{sk.shop_name}</div>
                  </td>

                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '5px', fontFamily: 'var(--font-mono)', color: '#34d399' }}>
                      <Phone size={12} />
                      <span>{sk.whatsapp_phone}</span>
                    </div>
                  </td>

                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '4px', color: 'var(--text-muted)', fontSize: '0.78rem' }}>
                      <MapPin size={12} color="#f59e0b" />
                      <span>{sk.location}</span>
                    </div>
                  </td>

                  <td>
                    {sk.requirements && sk.requirements.length > 0 ? (
                      <div style={{ fontSize: '0.76rem' }}>
                        {sk.requirements[0].product_name} ({sk.requirements[0].required_quantity.toLocaleString()} pcs @ <strong style={{ color: '#34d399' }}>₹{sk.requirements[0].target_price.toFixed(2)}</strong>)
                      </div>
                    ) : (
                      <span style={{ color: 'var(--text-dim)', fontSize: '0.74rem' }}>General inquiry</span>
                    )}
                  </td>

                  <td style={{ textAlign: 'right' }}>
                    <button
                      className="btn btn-whatsapp btn-sm"
                      onClick={() => onNavigate('inbox', { shopkeeperId: sk.id })}
                      style={{ padding: '5px 10px', fontSize: '0.76rem' }}
                    >
                      <MessageSquare size={12} /> Message
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
