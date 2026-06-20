import React, { useState, useEffect } from 'react';
import { FiShield, FiUploadCloud, FiFileText, FiBarChart2 } from 'react-icons/fi';
import './Sidebar.css';

const Sidebar = () => {
  const [activeSection, setActiveSection] = useState('hero-section');

  useEffect(() => {
    const handleScroll = () => {
      const sections = ['hero-section', 'upload-panel', 'violations-table', 'analytics-panel'];
      const scrollPosition = window.scrollY + 150; // Offset for header

      for (const section of sections) {
        const element = document.getElementById(section);
        if (element) {
          const top = element.offsetTop;
          const bottom = top + element.offsetHeight;

          if (scrollPosition >= top && scrollPosition < bottom) {
            setActiveSection(section);
          }
        }
      }
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const scrollToSection = (sectionId) => {
    const element = document.getElementById(sectionId);
    if (element) {
      window.scrollTo({
        top: element.offsetTop - 80, // Account for header height
        behavior: 'smooth'
      });
    }
  };

  const navItems = [
    { id: 'hero-section', label: 'Overview', icon: <FiShield size={20} /> },
    { id: 'upload-panel', label: 'Process Evidence', icon: <FiUploadCloud size={20} /> },
    { id: 'violations-table', label: 'Violations Log', icon: <FiFileText size={20} /> },
    { id: 'analytics-panel', label: 'Analytics', icon: <FiBarChart2 size={20} /> },
  ];

  return (
    <nav className="sidebar">
      <ul className="sidebar-nav">
        {navItems.map((item) => (
          <li key={item.id} className="sidebar-item">
            <button
              className={`sidebar-link ${activeSection === item.id ? 'active' : ''}`}
              onClick={() => scrollToSection(item.id)}
            >
              <span className="sidebar-icon">{item.icon}</span>
              <span className="sidebar-label">{item.label}</span>
            </button>
          </li>
        ))}
      </ul>
    </nav>
  );
};

export default Sidebar;
