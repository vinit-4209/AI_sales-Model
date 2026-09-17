import React, { useRef, useEffect } from 'react';
import { MessageSquare, Clock, VolumeX } from 'lucide-react';

export default function LiveTranscript({ utterances, rawTranscript, isRunning }) {
  const containerRef = useRef(null);

  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [utterances, rawTranscript]);

  const hasContent = (utterances && utterances.length > 0) || Boolean(rawTranscript);

  return (
    <div className="glass-card" style={{ marginBottom: '20px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <MessageSquare size={18} color="#6366f1" />
          <h2 style={{ fontSize: '15px', fontWeight: 700 }}>Live Speech Transcript</h2>
        </div>
        {isRunning && (
          <span style={{ fontSize: '12px', color: '#34d399', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#10b981' }} className="pulse-recording" />
            Transcribing Live
          </span>
        )}
      </div>

      <div
        ref={containerRef}
        style={{
          background: 'var(--bg-input)',
          border: '1px solid var(--border-subtle)',
          borderRadius: '12px',
          padding: '16px',
          maxHeight: '260px',
          minHeight: '140px',
          overflowY: 'auto',
          display: 'flex',
          flexDirection: 'column',
          gap: '12px'
        }}
      >
        {!hasContent ? (
          <div style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            height: '120px',
            color: 'var(--text-muted)',
            gap: '8px',
            fontSize: '13px'
          }}>
            <VolumeX size={24} />
            <span>{isRunning ? 'Waiting for voice activity...' : 'Start a call to begin live transcription.'}</span>
          </div>
        ) : utterances && utterances.length > 0 ? (
          utterances.map((item, index) => (
            <div
              key={index}
              style={{
                background: 'var(--bg-card-elevated)',
                border: '1px solid var(--border-subtle)',
                borderRadius: '10px',
                padding: '12px',
                display: 'flex',
                flexDirection: 'column',
                gap: '6px'
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <span style={{ fontSize: '11px', color: '#818cf8', fontWeight: 600 }}>
                  Customer
                </span>
                {item.timestamp && (
                  <span style={{ fontSize: '11px', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <Clock size={11} />
                    {new Date(item.timestamp).toLocaleTimeString()}
                  </span>
                )}
              </div>
              <p style={{ fontSize: '13px', color: 'var(--text-primary)', lineHeight: 1.4 }}>
                {item.transcript}
              </p>
              {item.suggestion && (
                <div style={{
                  fontSize: '11px',
                  color: '#c084fc',
                  background: 'rgba(168, 85, 247, 0.1)',
                  border: '1px solid rgba(168, 85, 247, 0.2)',
                  borderRadius: '6px',
                  padding: '4px 8px',
                  marginTop: '4px'
                }}>
                  💡 <strong>Suggested response:</strong> {item.suggestion}
                </div>
              )}
            </div>
          ))
        ) : (
          <div style={{ whiteSpace: 'pre-wrap', fontSize: '13px', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
            {rawTranscript}
          </div>
        )}
      </div>
    </div>
  );
}
