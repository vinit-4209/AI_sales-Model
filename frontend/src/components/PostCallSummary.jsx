import React, { useState } from 'react';
import {
  FileText,
  RotateCw,
  Award,
  AlertTriangle,
  CheckCircle2,
  ListTodo,
  TrendingUp,
  Target,
  ChevronDown,
  ChevronUp,
  Smile,
  Meh,
  Frown
} from 'lucide-react';

export default function PostCallSummary({ summaryData, onRefresh }) {
  const [showFullTranscript, setShowFullTranscript] = useState(false);

  if (!summaryData) {
    return (
      <div className="glass-card" style={{ textAlign: 'center', padding: '36px 20px', color: 'var(--text-muted)' }}>
        <FileText size={32} style={{ margin: '0 auto 12px', opacity: 0.5 }} />
        <h3 style={{ fontSize: '15px', fontWeight: 600, color: 'var(--text-secondary)' }}>
          No Post-Call Summary Available
        </h3>
        <p style={{ fontSize: '13px', marginTop: '6px' }}>
          After you end a call, Whisper and Groq AI will generate an executive scorecard and analytical summary here.
        </p>
      </div>
    );
  }

  const sentiment = (summaryData.sentiment || 'neutral').toLowerCase();
  const summary = summaryData.summary || 'Summary not available';
  const transcript = summaryData.transcript || '';
  const structured = summaryData.structured || {};

  const intent = structured.customer_intent || '';
  const topics = structured.key_topics || [];
  const objections = structured.objections || [];
  const resolutions = structured.resolutions || [];
  const nextSteps = structured.next_steps || [];
  const followUp = structured.recommended_follow_up || '';
  const winRisk = structured.win_risk || '';
  const callScore = structured.call_score ?? '';

  let sentBadgeClass = 'sentiment-neutral';
  let SentIcon = Meh;
  let sentEmoji = '😐';
  if (sentiment.includes('positive')) {
    sentBadgeClass = 'sentiment-positive';
    SentIcon = Smile;
    sentEmoji = '🙂';
  } else if (sentiment.includes('negative')) {
    sentBadgeClass = 'sentiment-negative';
    SentIcon = Frown;
    sentEmoji = '🙁';
  }

  return (
    <div className="glass-card" style={{ animation: 'fadeIn 0.4s ease' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '18px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <FileText size={20} color="#6366f1" />
          <h2 style={{ fontSize: '16px', fontWeight: 700 }}>Executive Post-Call Summary</h2>
        </div>

        <button
          className="btn btn-secondary"
          onClick={onRefresh}
          style={{ padding: '6px 12px', fontSize: '12px' }}
        >
          <RotateCw size={13} />
          Refresh
        </button>
      </div>

      {/* Metrics Row: Score & Win/Risk & Overall Sentiment */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '12px', marginBottom: '18px' }}>
        {/* Sentiment Card */}
        <div className={`glass-card ${sentBadgeClass}`} style={{ padding: '14px', borderRadius: '12px' }}>
          <div style={{ fontSize: '11px', fontWeight: 600, textTransform: 'uppercase', marginBottom: '4px' }}>
            Overall Call Sentiment
          </div>
          <div style={{ fontSize: '16px', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '6px' }}>
            <SentIcon size={16} /> {summaryData.sentiment || 'Neutral'} {sentEmoji}
          </div>
        </div>

        {/* Call Score if available */}
        {callScore !== '' && (
          <div className="glass-card" style={{ padding: '14px', borderRadius: '12px', background: 'rgba(99, 102, 241, 0.1)', border: '1px solid rgba(99, 102, 241, 0.3)' }}>
            <div style={{ fontSize: '11px', fontWeight: 600, textTransform: 'uppercase', color: '#818cf8', marginBottom: '4px' }}>
              Call Quality Score
            </div>
            <div style={{ fontSize: '16px', fontWeight: 700, color: '#f8fafc', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Award size={16} color="#818cf8" /> {callScore} / 100
            </div>
          </div>
        )}

        {/* Win Risk Indicator if available */}
        {winRisk && (
          <div className="glass-card" style={{ padding: '14px', borderRadius: '12px', background: 'rgba(245, 158, 11, 0.1)', border: '1px solid rgba(245, 158, 11, 0.3)' }}>
            <div style={{ fontSize: '11px', fontWeight: 600, textTransform: 'uppercase', color: '#fbbf24', marginBottom: '4px' }}>
              Opportunity Risk Assessment
            </div>
            <div style={{ fontSize: '14px', fontWeight: 600, color: '#f8fafc', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <TrendingUp size={16} color="#fbbf24" /> {winRisk}
            </div>
          </div>
        )}
      </div>

      {/* Overview Summary */}
      <div style={{
        background: 'var(--bg-input)',
        border: '1px solid var(--border-subtle)',
        borderRadius: '12px',
        padding: '16px',
        marginBottom: '18px'
      }}>
        <h4 style={{ fontSize: '13px', fontWeight: 700, color: '#818cf8', textTransform: 'uppercase', marginBottom: '6px' }}>
          Call Executive Summary
        </h4>
        <p style={{ fontSize: '13px', color: 'var(--text-primary)', lineHeight: 1.5 }}>
          {summary}
        </p>
      </div>

      {/* Customer Intent & Key Topics */}
      {(intent || (topics && topics.length > 0)) && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px', marginBottom: '18px' }}>
          {intent && (
            <div style={{
              background: 'var(--bg-card-elevated)',
              border: '1px solid var(--border-subtle)',
              borderRadius: '12px',
              padding: '14px'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '6px' }}>
                <Target size={15} color="#38bdf8" />
                <span style={{ fontSize: '12px', fontWeight: 700, color: '#38bdf8', textTransform: 'uppercase' }}>
                  Customer Intent
                </span>
              </div>
              <p style={{ fontSize: '13px', color: 'var(--text-primary)', lineHeight: 1.4 }}>
                {intent}
              </p>
            </div>
          )}

          {topics && topics.length > 0 && (
            <div style={{
              background: 'var(--bg-card-elevated)',
              border: '1px solid var(--border-subtle)',
              borderRadius: '12px',
              padding: '14px'
            }}>
              <div style={{ fontSize: '12px', fontWeight: 700, color: 'var(--text-secondary)', textTransform: 'uppercase', marginBottom: '8px' }}>
                Key Topics Discussed
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                {topics.map((t, idx) => (
                  <span
                    key={idx}
                    style={{
                      background: 'rgba(255, 255, 255, 0.08)',
                      border: '1px solid var(--border-subtle)',
                      borderRadius: '16px',
                      padding: '3px 10px',
                      fontSize: '12px',
                      color: 'var(--text-primary)'
                    }}
                  >
                    {t}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Objections & Resolutions */}
      {((objections && objections.length > 0) || (resolutions && resolutions.length > 0)) && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px', marginBottom: '18px' }}>
          {objections && objections.length > 0 && (
            <div style={{
              background: 'rgba(239, 68, 68, 0.06)',
              border: '1px solid rgba(239, 68, 68, 0.2)',
              borderRadius: '12px',
              padding: '14px'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '8px', color: '#f87171' }}>
                <AlertTriangle size={15} />
                <span style={{ fontSize: '12px', fontWeight: 700, textTransform: 'uppercase' }}>
                  Identified Objections
                </span>
              </div>
              <ul style={{ paddingLeft: '18px', fontSize: '13px', color: 'var(--text-primary)', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                {objections.map((obj, i) => (
                  <li key={i}>{obj}</li>
                ))}
              </ul>
            </div>
          )}

          {resolutions && resolutions.length > 0 && (
            <div style={{
              background: 'rgba(16, 185, 129, 0.06)',
              border: '1px solid rgba(16, 185, 129, 0.2)',
              borderRadius: '12px',
              padding: '14px'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '8px', color: '#34d399' }}>
                <CheckCircle2 size={15} />
                <span style={{ fontSize: '12px', fontWeight: 700, textTransform: 'uppercase' }}>
                  Offered Resolutions
                </span>
              </div>
              <ul style={{ paddingLeft: '18px', fontSize: '13px', color: 'var(--text-primary)', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                {resolutions.map((res, i) => (
                  <li key={i}>{res}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Next Steps & Recommended Follow-up */}
      {((nextSteps && nextSteps.length > 0) || followUp) && (
        <div className="ai-box" style={{ marginBottom: '18px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '10px' }}>
            <ListTodo size={16} color="#c084fc" />
            <h4 style={{ fontSize: '13px', fontWeight: 700, color: '#c084fc', textTransform: 'uppercase' }}>
              Action Items & Recommended Follow-up
            </h4>
          </div>

          {nextSteps && nextSteps.length > 0 && (
            <ul style={{ paddingLeft: '18px', fontSize: '13px', color: 'var(--text-primary)', marginBottom: followUp ? '10px' : '0', display: 'flex', flexDirection: 'column', gap: '4px' }}>
              {nextSteps.map((step, idx) => (
                <li key={idx}>{step}</li>
              ))}
            </ul>
          )}

          {followUp && (
            <div style={{ fontSize: '13px', color: 'var(--text-primary)', paddingTop: nextSteps.length > 0 ? '8px' : '0', borderTop: nextSteps.length > 0 ? '1px solid rgba(192, 132, 252, 0.2)' : 'none' }}>
              <strong>Recommended Follow-up Strategy: </strong> {followUp}
            </div>
          )}
        </div>
      )}

      {/* Collapsible Full Transcript */}
      {transcript && (
        <div>
          <button
            onClick={() => setShowFullTranscript(!showFullTranscript)}
            className="btn btn-secondary"
            style={{ width: '100%', justifyContent: 'space-between', padding: '10px 14px' }}
          >
            <span>Full Conversation Transcript</span>
            {showFullTranscript ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
          </button>

          {showFullTranscript && (
            <div style={{
              marginTop: '10px',
              background: 'var(--bg-input)',
              border: '1px solid var(--border-subtle)',
              borderRadius: '10px',
              padding: '14px',
              fontSize: '12px',
              color: 'var(--text-secondary)',
              lineHeight: 1.6,
              whiteSpace: 'pre-wrap',
              maxHeight: '300px',
              overflowY: 'auto'
            }}>
              {transcript}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
