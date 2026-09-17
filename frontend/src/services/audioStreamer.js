/**
 * AudioStreamer manages microphone capture and sends 16kHz Float32 PCM
 * blocks over WebSocket directly to the backend.
 */
export class AudioStreamer {
  constructor({ onVolume, onStatusChange }) {
    this.onVolume = onVolume || (() => {});
    this.onStatusChange = onStatusChange || (() => {});
    this.audioContext = null;
    this.mediaStream = null;
    this.sourceNode = null;
    this.processorNode = null;
    this.isStreaming = false;
    this.targetSampleRate = 16000;
  }

  async start(socket) {
    if (this.isStreaming) return;

    try {
      this.mediaStream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });

      const AudioContextClass = window.AudioContext || window.webkitAudioContext;
      this.audioContext = new AudioContextClass();
      const sourceRate = this.audioContext.sampleRate;

      this.sourceNode = this.audioContext.createMediaStreamSource(this.mediaStream);

      // 4096 buffer provides smooth, consistent audio chunks
      const bufferSize = 4096;
      this.processorNode = this.audioContext.createScriptProcessor(bufferSize, 1, 1);

      this.processorNode.onaudioprocess = (event) => {
        if (!this.isStreaming || !socket || socket.readyState !== WebSocket.OPEN) {
          return;
        }

        const inputData = event.inputBuffer.getChannelData(0);

        // 1. Calculate RMS volume for audio visualizer
        let sum = 0;
        for (let i = 0; i < inputData.length; i++) {
          sum += inputData[i] * inputData[i];
        }
        const rms = Math.sqrt(sum / inputData.length);
        this.onVolume(Math.min(1, rms * 5)); // Scaled for UI meter

        // 2. Resample to 16,000 Hz if needed
        const resampled = this._resampleAudio(inputData, sourceRate, this.targetSampleRate);

        // 3. Send binary Float32Array buffer over WebSocket
        socket.send(resampled.buffer);
      };

      this.sourceNode.connect(this.processorNode);
      this.processorNode.connect(this.audioContext.destination);

      this.isStreaming = true;
      this.onStatusChange({ streaming: true });
    } catch (err) {
      console.error('AudioStreamer error:', err);
      this.stop();
      throw err;
    }
  }

  _resampleAudio(audio, sourceRate, targetRate) {
    if (sourceRate === targetRate || audio.length === 0) {
      return new Float32Array(audio);
    }

    const targetLength = Math.max(1, Math.round((audio.length * targetRate) / sourceRate));
    const result = new Float32Array(targetLength);
    const ratio = (audio.length - 1) / (targetLength - 1 || 1);

    for (let i = 0; i < targetLength; i++) {
      const srcIndex = i * ratio;
      const lower = Math.floor(srcIndex);
      const upper = Math.min(lower + 1, audio.length - 1);
      const weight = srcIndex - lower;
      result[i] = audio[lower] * (1 - weight) + audio[upper] * weight;
    }

    return result;
  }

  stop() {
    this.isStreaming = false;

    if (this.processorNode) {
      try {
        this.processorNode.disconnect();
      } catch (e) {}
      this.processorNode = null;
    }

    if (this.sourceNode) {
      try {
        this.sourceNode.disconnect();
      } catch (e) {}
      this.sourceNode = null;
    }

    if (this.mediaStream) {
      this.mediaStream.getTracks().forEach((track) => track.stop());
      this.mediaStream = null;
    }

    if (this.audioContext && this.audioContext.state !== 'closed') {
      try {
        this.audioContext.close();
      } catch (e) {}
      this.audioContext = null;
    }

    this.onVolume(0);
    this.onStatusChange({ streaming: false });
  }
}
