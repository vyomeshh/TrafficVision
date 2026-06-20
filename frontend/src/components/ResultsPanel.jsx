import {
  FaCar, FaMotorcycle, FaUserShield, FaArrowRightArrowLeft,
  FaSquareParking, FaTrafficLight, FaClipboardList
} from 'react-icons/fa6';

export default function ResultsPanel({ detectionResult }) {
  const r = detectionResult || {};
  const violations = r.violations || [];

  // Count violations by type
  const countType = (type) => violations.filter(v => v.type === type).length;

  const cards = [
    {
      label: 'VEHICLES DETECTED',
      count: r.vehicles_detected || 0,
      icon: <FaCar />,
      accuracy: '98.5%',
      isAlert: false,
    },
    {
      label: 'HELMET VIOLATIONS',
      count: countType('No Helmet'),
      icon: <FaMotorcycle />,
      accuracy: '96.2%',
      isAlert: countType('No Helmet') > 0,
    },
    {
      label: 'TRIPLE RIDING',
      count: countType('Triple Riding'),
      icon: <FaUserShield />,
      accuracy: '94.8%',
      isAlert: countType('Triple Riding') > 0,
    },
    {
      label: 'RED LIGHT VIOLATION',
      count: countType('Red Light Violation'),
      icon: <FaTrafficLight />,
      accuracy: '97.9%',
      isAlert: countType('Red Light Violation') > 0,
    },
    {
      label: 'PLATES RECOGNIZED',
      count: r.plates_recognized?.length || 0,
      icon: <FaSquareParking />,
      accuracy: '92.0%',
      isAlert: false,
    },
  ];

  return (
    <section>
      <div className="section-header">
        <div className="section-icon"><FaClipboardList /></div>
        <h2 className="section-title">DETECTION RESULTS</h2>
      </div>

      <div className="results-grid">
        {cards.map((card, i) => (
          <div key={i} className={`result-card ${card.isAlert ? 'alert' : ''}`}>
            <div className="result-header">
              <span className="result-label">{card.label}</span>
              <span className="result-icon">{card.icon}</span>
            </div>
            <div className="result-count">{card.count}</div>
            <div className="result-meta">
              <span className="result-confidence">{card.accuracy} ACC</span>
              <span className={`result-status ${card.isAlert ? 'violation' : 'normal'}`}>
                {card.isAlert ? 'VIOLATION' : 'NORMAL'}
              </span>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
