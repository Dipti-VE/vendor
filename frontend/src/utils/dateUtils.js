/**
 * Date and time formatting utilities with strict UTC normalization.
 * Ensures timestamps stored in UTC in PostgreSQL are rendered in the client's local timezone (e.g. IST).
 */

export function parseUtcDate(raw) {
  if (!raw) return null;
  if (raw instanceof Date) return isNaN(raw.getTime()) ? null : raw;
  
  let str = String(raw).trim();
  if (!str) return null;

  // Convert space-separated format (e.g., '2026-10-12 12:10:44') to ISO 'T'
  if (str.includes(' ') && !str.includes('T')) {
    str = str.replace(' ', 'T');
  }

  // Check if timezone indicator already exists
  const hasTimezone = str.endsWith('Z') || str.includes('+') || (str.indexOf('T') !== -1 && str.lastIndexOf('-') > str.indexOf('T'));
  const utcStr = hasTimezone ? str : `${str}Z`;
  
  const date = new Date(utcStr);
  return isNaN(date.getTime()) ? null : date;
}

export function formatTime(raw, options = {}) {
  const date = parseUtcDate(raw);
  if (!date) return '';
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', ...options });
}

export function formatDate(raw) {
  const date = parseUtcDate(raw);
  if (!date) return '';
  return date.toLocaleDateString([], { month: 'short', day: 'numeric', year: 'numeric' });
}

export function formatDateTime(raw) {
  const date = parseUtcDate(raw);
  if (!date) return '';
  return date.toLocaleDateString([], { month: 'short', day: 'numeric' }) + ', ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}
