import { useState, useEffect, useRef } from 'react';
import { Toaster, toast } from 'react-hot-toast';
import axios from 'axios';
import Header from './components/Header';
import HeroSection from './components/HeroSection';
import UploadPanel from './components/UploadPanel';
import ResultsPanel from './components/ResultsPanel';
import ViolationsTable from './components/ViolationsTable';
import AnalyticsPanel from './components/AnalyticsPanel';
import EvidenceModal from './components/EvidenceModal';
import './App.css';

const API_BASE = 'http://localhost:8000';

function App() {
  // --- State ---
  const [violations, setViolations] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [detectionResult, setDetectionResult] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingLogs, setProcessingLogs] = useState([]);
  const [selectedEvidence, setSelectedEvidence] = useState(null);
  const [serverOnline, setServerOnline] = useState(false);

  // --- Fetch initial data ---
  useEffect(() => {
    checkServerHealth();
    fetchViolations();
    fetchAnalytics();
  }, []);

  const checkServerHealth = async () => {
    try {
      const res = await axios.get(`${API_BASE}/api/health`);
      setServerOnline(res.data.status === 'online');
    } catch {
      setServerOnline(false);
    }
  };

  const fetchViolations = async () => {
    try {
      const res = await axios.get(`${API_BASE}/api/violations`);
      setViolations(res.data.violations || []);
    } catch {
      // Server might not be running yet
    }
  };

  const fetchAnalytics = async () => {
    try {
      const res = await axios.get(`${API_BASE}/api/analytics`);
      setAnalytics(res.data);
    } catch {
      // Server might not be running yet
    }
  };

  // --- Image Upload & Detection ---
  const handleImageUpload = async (file) => {
    if (!file) return;

    setIsProcessing(true);
    setProcessingLogs([]);
    setDetectionResult(null);

    const formData = new FormData();
    formData.append('image', file);

    // Add simulated streaming logs
    const logMessages = [
      '[SYSTEM] Initiating TrafficVision AI Core...',
      '[IMAGE] Reading uploaded feed...',
      '[PREPROCESS] Applying CLAHE low-light enhancement...',
      '[PREPROCESS] Running Gaussian denoising filter...',
      '[PREPROCESS] Correcting motion blur artifacts...',
      '[MODEL] Loading YOLOv8s inference engine...',
      '[YOLO] Running object detection (conf > 0.25)...',
    ];

    for (let i = 0; i < logMessages.length; i++) {
      await new Promise(r => setTimeout(r, 400));
      setProcessingLogs(prev => [...prev, logMessages[i]]);
    }

    try {
      const res = await axios.post(`${API_BASE}/api/detect`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 60000,
      });

      const data = res.data;

      // Continue logs with real results
      const resultLogs = data.processing_logs || [];
      for (let i = 0; i < resultLogs.length; i++) {
        await new Promise(r => setTimeout(r, 200));
        setProcessingLogs(prev => [...prev, resultLogs[i]]);
      }

      setDetectionResult(data);
      setIsProcessing(false);

      // Refresh violations and analytics
      fetchViolations();
      fetchAnalytics();

      if (data.violations && data.violations.length > 0) {
        toast.error(`⚠️ ${data.violations.length} violation(s) detected!`, {
          duration: 5000,
          style: { background: '#1a0a2e', color: '#ff3366', border: '1px solid #ff3366' },
        });
      } else {
        toast.success('✅ No violations detected.', {
          duration: 3000,
          style: { background: '#0a1a2e', color: '#00ff87', border: '1px solid #00ff87' },
        });
      }
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'Server unreachable. Is the backend running?';
      setProcessingLogs(prev => [...prev, `[ERROR] ${errorMsg}`]);
      toast.error(`Detection failed: ${errorMsg}`);
      setIsProcessing(false);
    }
  };

  // --- Export Reports ---
  const handleExportCSV = async (reportType = 'daily') => {
    try {
      const res = await axios.get(`${API_BASE}/api/reports/${reportType}?format=csv`, {
        responseType: 'blob',
      });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `trafficvision_${reportType}_report.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      toast.success('📄 CSV Report downloaded!');
    } catch {
      toast.error('Failed to generate report.');
    }
  };

  return (
    <div className="app-root">
      <Toaster position="top-right" />
      <Header serverOnline={serverOnline} />
      
      <main className="main-content">
        <HeroSection />
        
        <UploadPanel
          onUpload={handleImageUpload}
          isProcessing={isProcessing}
          processingLogs={processingLogs}
          detectionResult={detectionResult}
        />

        <ResultsPanel detectionResult={detectionResult} />

        <ViolationsTable
          violations={violations}
          onViewEvidence={(v) => setSelectedEvidence(v)}
        />

        <AnalyticsPanel
          analytics={analytics}
          onExportCSV={handleExportCSV}
        />
      </main>

      {selectedEvidence && (
        <EvidenceModal
          evidence={selectedEvidence}
          onClose={() => setSelectedEvidence(null)}
        />
      )}
    </div>
  );
}

export default App;
