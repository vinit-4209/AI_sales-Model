import React, { useState, useEffect, useRef } from 'react';
import Header from './components/Header';
import SidebarCRM from './components/SidebarCRM';
import CallControls from './components/CallControls';
import LiveInsights from './components/LiveInsights';
import LiveTranscript from './components/LiveTranscript';
import PostCallSummary from './components/PostCallSummary';
import { AudioStreamer } from './services/audioStreamer';
import {
  fetchHealth,
  startCallApi,
  stopCallApi,
  getCallStatusApi,
  getTranscriptApi,
  getSummaryApi
} from './services/api';

export default function App() {
  const [isConnected, setIsConnected] = useState(false);
  const [isRunning, setIsRunning] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [callDuration, setCallDuration] = useState(0);
  const [volume, setVolume] = useState(0);
  const [statusMessage, setStatusMessage] = useState('');

  // CRM State
  const [customer, setCustomer] = useState(null);
  const [recommendations, setRecommendations] = useState('');

  // Live Call State
  const [sentiment, setSentiment] = useState('Neutral');
  const [summary, setSummary] = useState('');
  const [suggestion, setSuggestion] = useState('Waiting for customer input...');
  const [utterances, setUtterances] = useState([]);
  const [rawTranscript, setRawTranscript] = useState('');

  // Post-Call Summary
  const [summaryData, setSummaryData] = useState(null);

  // References
  const socketRef = useRef(null);
  const streamerRef = useRef(null);
  const timerRef = useRef(null);

  // 1. Initialize AudioStreamer
  useEffect(() => {
    streamerRef.current = new AudioStreamer({
      onVolume: (vol) => setVolume(vol),
      onStatusChange: (status) => {
        if (!status.streaming) {
          setVolume(0);
        }
      },
    });

    return () => {
      if (streamerRef.current) {
        streamerRef.current.stop();
      }
    };
  }, []);

  // 2. Call duration timer
  useEffect(() => {
    if (isRunning) {
      timerRef.current = setInterval(() => {
        setCallDuration((prev) => prev + 1);
      }, 1000);
    } else {
      clearInterval(timerRef.current);
    }
    return () => clearInterval(timerRef.current);
  }, [isRunning]);

  // 3. Setup WebSocket connection with auto-reconnect and deduplication
  const reconnectTimerRef = useRef(null);

  const connectWebSocket = () => {
    // Avoid creating duplicate sockets if one is already open or connecting
    if (
      socketRef.current &&
      (socketRef.current.readyState === WebSocket.OPEN ||
        socketRef.current.readyState === WebSocket.CONNECTING)
    ) {
      return;
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/call`;

    const socket = new WebSocket(wsUrl);
    socketRef.current = socket;

    socket.onopen = () => {
      setIsConnected(true);
      setStatusMessage('');
    };

    socket.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        if (payload.type === 'status') {
          setIsRunning(Boolean(payload.data?.is_running));
        } else if (payload.type === 'utterance') {
          const u = payload.data;
          if (!u || !u.transcript) return;

          setSentiment(u.sentiment || 'Neutral');
          setSummary(u.summary || '');
          setSuggestion(u.suggestion || '');

          setUtterances((prev) => {
            // Guard against duplicates from multiple socket events
            const alreadyExists = prev.some((item) => {
              if (item.timestamp && u.timestamp && item.timestamp === u.timestamp) {
                return true;
              }
              if (
                item.transcript === u.transcript &&
                item.timestamp &&
                u.timestamp &&
                Math.abs(new Date(item.timestamp).getTime() - new Date(u.timestamp).getTime()) < 2000
              ) {
                return true;
              }
              return false;
            });

            if (alreadyExists) {
              return prev;
            }
            return [...prev, u];
          });
        } else if (payload.type === 'call_ended') {
          setIsRunning(false);
          setSummaryData(payload.data);
        }
      } catch (err) {
        console.error('Error parsing WS message:', err);
      }
    };

    socket.onclose = () => {
      setIsConnected(false);
      clearTimeout(reconnectTimerRef.current);
      reconnectTimerRef.current = setTimeout(connectWebSocket, 3000);
    };

    socket.onerror = (err) => {
      console.warn('WebSocket error, will retry:', err);
    };
  };

  useEffect(() => {
    connectWebSocket();

    // Initial check on mount
    fetchHealth().then((health) => {
      if (health && health.is_running) {
        setIsRunning(true);
      }
    });

    getSummaryApi().then((res) => {
      if (res && res.summary) {
        setSummaryData(res.summary);
      }
    });

    return () => {
      clearTimeout(reconnectTimerRef.current);
      if (socketRef.current) {
        socketRef.current.onclose = null; // Prevent reconnect on intentional unmount
        socketRef.current.close();
        socketRef.current = null;
      }
    };
  }, []);

  // 4. Start Call
  const handleStartCall = async () => {
    setIsProcessing(true);
    setStatusMessage('');
    try {
      // Start backend pipeline
      await startCallApi();

      // Reset live states
      setCallDuration(0);
      setUtterances([]);
      setRawTranscript('');
      setSentiment('Neutral');
      setSummary('');
      setSuggestion('Listening for customer statements...');

      // Start browser microphone capture & stream to WebSocket
      if (streamerRef.current && socketRef.current) {
        await streamerRef.current.start(socketRef.current);
      }

      setIsRunning(true);
    } catch (err) {
      console.error('Failed to start call:', err);
      setStatusMessage('Microphone access denied or backend error. Please allow microphone permissions.');
      setIsRunning(false);
    } finally {
      setIsProcessing(false);
    }
  };

  // 5. Stop Call
  const handleStopCall = async () => {
    setIsProcessing(true);
    setStatusMessage('Finalizing transcription and generating AI summary...');
    try {
      // Stop browser audio recording
      if (streamerRef.current) {
        streamerRef.current.stop();
      }

      // Stop backend pipeline & retrieve final summary
      const response = await stopCallApi();
      setIsRunning(false);

      if (response && response.summary) {
        setSummaryData(response.summary);
      } else {
        // Fallback fetch summary
        const sumRes = await getSummaryApi();
        if (sumRes && sumRes.summary) {
          setSummaryData(sumRes.summary);
        }
      }

      setStatusMessage('');
    } catch (err) {
      console.error('Failed to stop call:', err);
      setStatusMessage('Error stopping call. Please try again.');
    } finally {
      setIsProcessing(false);
    }
  };

  // Refresh post-call summary
  const handleRefreshSummary = async () => {
    try {
      const res = await getSummaryApi();
      if (res && res.summary) {
        setSummaryData(res.summary);
      }
    } catch (err) {
      console.error('Error refreshing summary:', err);
    }
  };

  return (
    <div className="app-container">
      {/* Top Navbar */}
      <Header
        isRunning={isRunning}
        isConnected={isConnected}
        callDuration={callDuration}
      />

      {/* Main Dashboard Layout */}
      <main className="main-layout">
        {/* Left Sidebar: CRM Customer Profile */}
        <SidebarCRM
          customer={customer}
          recommendations={recommendations}
          onCustomerLoaded={(cust, recs) => {
            setCustomer(cust);
            setRecommendations(recs);
          }}
        />

        {/* Right Area: Call Controls, Live Insights, Transcript & Post-Call Summary */}
        <section style={{ display: 'flex', flexDirection: 'column' }}>
          {/* Call Controls & Audio Waveform */}
          <CallControls
            isRunning={isRunning}
            isProcessing={isProcessing}
            volume={volume}
            onStartCall={handleStartCall}
            onStopCall={handleStopCall}
            statusMessage={statusMessage}
          />

          {/* Real-time Sentiment & AI Next Best Action */}
          <LiveInsights
            sentiment={sentiment}
            summary={summary}
            suggestion={suggestion}
          />

          {/* Live Transcript Stream */}
          <LiveTranscript
            utterances={utterances}
            rawTranscript={rawTranscript}
            isRunning={isRunning}
          />

          {/* Executive Post-Call Summary & Scorecard */}
          <PostCallSummary
            summaryData={summaryData}
            onRefresh={handleRefreshSummary}
          />
        </section>
      </main>
    </div>
  );
}
