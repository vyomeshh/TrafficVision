import { useState, useRef } from 'react';
import { FaCloudArrowUp, FaFileImage, FaPlay, FaRotateRight, FaImage } from 'react-icons/fa6';

export default function UploadPanel({ onUpload, isProcessing, processingLogs, detectionResult }) {
  const [selectedFile, setSelectedFile] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const [activeTab, setActiveTab] = useState('original');
  const fileInputRef = useRef(null);
  const terminalRef = useRef(null);

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
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  // Get preview URL for the selected file
  const previewUrl = selectedFile ? URL.createObjectURL(selectedFile) : null;

  // Get images from detection result
  const getImageSrc = (tab) => {
    if (!detectionResult?.images) return null;
    const b64 = detectionResult.images[tab];
    if (b64) return `data:image/png;base64,${b64}`;
    return null;
  };

  const currentImage = activeTab === 'original' && previewUrl
    ? previewUrl
    : getImageSrc(activeTab);

  return (
    <section id="upload" style={{ paddingTop: '16px' }}>
      <div className="section-header">
        <div className="section-icon"><FaCloudArrowUp /></div>
        <h2 className="section-title">UPLOAD & DETECTION ENGINE</h2>
      </div>

      <div className="upload-grid">
        {/* Left: Upload Card */}
        <div className="glass-panel">
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
              <div className="upload-filename">
                📁 {selectedFile.name} ({(selectedFile.size / 1024).toFixed(1)} KB)
              </div>
            )}
          </div>

          <div className="upload-actions">
            <button className="btn btn-secondary" onClick={() => fileInputRef.current?.click()}>
              <FaFileImage /> Select Image
            </button>
            <button
              className="btn btn-purple"
              disabled={!selectedFile || isProcessing}
              onClick={handleStartDetection}
            >
              {isProcessing ? <><span className="spinner" /> Processing...</> : <><FaPlay /> Start Detection</>}
            </button>
            <button className="btn btn-secondary" onClick={handleReset} style={{ maxWidth: 100 }}>
              <FaRotateRight /> Reset
            </button>
          </div>

          {/* Terminal Console */}
          {processingLogs.length > 0 && (
            <div className="terminal-console" ref={terminalRef}>
              {processingLogs.map((log, i) => (
                <div key={i} className={`terminal-line ${log.includes('[ERROR]') ? 'error' : ''}`}>
                  {log}
                </div>
              ))}
            </div>
          )}
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
