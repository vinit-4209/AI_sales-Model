import React, { useState, useEffect } from 'react';
import { User, Phone, Mail, ShoppingBag, Tag, Calendar, Search, Sparkles, Loader2, CheckCircle } from 'lucide-react';
import { fetchCustomerApi, fetchLeadsApi } from '../services/api';

export default function SidebarCRM({ customer, recommendations, onCustomerLoaded }) {
  const [phone, setPhone] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [leads, setLeads] = useState([]);

  // Load sample demo leads for 1-click testing
  useEffect(() => {
    fetchLeadsApi()
      .then((data) => {
        if (data && data.leads) {
          setLeads(data.leads.slice(0, 5));
        }
      })
      .catch((err) => console.log('Could not load sample leads:', err));
  }, []);

  const handleFetch = async (targetPhone = phone) => {
    const cleanPhone = (targetPhone || '').trim();
    if (!cleanPhone) {
      setError('Please enter a phone number');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const data = await fetchCustomerApi(cleanPhone);
      onCustomerLoaded(data.customer, data.recommendations);
    } catch (err) {
      setError(err.message || 'Customer not found with this phone number');
      onCustomerLoaded(null, '');
    } finally {
      setLoading(false);
    }
  };

  const handleSelectLead = (lead) => {
    setPhone(lead.phone);
    handleFetch(lead.phone);
  };

  return (
    <aside style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
      {/* CRM Search Card */}
      <div className="glass-card">
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' }}>
          <User size={18} color="#6366f1" />
          <h2 style={{ fontSize: '15px', fontWeight: 700 }}>Customer CRM Profile</h2>
        </div>

        <div style={{ display: 'flex', gap: '8px', marginBottom: '12px' }}>
          <div style={{ position: 'relative', flex: 1 }}>
            <Phone size={14} color="var(--text-muted)" style={{ position: 'absolute', left: '10px', top: '12px' }} />
            <input
              type="text"
              placeholder="+91-9876543210"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleFetch()}
              style={{
                width: '100%',
                padding: '9px 10px 9px 32px',
                background: 'var(--bg-input)',
                border: '1px solid var(--border-subtle)',
                borderRadius: '8px',
                color: 'var(--text-primary)',
                fontSize: '13px',
                outline: 'none'
              }}
            />
          </div>
          <button
            className="btn btn-primary"
            onClick={() => handleFetch()}
            disabled={loading}
            style={{ padding: '8px 14px', fontSize: '13px' }}
          >
            {loading ? <Loader2 size={15} className="pulse-recording" /> : <Search size={15} />}
            Fetch
          </button>
        </div>

        {error && (
          <div style={{
            fontSize: '12px',
            color: '#f87171',
            background: 'rgba(239, 68, 68, 0.1)',
            padding: '8px 10px',
            borderRadius: '8px',
            marginBottom: '10px'
          }}>
            {error}
          </div>
        )}

        {/* Demo Leads Fast Select */}
        {leads.length > 0 && (
          <div>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '6px', fontWeight: 600, textTransform: 'uppercase' }}>
              Quick Demo Contacts:
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
              {leads.map((lead) => (
                <button
                  key={lead.lead_id}
                  onClick={() => handleSelectLead(lead)}
                  style={{
                    background: phone === lead.phone ? 'rgba(99, 102, 241, 0.25)' : 'var(--bg-card-elevated)',
                    border: phone === lead.phone ? '1px solid #6366f1' : '1px solid var(--border-subtle)',
                    color: phone === lead.phone ? '#818cf8' : 'var(--text-secondary)',
                    borderRadius: '6px',
                    padding: '4px 8px',
                    fontSize: '11px',
                    cursor: 'pointer',
                    transition: 'all 0.15s ease'
                  }}
                >
                  {lead.name}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Customer Details Display */}
      {customer && (
        <div className="glass-card" style={{ animation: 'fadeIn 0.3s ease' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
            <h3 style={{ fontSize: '14px', fontWeight: 700, color: 'var(--text-primary)' }}>
              {customer.Name}
            </h3>
            <span style={{ fontSize: '11px', color: '#34d399', display: 'flex', alignItems: 'center', gap: '4px' }}>
              <CheckCircle size={12} /> Verified
            </span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '12px', color: 'var(--text-secondary)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Phone size={13} color="var(--text-muted)" />
              <span>{customer.Phone}</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Mail size={13} color="var(--text-muted)" />
              <span>{customer['Email Id']}</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <ShoppingBag size={13} color="var(--text-muted)" />
              <span style={{ color: 'var(--text-primary)', fontWeight: 500 }}>{customer['Product Name']}</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Tag size={13} color="var(--text-muted)" />
              <span>{customer.Category} (₹{customer['Price (INR)']})</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Calendar size={13} color="var(--text-muted)" />
              <span>Purchased: {customer['Purchase Date']}</span>
            </div>
          </div>
        </div>
      )}

      {/* Product Recommendations & Client AI Summary */}
      {recommendations && (
        <div className="ai-box">
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '8px' }}>
            <Sparkles size={16} color="#a855f7" />
            <h4 style={{ fontSize: '13px', fontWeight: 700, color: '#c084fc' }}>
              AI Cross-Sell Recommendations
            </h4>
          </div>
          <div style={{
            fontSize: '12px',
            color: 'var(--text-primary)',
            lineHeight: 1.5,
            whiteSpace: 'pre-wrap'
          }}>
            {recommendations}
          </div>
        </div>
      )}
    </aside>
  );
}
