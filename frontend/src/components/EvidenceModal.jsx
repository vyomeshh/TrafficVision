import { FaXmark } from 'react-icons/fa6';

export default function EvidenceModal({ evidence, onClose }) {
  if (!evidence) return null;

  // Build the annotated image if available
  const imageUrl = evidence.annotated_image_path
    ? `http://localhost:8000/static/${evidence.annotated_image_path}`
    : evidence.image_path
      ? `http://localhost:8000/static/${evidence.image_path}`
      : null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3 className="modal-title">VIOLATION EVIDENCE</h3>
          <button className="modal-close" onClick={onClose}>
            <FaXmark />
          </button>
        </div>

        {imageUrl && (
          <div className="modal-image-container">
            <img src={imageUrl} alt="Evidence" className="modal-image" />
          </div>
        )}

        <div className="modal-details-grid">
          <div className="modal-detail">
            <div className="modal-detail-label">Detection ID</div>
            <div className="modal-detail-value">{evidence.detection_id || 'N/A'}</div>
          </div>
          <div className="modal-detail">
            <div className="modal-detail-label">License Plate</div>
            <div className="modal-detail-value" style={{ color: '#00f2fe', fontFamily: "'Orbitron', sans-serif" }}>
              {evidence.license_plate || 'Not Recognized'}
            </div>
          </div>
          <div className="modal-detail">
            <div className="modal-detail-label">Vehicle Type</div>
            <div className="modal-detail-value">{evidence.vehicle_type || 'Unknown'}</div>
          </div>
          <div className="modal-detail">
            <div className="modal-detail-label">Violation Type</div>
            <div className="modal-detail-value" style={{ color: evidence.violation_type !== 'None' ? '#ff3366' : '#00ff87' }}>
              {evidence.violation_type || 'None'}
            </div>
          </div>
          <div className="modal-detail">
            <div className="modal-detail-label">Confidence Score</div>
            <div className="modal-detail-value" style={{ color: '#00ff87' }}>
              {evidence.confidence ? `${(evidence.confidence * 100).toFixed(1)}%` : 'N/A'}
            </div>
          </div>
          <div className="modal-detail">
            <div className="modal-detail-label">Timestamp</div>
            <div className="modal-detail-value">{evidence.timestamp || '-'}</div>
          </div>
          <div className="modal-detail">
            <div className="modal-detail-label">Location</div>
            <div className="modal-detail-value">{evidence.location || 'Junction Zone 4'}</div>
          </div>
          <div className="modal-detail">
            <div className="modal-detail-label">Status</div>
            <div className="modal-detail-value" style={{ color: '#ffaa00' }}>
              {evidence.status || 'PENDING'}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
