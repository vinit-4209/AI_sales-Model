import React from 'react';
import { Mic, Square, Loader2, Volume2, AlertCircle } from 'lucide-react';

export default function CallControls({
  isRunning,
  isProcessing,
  volume,
  onStartCall,
  onStopCall,
  statusMessage
}) {
  // Generate visualizer bars based on live volume
  const numBars = 16;
  const bars = Array.from({ length: numBars }, (_, i) => {
    // vary bar heights slightly for visual rhythm
    const factor = Math.sin((i / numBars) * Math.PI);
    const height = isRunning
      ? Math.max(4, Math.min(24, Math.round(volume * 24 * (0.6 + 0.8 * factor))))
      : 4;
    return height;
  });

  return (
    <div className="glass-card" style={{ marginBottom: '20px' }}>
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '16px'
      }}>
        {/* Call Action Button */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          {!isRunning ? (
            <button
              className="btn btn-success"
              onClick={onStartCall}
              disabled={isProcessing}
              style={{ padding: '12px 24px', fontSize: '15px' }}
            >
              {isProcessing ? (
                <Loader2 size={18} className="pulse-recording" />
              ) : (
                <Mic size={18} />
              )}
              Start Sales Call
            </button>
          ) : (
            <button
              className="btn btn-danger"
              onClick={onStopCall}
              disabled={isProcessing}
              style={{ padding: '12px 24px', fontSize: '15px' }}
            >
              {isProcessing ? (
                <Loader2 size={18} className="pulse-recording" />
              ) : (
                <Square size={18} fill="#ffffff" />
              )}
              End Call & Analyze
            </button>
          )}

          {/* Status badge */}
          <div style={{
            fontSize: '13px',
            color: isRunning ? '#34d399' : 'var(--text-secondary)',
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}>
            <span style={{
              width: '8px',
              height: '8px',
              borderRadius: '50%',
              background: isRunning ? '#10b981' : '#64748b',
              display: 'inline-block'
            }} className={isRunning ? 'pulse-recording' : ''} />
            <span>
              {isProcessing
                ? 'Processing Whisper & AI...'
                : isRunning
                ? 'Listening to microphone...'
                : 'Ready to start call'}
            </span>
          </div>
        </div>

        {/* Audio Visualizer */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          background: 'var(--bg-input)',
          padding: '8px 16px',
          borderRadius: '10px',
          border: '1px solid var(--border-subtle)'
        }}>
          <Volume2 size={16} color={isRunning ? '#10b981' : 'var(--text-muted)'} />
          <div className="visualizer-container">
            {bars.map((height, idx) => (
              <div
                key={idx}
                className="visualizer-bar"
                style={{
                  height: `${height}px`,
                  background: isRunning
                    ? height > 16
                      ? '#ef4444'
                      : height > 10
                      ? '#f59e0b'
                      : '#10b981'
                    : 'rgba(255, 255, 255, 0.15)'
                }}
              />
            ))}
          </div>
          <span style={{ fontSize: '11px', color: 'var(--text-muted)', minWidth: '40px' }}>
            {isRunning ? `${Math.round(volume * 100)}%` : 'Muted'}
          </span>
        </div>
      </div>

      {statusMessage && (
        <div style={{
          marginTop: '12px',
          fontSize: '12px',
          color: '#fbbf24',
          display: 'flex',
          alignItems: 'center',
          gap: '6px'
        }}>
          <AlertCircle size={14} />
          <span>{statusMessage}</span>
        </div>
      )}
    </div>
  );
}
