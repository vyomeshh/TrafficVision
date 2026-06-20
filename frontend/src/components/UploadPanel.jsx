import { useState, useRef, useEffect } from 'react';
import { 
  FaCloudArrowUp, FaFileImage, FaPlay, FaRotateRight, FaImage,
  FaCar, FaMotorcycle, FaUserShield, FaSquareParking, FaTrafficLight, FaClipboardList, FaArrowLeft
} from 'react-icons/fa6';

export default function UploadPanel({ onUpload, isProcessing, processingLogs, detectionResult }) {
  const [selectedFile, setSelectedFile] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const [activeTab, setActiveTab] = useState('original');
  const [isFlipped, setIsFlipped] = useState(false);
  const fileInputRef = useRef(null);
  const terminalRef = useRef(null);

  // Auto-switch to annotated tab and flip the card when detection succeeds
  useEffect(() => {
    if (!isProcessing && detectionResult && detectionResult.success) {
      setIsFlipped(true);
      if (detectionResult.images?.annotated) {
        setActiveTab('annotated');
      }
    }
  }, [isProcessing, detectionResult]);

  // Auto-scroll terminal
  useEffect(() => {
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
    }
  }, [processingLogs]);

  const handleDrop = (e) => {
    e.preventDefault();
    setDragActive(false);
    if (e.dataTransfer.files.length > 0) {
      setSelectedFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files.length > 0) {
      setSelectedFile(e.target.files[0]);
    }
  };

  const handleStartDetection = () => {
    if (selectedFile) {
      onUpload(selectedFile);
    }
  };

  const handleReset = () => {
    setSelectedFile(null);
    setActiveTab('original');
    setIsFlipped(false);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const previewUrl = selectedFile ? URL.createObjectURL(selectedFile) : null;

  const getImageSrc = (tab) => {
    if (!detectionResult?.images) return null;
    const b64 = detectionResult.images[tab];
    if (b64) return `data:image/png;base64,${b64}`;
    return null;
  };

  const currentImage = activeTab === 'original' && previewUrl
    ? previewUrl
    : getImageSrc(activeTab);

  // Detections data logic
  const r = detectionResult || {};
  const violations = r.violations || [];
  const countType = (type) => violations.filter(v => v.type === type).length;

  const cards = [
    { label: 'VEHICLES', count: r.vehicles_detected || 0, icon: <FaCar />, isAlert: false },
    { label: 'NO HELMET', count: countType('No Helmet'), icon: <FaMotorcycle />, isAlert: countType('No Helmet') > 0 },
    { label: 'TRIPLE RIDING', count: countType('Triple Riding'), icon: <FaUserShield />, isAlert: countType('Triple Riding') > 0 },
    { label: 'RED LIGHT', count: countType('Red Light Violation'), icon: <FaTrafficLight />, isAlert: countType('Red Light Violation') > 0 },
    { label: 'PLATES', count: r.plates_recognized?.length || 0, icon: <FaSquareParking />, isAlert: false },
  ];

  return (
    <section id="upload" style={{ paddingTop: '16px' }}>
      <div className="section-header">
        <div className="section-icon"><FaCloudArrowUp /></div>
        <h2 className="section-title">UPLOAD & DETECTION ENGINE</h2>
      </div>

      <div className="upload-grid">
        {/* Left: Flip Card Container */}
        <div className={`flip-container ${isFlipped ? 'flipped' : ''}`}>
          <div className="flipper">
            
            {/* FRONT FACE: Upload form and console */}
            <div className="front">
              <div
                className={`drag-area ${dragActive ? 'active' : ''}`}
                onDragOver={(e) => { e.preventDefault(); setDragActive(true); }}
                onDragLeave={() => setDragActive(false)}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
              >
                <input
                  type="file"
                  ref={fileInputRef}
                  onChange={handleFileChange}
                  accept="image/*"
                  style={{ display: 'none' }}
                />
                <div className="drag-icon"><FaCloudArrowUp /></div>
                <div className="drag-title">Drag & Drop traffic image here</div>
                <div className="drag-subtitle">
                  Supports PNG, JPG, JPEG up to 15MB. Runs YOLOv8 + PaddleOCR pipeline.
                </div>
                {selectedFile && (
                  <div className="upload-filename" style={{ marginTop: '10px', fontSize: '0.9rem', color: '#00ff87' }}>
                    📁 {selectedFile.name} ({(selectedFile.size / 1024).toFixed(1)} KB)
                  </div>
                )}
              </div>

              <div className="upload-actions" style={{ marginTop: '15px' }}>
                <button className="btn btn-secondary" onClick={() => fileInputRef.current?.click()}>
                  <FaFileImage /> Select
                </button>
                <button
                  className="btn btn-purple"
                  disabled={!selectedFile || isProcessing}
                  onClick={handleStartDetection}
                  style={{ flex: 2 }}
                >
                  {isProcessing ? <><span className="spinner" /> Processing...</> : <><FaPlay /> Start Detection</>}
                </button>
              </div>

              {/* Terminal Console */}
              {processingLogs.length > 0 && (
                <div className="terminal-console" ref={terminalRef} style={{ marginTop: '15px', flexGrow: 1 }}>
                  {processingLogs.map((log, i) => (
                    <div key={i} className={`terminal-line ${log.includes('[ERROR]') ? 'error' : ''}`}>
                      {log}
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* BACK FACE: Detection Results */}
            <div className="back">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '15px' }}>
                <h3 style={{ fontSize: '1.2rem', display: 'flex', alignItems: 'center', gap: '8px', margin: 0 }}>
                  <FaClipboardList /> DETECTION RESULTS
                </h3>
                <button className="btn btn-secondary" onClick={handleReset} style={{ padding: '6px 12px', fontSize: '0.85rem' }}>
                  <FaArrowLeft /> New Upload
                </button>
              </div>

              {/* Mini version of the results grid */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', marginBottom: '15px' }}>
                {cards.map((card, i) => (
                  <div key={i} className={`result-card ${card.isAlert ? 'alert' : ''}`} style={{ padding: '12px' }}>
                    <div className="result-header" style={{ fontSize: '0.75rem' }}>
                      <span className="result-label">{card.label}</span>
                      <span className="result-icon">{card.icon}</span>
                    </div>
                    <div className="result-count" style={{ fontSize: '1.5rem' }}>{card.count}</div>
                  </div>
                ))}
              </div>

              {/* Detected Violations List */}
              {violations.length > 0 ? (
                <div style={{ background: 'rgba(255, 255, 255, 0.02)', padding: '12px', borderRadius: '8px', flexGrow: 1 }}>
                  <h4 style={{ fontSize: '0.9rem', marginBottom: '10px', color: '#8b9bb4' }}>
                    VIOLATIONS IN IMAGE
                  </h4>
                  <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    {violations.map((v, i) => (
                      <li key={i} style={{ display: 'flex', justifyContent: 'space-between', background: 'rgba(255,51,102,0.1)', padding: '10px', borderRadius: '6px', borderLeft: '3px solid #ff3366', fontSize: '0.85rem' }}>
                        <div>
                          <strong style={{ display: 'block', color: '#fff' }}>{v.type || v.violation_type}</strong>
                          <span style={{ color: '#8b9bb4' }}>{v.vehicle_type || 'Unknown'}</span>
                        </div>
                        <div style={{ fontWeight: '600', color: '#00ff87', alignSelf: 'center' }}>
                          {(v.confidence * 100).toFixed(1)}% Conf
                        </div>
                      </li>
                    ))}
                  </ul>
                </div>
              ) : (
                <div style={{ textAlign: 'center', padding: '20px', color: '#8b9bb4', flexGrow: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  No violations detected in this frame.
                </div>
              )}
            </div>

          </div>
        </div>

        {/* Right: Image Viewer */}
        <div className="glass-panel viewer-panel">
          <div className="viewer-tabs">
            <button
              className={`tab-btn ${activeTab === 'original' ? 'active' : ''}`}
              onClick={() => setActiveTab('original')}
            >
              Original Feed
            </button>
            <button
              className={`tab-btn ${activeTab === 'processed' ? 'active' : ''}`}
              disabled={!detectionResult?.images?.processed}
              onClick={() => setActiveTab('processed')}
            >
              Preprocessed
            </button>
            <button
              className={`tab-btn ${activeTab === 'annotated' ? 'active' : ''}`}
              disabled={!detectionResult?.images?.annotated}
              onClick={() => setActiveTab('annotated')}
            >
              AI Annotation
            </button>
          </div>

          <div className="viewer-area">
            {isProcessing && <div className="scanner-laser" />}

            {currentImage ? (
              <img src={currentImage} alt={`${activeTab} view`} className="viewer-image" />
            ) : (
              <div className="viewer-placeholder">
                <div className="viewer-placeholder-icon"><FaImage /></div>
                <p>Upload a traffic image to visualize feeds</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </section>
  );
}
