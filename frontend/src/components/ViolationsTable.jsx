import { useState } from 'react';
import {
  FaMagnifyingGlass, FaReceipt, FaEye
} from 'react-icons/fa6';

export default function ViolationsTable({ violations, onViewEvidence }) {
  const [search, setSearch] = useState('');
  const [typeFilter, setTypeFilter] = useState('ALL');
  const [violationFilter, setViolationFilter] = useState('ALL');

  const filtered = violations.filter(v => {
    const matchesSearch = !search ||
      (v.license_plate || '').toLowerCase().includes(search.toLowerCase()) ||
      (v.detection_id || '').toLowerCase().includes(search.toLowerCase()) ||
      (v.vehicle_type || '').toLowerCase().includes(search.toLowerCase());

    const matchesType = typeFilter === 'ALL' || v.vehicle_type === typeFilter;
    const matchesViolation = violationFilter === 'ALL' || v.violation_type === violationFilter;

    return matchesSearch && matchesType && matchesViolation;
  });

  const getViolationClass = (type) => {
    if (!type || type === 'None') return 'none';
    if (['Red Light Violation', 'Wrong Side Driving', 'No Helmet'].includes(type)) return 'critical';
    return 'warning';
  };

  return (
    <section id="violations">
      <div className="section-header">
        <div className="section-icon"><FaReceipt /></div>
        <h2 className="section-title">VIOLATION RECORDS DATABASE</h2>
      </div>

      <div className="glass-panel">
        <div className="table-controls">
          <div className="search-box">
            <FaMagnifyingGlass className="search-icon" />
            <input
              type="text"
              placeholder="Search license plate, ID, vehicle type..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>

          <select
            className="filter-select"
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
          >
            <option value="ALL">All Vehicle Types</option>
            <option value="Motorcycle">Motorcycle</option>
            <option value="Car">Car</option>
            <option value="Truck">Truck</option>
            <option value="Bus">Bus</option>
          </select>

          <select
            className="filter-select"
            value={violationFilter}
            onChange={(e) => setViolationFilter(e.target.value)}
          >
            <option value="ALL">All Violations</option>
            <option value="No Helmet">No Helmet</option>
            <option value="Triple Riding">Triple Riding</option>
            <option value="Red Light Violation">Red Light Violation</option>
            <option value="None">No Violation</option>
          </select>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table className="data-table">
            <thead>
              <tr>
                <th>Detection ID</th>
                <th>License Plate</th>
                <th>Vehicle Type</th>
                <th>Violation</th>
                <th>Timestamp</th>
                <th>Confidence</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {filtered.length === 0 ? (
                <tr>
                  <td colSpan="7" className="no-data-row">
                    {violations.length === 0
                      ? 'No violations recorded yet. Upload an image to start detection.'
                      : 'No matching records found.'}
                  </td>
                </tr>
              ) : (
                filtered.map((v, i) => (
                  <tr key={v.detection_id || i}>
                    <td>{v.detection_id || `TR-${i}`}</td>
                    <td>
                      <span className="plate-badge">{v.license_plate || 'N/A'}</span>
                    </td>
                    <td>{v.vehicle_type || 'Unknown'}</td>
                    <td>
                      <span className={`violation-tag ${getViolationClass(v.violation_type)}`}>
                        {v.violation_type || 'None'}
                      </span>
                    </td>
                    <td>{v.timestamp || '-'}</td>
                    <td className="confidence-val">
                      {v.confidence ? `${(v.confidence * 100).toFixed(1)}%` : '-'}
                    </td>
                    <td>
                      <button className="btn-view" onClick={() => onViewEvidence(v)}>
                        <FaEye /> View
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}
