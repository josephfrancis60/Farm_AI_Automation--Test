import React, { useEffect, useRef } from 'react';

const VoiceVisualizer = ({ isListening, isSpeaking }) => {
  const canvasRef = useRef(null);
  const audioContextRef = useRef(null);
  const analyserRef = useRef(null);
  const dataArrayRef = useRef(null);
  const animationRef = useRef(null);

  // Smoothing values
  const smoothAmp = useRef(8);
  const smoothFreq = useRef(0.04);

  useEffect(() => {
    if (isListening) {
      startListening();
    } else {
      stopListening();
    }
    return () => stopListening();
  }, [isListening]);

  const startListening = async () => {
    try {
      audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)();
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const source = audioContextRef.current.createMediaStreamSource(stream);
      analyserRef.current = audioContextRef.current.createAnalyser();
      analyserRef.current.fftSize = 256;
      source.connect(analyserRef.current);
      const bufferLength = analyserRef.current.frequencyBinCount;
      dataArrayRef.current = new Uint8Array(bufferLength);
    } catch (err) {
      console.error('Error accessing microphone:', err);
    }
  };

  const stopListening = () => {
    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }
  };

  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    let phase = 0;

    const SHADOW_BLUR = 15;
    const LINE_WIDTH = 2;
    // Max amplitude so waves never clip: half-height minus glow and line
    const MAX_AMP = canvas.height / 2 - SHADOW_BLUR - LINE_WIDTH - 2;

    const render = () => {
      const width = canvas.width;
      const height = canvas.height;
      ctx.clearRect(0, 0, width, height);

      let targetAmp = 8;
      let targetFreq = 0.04;

      if (isListening && analyserRef.current) {
        analyserRef.current.getByteFrequencyData(dataArrayRef.current);
        const sum = dataArrayRef.current.reduce((a, b) => a + b, 0);
        const average = sum / dataArrayRef.current.length;
        targetAmp = 6 + average * 1.0;
        targetFreq = 0.04 + average * 0.003;
      } else if (isSpeaking) {
        targetAmp = 15 + Math.sin(Date.now() * 0.02) * 8 + Math.random() * 3;
        targetFreq = 0.06 + Math.sin(Date.now() * 0.01) * 0.02;
      }

      // Clamp so the wave (including glow) never touches the canvas edge
      targetAmp = Math.min(targetAmp, MAX_AMP);

      smoothAmp.current += (targetAmp - smoothAmp.current) * 0.12;
      smoothFreq.current += (targetFreq - smoothFreq.current) * 0.12;

      // Use screen blending for neon overlap look
      ctx.globalCompositeOperation = 'screen';
      ctx.shadowBlur = SHADOW_BLUR;

      // Define 4 distinct neon waves
      const waves = [
        { color: '#00d4ff', pOff: 0, fMult: 1, aMult: 1 },
        { color: '#ff00ff', pOff: Math.PI / 2, fMult: 0.8, aMult: 0.7 },
        { color: '#ffff00', pOff: Math.PI, fMult: 1.2, aMult: 0.5 },
        { color: '#0000ff', pOff: Math.PI * 1.5, fMult: 0.7, aMult: 0.8 },
      ];

      waves.forEach(w => {
        ctx.shadowColor = w.color;
        drawWave(
          ctx, width, height,
          phase + w.pOff,
          smoothAmp.current * w.aMult,   // aMult < 1, so always within MAX_AMP
          smoothFreq.current * w.fMult,
          w.color,
          LINE_WIDTH
        );
      });

      phase += 0.06;
      animationRef.current = requestAnimationFrame(render);
    };

    const drawWave = (ctx, w, h, p, amp, freq, color, lineWidth) => {
      ctx.beginPath();
      ctx.strokeStyle = color;
      ctx.lineWidth = lineWidth;
      for (let x = 0; x < w; x++) {
        // Sine wave with tapered ends
        const y = h / 2 + Math.sin(x * freq + p) * amp * Math.sin(x * Math.PI / w);
        if (x === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      }
      ctx.stroke();
    };

    render();
    return () => cancelAnimationFrame(animationRef.current);
  }, [isListening, isSpeaking]);

  return (
    <div className="voice-visualizer-container">
      {/* Increased height from 80 → 120 to give waves more room */}
      <canvas ref={canvasRef} width={200} height={120} className="voice-canvas" />
      {!isListening && !isSpeaking && (
        <div className="voice-tooltip">Press 'M' to toggle voice</div>
      )}
    </div>
  );
};

export default VoiceVisualizer;