const API_BASE = '/api';

export async function fetchHealth() {
  try {
    const res = await fetch(`${API_BASE}/health`);
    return await res.json();
  } catch (err) {
    console.error('Failed to fetch health:', err);
    return { status: 'error', is_running: false };
  }
}

export async function startCallApi() {
  const res = await fetch(`${API_BASE}/call/start`, { method: 'POST' });
  return await res.json();
}

export async function stopCallApi() {
  const res = await fetch(`${API_BASE}/call/stop`, { method: 'POST' });
  return await res.json();
}

export async function getCallStatusApi() {
  const res = await fetch(`${API_BASE}/call/status`);
  return await res.json();
}

export async function getTranscriptApi() {
  const res = await fetch(`${API_BASE}/call/transcript`);
  return await res.json();
}

export async function getSummaryApi() {
  const res = await fetch(`${API_BASE}/call/summary`);
  return await res.json();
}

export async function fetchLeadsApi() {
  const res = await fetch(`${API_BASE}/crm/leads`);
  return await res.json();
}

export async function fetchCustomerApi(phone) {
  const res = await fetch(`${API_BASE}/crm/customer?phone=${encodeURIComponent(phone)}`);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Customer not found' }));
    throw new Error(err.detail || 'Customer not found');
  }
  return await res.json();
}
