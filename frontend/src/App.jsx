import { useState, useEffect } from 'react';
import { Toaster, toast } from 'react-hot-toast';
import { getHealth, getViolations, getAnalytics, detectImage, exportReport } from './services/api';
import Header from './components/Header';
import HeroSection from './components/HeroSection';
import UploadPanel from './components/UploadPanel';

import ViolationsTable from './components/ViolationsTable';
import AnalyticsPanel from './components/AnalyticsPanel';
import EvidenceModal from './components/EvidenceModal';
import './App.css';

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
      const res = await getHealth();
      setServerOnline(res.status === 'ok');
    } catch {
      setServerOnline(false);
    }
  };

  const fetchViolations = async () => {
    try {
      const res = await getViolations();
      setViolations(res.data?.violations || []);
    } catch {
      // Server might not be running yet
    }
  };

  const fetchAnalytics = async () => {
    try {
      const res = await getAnalytics();
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



    try {
      const data = await detectImage(formData);

      // Add real results logs immediately
      const resultLogs = data.processing_logs || [];
      if (resultLogs.length > 0) {
        setProcessingLogs(prev => [...prev, ...resultLogs]);
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
      let errorDetail = err.response?.data?.detail;
      let errorMsg = 'Server unreachable. Is the backend running?';
      
      if (typeof errorDetail === 'string') {
        errorMsg = errorDetail;
      } else if (Array.isArray(errorDetail)) {
        errorMsg = errorDetail.map(e => e.msg || JSON.stringify(e)).join(', ');
      } else if (errorDetail) {
        errorMsg = JSON.stringify(errorDetail);
      } else if (err.message) {
        errorMsg = err.message;
      }

      setProcessingLogs(prev => [...prev, `[ERROR] ${errorMsg}`]);
      toast.error(`Detection failed: ${errorMsg}`);
      setIsProcessing(false);
    }
  };

  // --- Export Reports ---
  const handleExportCSV = async (reportType = 'daily') => {
    try {
      const data = await exportReport(reportType);
      const url = window.URL.createObjectURL(new Blob([data]));
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
