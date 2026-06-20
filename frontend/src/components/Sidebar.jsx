import React, { useState, useEffect } from 'react';
import { FiShield, FiUploadCloud, FiFileText, FiBarChart2, FiDownload, FiChevronRight, FiChevronLeft } from 'react-icons/fi';
import './Sidebar.css';

const Sidebar = ({ onExportCSV, isPinned, setIsPinned }) => {
  const [activeSection, setActiveSection] = useState('hero-section');
  const [isHovered, setIsHovered] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      const sections = ['hero-section', 'upload-panel', 'violations-table', 'analytics-panel'];
      const scrollPosition = window.scrollY + 150; 

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
        top: element.offsetTop - 80, 
        behavior: 'smooth'
      });
    }
  };

  const navItems = [
    { id: 'hero-section', label: 'Overview', icon: <FiShield size={22} /> },
    { id: 'upload-panel', label: 'Process Evidence', icon: <FiUploadCloud size={22} /> },
    { id: 'violations-table', label: 'Violations Log', icon: <FiFileText size={22} /> },
    { id: 'analytics-panel', label: 'Analytics', icon: <FiBarChart2 size={22} /> },
  ];

  const expanded = isPinned || isHovered;

  return (
    <>
      <nav 
        className={`sidebar ${expanded ? 'expanded' : 'collapsed'}`}
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
      >
        <div className="sidebar-toggle-container">
          <button 
            className="sidebar-toggle" 
            onClick={() => setIsPinned(!isPinned)}
            title={isPinned ? "Unpin Sidebar" : "Pin Sidebar"}
          >
            {isPinned ? <FiChevronLeft size={20} /> : <FiChevronRight size={20} />}
          </button>
        </div>

        <ul className="sidebar-nav">
          {navItems.map((item) => (
            <li key={item.id} className="sidebar-item">
              <button
                className={`sidebar-link ${activeSection === item.id ? 'active' : ''}`}
                onClick={() => scrollToSection(item.id)}
                title={!expanded ? item.label : ''}
              >
                <span className="sidebar-icon">{item.icon}</span>
                <span className="sidebar-label">{item.label}</span>
              </button>
            </li>
          ))}
          
          <li className="sidebar-item download-item">
            <button
              className="sidebar-link download-btn"
              onClick={() => onExportCSV('weekly')}
              title={!expanded ? 'Download Reports' : ''}
            >
              <span className="sidebar-icon"><FiDownload size={22} /></span>
              <span className="sidebar-label">Download CSV</span>
            </button>
          </li>
        </ul>
      </nav>
      <div className={`sidebar-spacer ${expanded ? 'expanded' : 'collapsed'}`}></div>
    </>
  );
};

export default Sidebar;
