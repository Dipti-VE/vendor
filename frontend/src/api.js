// Centralized API Client

const BASE_URL = import.meta.env.VITE_API_URL || '';

export async function fetchApi(endpoint, options = {}) {
  const url = `${BASE_URL}${endpoint}`;
  const config = {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  };

  try {
    const res = await fetch(url, config);
    if (!res.ok) {
      const errorData = await res.json().catch(() => ({}));
      throw new Error(errorData.detail || `HTTP Error ${res.status}: ${res.statusText}`);
    }
    return await res.json();
  } catch (err) {
    console.error(`API Error on ${endpoint}:`, err);
    throw err;
  }
}

// WebSocket Manager
export class WSClient {
  constructor(onMessage) {
    this.onMessage = onMessage;
    this.ws = null;
    this.reconnectTimer = null;
    this.connect();
  }

  connect() {
    let wsUrl = import.meta.env.VITE_WS_URL;
    if (!wsUrl && BASE_URL) {
      const wsProtocol = BASE_URL.startsWith('https') ? 'wss:' : 'ws:';
      const hostOnly = BASE_URL.replace(/^https?:\/\//, '').replace(/\/$/, '');
      wsUrl = `${wsProtocol}//${hostOnly}/ws`;
    } else if (!wsUrl) {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      wsUrl = `${protocol}//${window.location.host}/ws`;
    }

    try {
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        console.log('Connected to Real-time WebSocket');
        if (this.onMessage) this.onMessage({ event: 'ws_connected', data: true });
      };

      this.ws.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          if (this.onMessage) this.onMessage(payload);
        } catch (e) {
          // ignore pong
        }
      };

      this.ws.onclose = () => {
        console.log('WebSocket closed. Reconnecting in 3s...');
        if (this.onMessage) this.onMessage({ event: 'ws_connected', data: false });
        this.reconnectTimer = setTimeout(() => this.connect(), 3000);
      };

      this.ws.onerror = (err) => {
        console.warn('WebSocket error:', err);
      };
    } catch (e) {
      console.error('Failed to create WebSocket:', e);
    }
  }

  disconnect() {
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
    if (this.ws) this.ws.close();
  }
}
