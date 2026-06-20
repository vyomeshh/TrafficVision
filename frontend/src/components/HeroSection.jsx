import { FaShieldHalved, FaCloudArrowUp, FaChartLine } from 'react-icons/fa6';

export default function HeroSection() {
  return (
    <section className="glass-panel hero-section">
      <div className="hero-grid-bg" />
      <div className="hero-glow hero-glow-1" />
      <div className="hero-glow hero-glow-2" />

      <div style={{ position: 'relative', zIndex: 2 }}>
        <div className="hero-badge">
          <FaShieldHalved /> AI-Powered Computer Vision Platform
        </div>
        <h1 className="hero-title">
          Automated Traffic <span>Violation Detection</span> System
        </h1>
        <p className="hero-subtitle">
          Real-time traffic enforcement using YOLOv8 object detection, PaddleOCR 
          license plate recognition, and intelligent violation classification — 
          enhancing road safety across metropolitan junctions.
        </p>
        <div className="hero-buttons">
          <a href="#upload" className="btn btn-primary">
            <FaCloudArrowUp /> Upload Traffic Image
          </a>
          <a href="#analytics" className="btn btn-secondary">
            <FaChartLine /> View Analytics
          </a>
        </div>
      </div>
    </section>
  );
}
