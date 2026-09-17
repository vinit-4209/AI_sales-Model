import React from 'react';
import { Mic, Activity, Radio, PhoneCall, Sparkles } from 'lucide-react';

export default function Header({ isRunning, isConnected, callDuration }) {
  const formatDuration = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <header style={{
      background: 'rgba(15, 23, 42, 0.75)',
      backdropFilter: 'blur(12px)',
      borderBottom: '1px solid var(--border-subtle)',
      padding: '16px 28px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      position: 'sticky',
      top: 0,
      zIndex: 50
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
        <div style={{
          width: '42px',
          height: '42px',
          borderRadius: '12px',
          background: 'linear-gradient(135deg, #6366f1, #a855f7)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: '0 4px 12px rgba(99, 102, 241, 0.4)'
        }}>
          <Sparkles size={22} color="#ffffff" />
        </div>
        <div>
          <h1 style={{ fontSize: '18px', fontWeight: 700, letterSpacing: '-0.02em', display: 'flex', alignItems: 'center', gap: '8px' }}>
            AI Sales Copilot
            <span style={{
              fontSize: '11px',
              padding: '2px 8px',
              borderRadius: '20px',
              background: 'rgba(99, 102, 241, 0.2)',
              color: '#818cf8',
              border: '1px solid rgba(99, 102, 241, 0.3)',
              fontWeight: 600
            }}>
              PRO
            </span>
          </h1>
          <p style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
            Real-Time Speech Transcription & Sentiment Analytics
          </p>
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        {/* Call Timer if running */}
        {isRunning && (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            background: 'rgba(239, 68, 68, 0.12)',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            padding: '6px 14px',
            borderRadius: '20px',
            color: '#f87171',
            fontWeight: 600,
            fontSize: '13px'
          }}>
            <span style={{
              width: '8px',
              height: '8px',
              borderRadius: '50%',
              background: '#ef4444',
              display: 'inline-block'
            }} className="pulse-recording" />
            LIVE CALL: {formatDuration(callDuration)}
          </div>
        )}

        {/* Backend & WebSocket Status */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          background: 'var(--bg-card)',
          border: '1px solid var(--border-subtle)',
          padding: '6px 12px',
          borderRadius: '20px',
          fontSize: '12px',
          color: isConnected ? '#34d399' : '#94a3b8'
        }}>
          <Radio size={14} color={isConnected ? '#10b981' : '#64748b'} />
          <span>{isConnected ? 'Server Connected' : 'Connecting...'}</span>
        </div>
      </div>
    </header>
  );
}
