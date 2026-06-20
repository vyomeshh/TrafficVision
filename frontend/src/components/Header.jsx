import { useState, useEffect } from 'react';
import { FaSatelliteDish, FaBell, FaBars } from 'react-icons/fa6';

export default function Header({ serverOnline }) {
  const [time, setTime] = useState('');

  useEffect(() => {
    const tick = () => {
      setTime(new Date().toUTCString().replace('GMT', 'UTC'));
    };
    tick();
    const timer = setInterval(tick, 1000);
    return () => clearInterval(timer);
  }, []);

  return (
    <header className="header">
      <div className="header-brand">
        <div className="header-logo">
          <FaSatelliteDish />
        </div>
        <div>
          <div className="header-title">TRAFFICVISION AI</div>
          <div className="header-subtitle">Smart City Enforcement Platform</div>
        </div>
      </div>

      <div className="header-controls">

        <div className="header-time">{time}</div>
      </div>
    </header>
  );
}
