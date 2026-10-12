import React, { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import Navbar from './components/Navbar';
import OverviewDashboard from './views/OverviewDashboard';
import ProductOffersView from './views/ProductOffersView';
import ShopkeepersView from './views/ShopkeepersView';
import SmartMatchingView from './views/SmartMatchingView';
import WhatsAppInboxView from './views/WhatsAppInboxView';
import MessageHistoryView from './views/MessageHistoryView';
import LeadManagementView from './views/LeadManagementView';

import PostOfferModal from './components/PostOfferModal';
import RegisterShopkeeperModal from './components/RegisterShopkeeperModal';
import WebhookConfigModal from './components/WebhookConfigModal';

import { WSClient } from './api';
import { MessageSquare, Bell } from 'lucide-react';

export default function App() {
  const [currentView, setCurrentView] = useState('inbox');
  const [navParams, setNavParams] = useState({});
  const [wsConnected, setWsConnected] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);

  // Modals
  const [isPostOfferOpen, setIsPostOfferOpen] = useState(false);
  const [isRegisterShopkeeperOpen, setIsRegisterShopkeeperOpen] = useState(false);
  const [isWebhookModalOpen, setIsWebhookModalOpen] = useState(false);

  // Live Toast
  const [toast, setToast] = useState(null);

  useEffect(() => {
    // Establish WebSocket connection
    const client = new WSClient((msg) => {
      if (msg.event === 'ws_connected') {
        setWsConnected(msg.data);
      } else if (msg.event === 'incoming_message') {
        setUnreadCount((c) => c + 1);
        setToast({
          title: `WhatsApp Reply from ${msg.data.shopkeeper_name || 'Shopkeeper'}`,
          body: msg.data.message_text,
          convId: msg.data.conversation_id
        });
        setTimeout(() => setToast(null), 6000);
      } else if (msg.event === 'status_updated') {
        console.log('WhatsApp message status updated:', msg.data);
      } else if (msg.event === 'interest_expressed') {
        setToast({
          title: 'New Explicit Interest Registered!',
          body: `${msg.data.shopkeeper_name} (${msg.data.shop_name}) for ${msg.data.product_name}`,
          convId: null
        });
        setTimeout(() => setToast(null), 6000);
      }
    });

    return () => client.disconnect();
  }, []);

  const handleNavigate = (view, params = {}) => {
    setCurrentView(view);
    setNavParams(params);
    if (view === 'inbox') {
      setUnreadCount(0);
    }
  };

  return (
    <div className="app-container">
      {/* Toast Notification */}
      {toast && (
        <div style={{
          position: 'fixed',
          top: '20px',
          right: '24px',
          zIndex: 1000,
          background: '#111b21',
          border: '1px solid #25d366',
          borderRadius: '10px',
          padding: '14px 18px',
          boxShadow: '0 8px 24px rgba(0, 0, 0, 0.6)',
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          maxWidth: '380px',
          animation: 'slideIn 0.25s ease'
        }}>
          <div style={{ background: 'rgba(37, 211, 102, 0.2)', padding: '8px', borderRadius: '50%', color: '#25d366' }}>
            <MessageSquare size={18} />
          </div>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ fontSize: '0.82rem', fontWeight: 700, color: '#fff' }}>{toast.title}</div>
            <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              "{toast.body}"
            </div>
          </div>
          <button
            className="btn btn-whatsapp btn-sm"
            onClick={() => {
              setToast(null);
              handleNavigate('inbox');
            }}
            style={{ fontSize: '0.72rem', padding: '3px 8px' }}
          >
            View
          </button>
        </div>
      )}

      {/* Post Offer Modal */}
      <PostOfferModal
        isOpen={isPostOfferOpen}
        onClose={() => setIsPostOfferOpen(false)}
        onOfferCreated={(newOffer) => {
          handleNavigate('matches', { offerId: newOffer.id });
        }}
      />

      {/* Register Shopkeeper Modal */}
      <RegisterShopkeeperModal
        isOpen={isRegisterShopkeeperOpen}
        onClose={() => setIsRegisterShopkeeperOpen(false)}
        onShopkeeperRegistered={(newSk) => {
          handleNavigate('shopkeepers');
        }}
      />

      {/* Webhook Config Modal */}
      <WebhookConfigModal
        isOpen={isWebhookModalOpen}
        onClose={() => setIsWebhookModalOpen(false)}
        onResetDemoData={() => {
          handleNavigate('dashboard');
        }}
      />

      {/* Left Navigation Sidebar */}
      <Sidebar
        currentView={currentView}
        onNavigate={handleNavigate}
        onOpenWebhookModal={() => setIsWebhookModalOpen(true)}
        unreadCount={unreadCount}
      />

      {/* Main App Workspace */}
      <main className="app-main">
        <Navbar
          currentView={currentView}
          wsConnected={wsConnected}
          onOpenPostOffer={() => setIsPostOfferOpen(true)}
          onOpenWebhookModal={() => setIsWebhookModalOpen(true)}
          onNavigate={handleNavigate}
        />

        {currentView === 'dashboard' && (
          <OverviewDashboard
            onNavigate={handleNavigate}
            onOpenPostOffer={() => setIsPostOfferOpen(true)}
          />
        )}

        {currentView === 'offers' && (
          <ProductOffersView
            onNavigate={handleNavigate}
            onOpenPostOffer={() => setIsPostOfferOpen(true)}
          />
        )}

        {currentView === 'shopkeepers' && (
          <ShopkeepersView
            onNavigate={handleNavigate}
            onOpenRegisterShopkeeper={() => setIsRegisterShopkeeperOpen(true)}
          />
        )}

        {currentView === 'matches' && (
          <SmartMatchingView
            selectedOfferId={navParams.offerId}
            onNavigate={handleNavigate}
          />
        )}

        {currentView === 'inbox' && (
          <WhatsAppInboxView
            initialShopkeeperId={navParams.shopkeeperId}
            initialOfferId={navParams.offerId}
          />
        )}

        {currentView === 'messages' && (
          <MessageHistoryView />
        )}

        {currentView === 'leads' && (
          <LeadManagementView
            onNavigate={handleNavigate}
          />
        )}
      </main>
    </div>
  );
}
