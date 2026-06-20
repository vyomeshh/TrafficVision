import { useEffect, useRef } from 'react';
import {
  FaChartPie, FaCar, FaBan, FaCircleCheck, FaBolt,
  FaFileCsv, FaFilePdf
} from 'react-icons/fa6';

// Import Chart.js
import {
  Chart as ChartJS,
  ArcElement, Tooltip, Legend,
  CategoryScale, LinearScale,
  BarElement, PointElement, LineElement,
  Filler
} from 'chart.js';

ChartJS.register(
  ArcElement, Tooltip, Legend,
  CategoryScale, LinearScale,
  BarElement, PointElement, LineElement,
  Filler
);

// Chart color palette
const COLORS = {
  cyan: '#00f2fe',
  purple: '#b15cff',
  pink: '#f736ff',
  green: '#00ff87',
  orange: '#ffaa00',
  red: '#ff3366',
  yellow: '#f9d423',
  blue: '#4facfe',
};

export default function AnalyticsPanel({ analytics, onExportCSV }) {
  const pieRef = useRef(null);
  const barRef = useRef(null);
  const lineRef = useRef(null);
  const doughRef = useRef(null);
  const chartInstances = useRef({});

  // Default analytics data for when backend isn't available
  const defaultAnalytics = {
    total_stats: {
      total_vehicles: 143820,
      total_violations: 12953,
      avg_confidence: 96.75,
      avg_processing_ms: 120,
    },
    violation_distribution: {
      labels: ['Helmet', 'Seatbelt', 'Red Light', 'Wrong Side', 'Illegal Parking', 'Stop Line', 'Triple Riding'],
      data: [26, 18, 14, 11, 8, 15, 8],
    },
    daily_counts: {
      labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
      data: [120, 145, 130, 165, 190, 220, 205],
    },
    monthly_trend: {
      labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
      data: [8200, 9400, 10500, 11200, 12100, 12953],
    },
    vehicle_classification: {
      labels: ['Cars', 'Motorcycles', 'Trucks', 'Buses'],
      data: [55, 30, 10, 5],
    },
  };

  const data = analytics || defaultAnalytics;
  const stats = data.total_stats || defaultAnalytics.total_stats;

  // Build and destroy charts
  useEffect(() => {
    // Destroy existing charts
    Object.values(chartInstances.current).forEach(c => c?.destroy());

    const chartFont = { family: "'Inter', sans-serif" };
    ChartJS.defaults.color = '#8fa0c4';
    ChartJS.defaults.font.family = chartFont.family;

    // 1. Violation Distribution Pie
    if (pieRef.current) {
      const vd = data.violation_distribution || defaultAnalytics.violation_distribution;
      chartInstances.current.pie = new ChartJS(pieRef.current, {
        type: 'pie',
        data: {
          labels: vd.labels,
          datasets: [{
            data: vd.data,
            backgroundColor: [COLORS.cyan, COLORS.blue, COLORS.purple, COLORS.pink, COLORS.green, COLORS.yellow, COLORS.red],
            borderWidth: 1,
            borderColor: 'rgba(10, 18, 42, 0.8)',
          }],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { position: 'right', labels: { boxWidth: 12, font: { size: 10 } } } },
        },
      });
    }

    // 2. Daily Bar Chart
    if (barRef.current) {
      const dc = data.daily_counts || defaultAnalytics.daily_counts;
      chartInstances.current.bar = new ChartJS(barRef.current, {
        type: 'bar',
        data: {
          labels: dc.labels,
          datasets: [{
            label: 'Infractions',
            data: dc.data,
            backgroundColor: 'rgba(0, 242, 254, 0.45)',
            borderColor: COLORS.cyan,
            borderWidth: 1,
            borderRadius: 4,
          }],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { display: false } },
          scales: {
            x: { grid: { color: 'rgba(255,255,255,0.03)' } },
            y: { grid: { color: 'rgba(255,255,255,0.03)' } },
          },
        },
      });
    }

    // 3. Monthly Trend Line Chart
    if (lineRef.current) {
      const mt = data.monthly_trend || defaultAnalytics.monthly_trend;
      chartInstances.current.line = new ChartJS(lineRef.current, {
        type: 'line',
        data: {
          labels: mt.labels,
          datasets: [{
            label: 'Detections',
            data: mt.data,
            borderColor: COLORS.purple,
            backgroundColor: 'rgba(177, 92, 255, 0.08)',
            fill: true,
            tension: 0.4,
            borderWidth: 2,
            pointBackgroundColor: COLORS.pink,
          }],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { display: false } },
          scales: {
            x: { grid: { color: 'rgba(255,255,255,0.03)' } },
            y: { grid: { color: 'rgba(255,255,255,0.03)' } },
          },
        },
      });
    }

    // 4. Vehicle Classification Doughnut
    if (doughRef.current) {
      const vc = data.vehicle_classification || defaultAnalytics.vehicle_classification;
      chartInstances.current.doughnut = new ChartJS(doughRef.current, {
        type: 'doughnut',
        data: {
          labels: vc.labels,
          datasets: [{
            data: vc.data,
            backgroundColor: [COLORS.cyan, COLORS.purple, COLORS.green, COLORS.orange],
            borderWidth: 1,
            borderColor: 'rgba(10, 18, 42, 0.8)',
          }],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { position: 'right', labels: { boxWidth: 12, font: { size: 10 } } } },
          cutout: '70%',
        },
      });
    }

    return () => {
      Object.values(chartInstances.current).forEach(c => c?.destroy());
    };
  }, [analytics]);

  const kpis = [
    { label: 'TOTAL VEHICLES TRACKED', value: stats.total_vehicles?.toLocaleString() || '143,820', icon: <FaCar />, color: 'cyan' },
    { label: 'TOTAL VIOLATIONS', value: stats.total_violations?.toLocaleString() || '12,953', icon: <FaBan />, color: 'purple' },
    { label: 'AVG AI ACCURACY', value: `${stats.avg_confidence || 96.75}%`, icon: <FaCircleCheck />, color: 'green' },
    { label: 'AVG PROCESSING', value: `${stats.avg_processing_ms || 120} ms`, icon: <FaBolt />, color: 'orange' },
  ];

  return (
    <section id="analytics">
      <div className="section-header">
        <div className="section-icon"><FaChartPie /></div>
        <h2 className="section-title">ANALYTICS ENGINE</h2>
      </div>

      {/* KPI Cards */}
      <div className="analytics-kpi-grid">
        {kpis.map((kpi, i) => (
          <div key={i} className="kpi-card">
            <div className={`kpi-icon ${kpi.color}`}>{kpi.icon}</div>
            <div>
              <div className="kpi-label">{kpi.label}</div>
              <div className="kpi-value">{kpi.value}</div>
            </div>
          </div>
        ))}
      </div>

      {/* Charts Grid */}
      <div className="charts-grid">
        <div className="glass-panel chart-card">
          <div className="chart-title">Violation Category Distribution</div>
          <div className="chart-container">
            <canvas ref={pieRef} />
          </div>
        </div>

        <div className="glass-panel chart-card">
          <div className="chart-title">Daily Infraction Counts</div>
          <div className="chart-container">
            <canvas ref={barRef} />
          </div>
        </div>

        <div className="glass-panel chart-card">
          <div className="chart-title">Monthly Enforcement Trends</div>
          <div className="chart-container">
            <canvas ref={lineRef} />
          </div>
        </div>

        <div className="glass-panel chart-card">
          <div className="chart-title">Vehicle Classification</div>
          <div className="chart-container">
            <canvas ref={doughRef} />
          </div>
        </div>
      </div>

      {/* Export Buttons */}
      <div className="export-row">
        <button className="btn btn-secondary" onClick={() => onExportCSV('daily')}>
          <FaFileCsv /> Export Daily CSV
        </button>
        <button className="btn btn-secondary" onClick={() => onExportCSV('weekly')}>
          <FaFileCsv /> Export Weekly CSV
        </button>
        <button className="btn btn-primary" onClick={() => onExportCSV('monthly')}>
          <FaFilePdf /> Export Monthly Report
        </button>
      </div>
    </section>
  );
}
