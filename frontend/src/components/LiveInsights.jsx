import React, { useState } from 'react';
import { Smile, Meh, Frown, Sparkles, Copy, Check, MessageSquareText } from 'lucide-react';

export default function LiveInsights({ sentiment, summary, suggestion }) {
  const [copied, setCopied] = useState(false);

  const cleanSentiment = (sentiment || 'neutral').toLowerCase();
  let sentClass = 'sentiment-neutral';
  let Icon = Meh;
  let label = 'NEUTRAL';
  let emoji = '😐';

  if (cleanSentiment.includes('positive')) {
    sentClass = 'sentiment-positive';
    Icon = Smile;
    label = 'POSITIVE';
    emoji = '🙂';
  } else if (cleanSentiment.includes('negative')) {
    sentClass = 'sentiment-negative';
    Icon = Frown;
    label = 'NEGATIVE';
    emoji = '🙁';
  }

  const handleCopy = () => {
    if (suggestion) {
      navigator.clipboard.writeText(suggestion);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px', marginBottom: '20px' }}>
      {/* Real-time Sentiment & Customer Summary */}
      <div className={`glass-card ${sentClass}`} style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
            <span style={{ fontSize: '11px', fontWeight: 700, letterSpacing: '0.05em', textTransform: 'uppercase' }}>
              Real-Time Customer Sentiment
            </span>
            <span style={{
              fontSize: '11px',
              fontWeight: 700,
              padding: '2px 8px',
              borderRadius: '12px',
              background: 'rgba(255, 255, 255, 0.1)',
              display: 'flex',
              alignItems: 'center',
              gap: '4px'
            }}>
              <Icon size={13} /> {label} {emoji}
            </span>
          </div>

          <h3 style={{ fontSize: '18px', fontWeight: 700, marginBottom: '6px' }}>
            {sentiment || 'Neutral'}
          </h3>

          <div style={{ fontSize: '13px', color: 'var(--text-primary)', marginTop: '8px', lineHeight: 1.4 }}>
            <strong>Customer Need: </strong>
            <span>{summary || 'Listening for customer statement...'}</span>
          </div>
        </div>
      </div>

      {/* AI Recommendation for Sales Rep */}
      <div className="ai-box" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Sparkles size={16} color="#c084fc" />
              <span style={{ fontSize: '12px', fontWeight: 700, color: '#c084fc', textTransform: 'uppercase' }}>
                AI Recommendation for Sales Rep
              </span>
            </div>
            {suggestion && (
              <button
                onClick={handleCopy}
                title="Copy suggested response"
                style={{
                  background: 'rgba(255, 255, 255, 0.08)',
                  border: '1px solid rgba(255, 255, 255, 0.15)',
                  borderRadius: '6px',
                  padding: '4px 8px',
                  color: 'var(--text-primary)',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px',
                  fontSize: '11px'
                }}
              >
                {copied ? <Check size={12} color="#34d399" /> : <Copy size={12} />}
                {copied ? 'Copied' : 'Copy'}
              </button>
            )}
          </div>

          <p style={{
            fontSize: '14px',
            fontWeight: 500,
            color: '#f8fafc',
            lineHeight: 1.5
          }}>
            {suggestion || 'Waiting for customer speech to suggest real-time action...'}
          </p>
        </div>
      </div>
    </div>
  );
}
