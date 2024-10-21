import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import './App.css';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faRobot, faSpinner, faUpload, faFileVideo, faCopy, faTrashAlt, faEnvelope } from '@fortawesome/free-solid-svg-icons';
import { faTwitter, faLinkedin, faGithub } from '@fortawesome/free-brands-svg-icons';

const CHUNK_SIZE = 5 * 1024 * 1024; // 5MB chunks
const BACKEND_URL = 'https://frame-insight-ai.onrender.com/';

const loadingMessages = [
  "Initializing neural network pathways...",
  "Analyzing video frames with quantum algorithms...",
  "Synthesizing deep learning models...",
  "Optimizing AI perception matrices..."
];

function App() {
  const [file, setFile] = useState(null);
  const [analysisType, setAnalysisType] = useState('general');
  const [customPrompt, setCustomPrompt] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [progress, setProgress] = useState(0);
  const [analysisTypes, setAnalysisTypes] = useState({});
  const [copySuccess, setCopySuccess] = useState('');
  const [loadingMessageIndex, setLoadingMessageIndex] = useState(0);
  const appRef = useRef(null);
  const [hideFooter, setHideFooter] = useState(false);
  const resultRef = useRef(null);
  const [lastScrollY, setLastScrollY] = useState(0);

  useEffect(() => {
    fetchAnalysisTypes();
  }, []);

  useEffect(() => {
    let interval;
    if (loading) {
      interval = setInterval(() => {
        setProgress((prevProgress) => {
          if (prevProgress >= 100) {
            clearInterval(interval);
            return 100;
          }
          return prevProgress + 1;
        });
        setLoadingMessageIndex((prevIndex) => (prevIndex + 1) % loadingMessages.length);
      }, 1000); // Update every second
    }
    return () => clearInterval(interval);
  }, [loading]);

  useEffect(() => {
    const handleScroll = () => {
      if (resultRef.current) {
        const rect = resultRef.current.getBoundingClientRect();
        if (rect.top < window.innerHeight) {
          setHideFooter(true);
        } else {
          setHideFooter(false);
        }
      }
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  useEffect(() => {
    const handleScroll = () => {
      const currentScrollY = window.scrollY;
      
      if (currentScrollY > lastScrollY) {
        setHideFooter(true);
      } else {
        setHideFooter(false);
      }

      setLastScrollY(currentScrollY);
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, [lastScrollY]);

  const fetchAnalysisTypes = async () => {
    try {
      const response = await axios.get(`${BACKEND_URL}/analysis_types`);
      setAnalysisTypes(response.data);
    } catch (error) {
      console.error('Error fetching analysis types:', error);
    }
  };

  const uploadChunk = async (chunk, chunkNumber, totalChunks) => {
    const formData = new FormData();
    formData.append('chunk', chunk);
    formData.append('chunk_number', chunkNumber);
    formData.append('total_chunks', totalChunks);
    formData.append('analysis_type', analysisType);
    formData.append('custom_prompt', customPrompt);

    const response = await axios.post(`${BACKEND_URL}/upload_chunk`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (progressEvent) => {
        const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        setProgress((prevProgress) => {
          const chunkProgress = (percentCompleted / totalChunks) + ((chunkNumber - 1) / totalChunks * 100);
          return Math.min(prevProgress + 1, chunkProgress);
        });
      },
    });

    return response.data;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) {
      setError('Please select a file');
      return;
    }
    setLoading(true);
    setError(null);
    setResult(null);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('analysis_type', analysisType);
    if (analysisType === 'custom') {
      formData.append('custom_prompt', customPrompt);
    }

    try {
      const response = await axios.post(`${BACKEND_URL}/upload`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          setProgress(percentCompleted);
        },
      });
      setResult(response.data);
    } catch (error) {
      setError(error.response?.data?.detail || 'An error occurred during processing');
    } finally {
      setLoading(false);
    }
  };

  const clearCache = async () => {
    try {
      await axios.post(`${BACKEND_URL}/clear_cache`);
      alert('Cache cleared successfully');
    } catch (error) {
      console.error('Error clearing cache:', error);
      alert('Failed to clear cache');
    }
  };

  const formatAnalysisForClipboard = (result) => {
    let formattedText = `Analysis Result\n\n`;
    formattedText += `Analysis Type: ${result.analysis_type}\n`;
    if (result.custom_prompt) {
      formattedText += `Custom Prompt: ${result.custom_prompt}\n`;
    }
    formattedText += `Frames extracted: ${result.frames_extracted}\n\n`;
    formattedText += `GPT-4 Analysis:\n${formatText(result.analysis)}\n`;
    return formattedText;
  };

  const copyToClipboard = (result) => {
    const formattedText = formatAnalysisForClipboard(result);
    navigator.clipboard.writeText(formattedText).then(() => {
      setCopySuccess('Copied!');
      setTimeout(() => setCopySuccess(''), 2000);
    }, (err) => {
      console.error('Failed to copy text: ', err);
    });
  };

  const formatText = (text) => {
    // Replace numbered list items with styled ones
    text = text.replace(/(\d+\.\s)(.+)/g, '$1$2');
    
    // Replace asterisks with actual bold and italic text
    text = text.replace(/\*\*(.+?)\*\*/g, '$1');
    text = text.replace(/\*(.+?)\*/g, '$1');
    
    // Replace hashtags with actual headers
    text = text.replace(/^###\s(.+)$/gm, '$1');
    text = text.replace(/^##\s(.+)$/gm, '$1');
    text = text.replace(/^#\s(.+)$/gm, '$1');

    return text;
  };

  const renderAnalysis = (analysis) => {
    if (typeof analysis === 'string') {
      return (
        <div className="analysis-content">
          {analysis.split('\n\n').map((paragraph, index) => (
            <p key={index} dangerouslySetInnerHTML={{ __html: formatText(paragraph) }} />
          ))}
        </div>
      );
    } else if (typeof analysis === 'object') {
      return (
        <div className="analysis-content">
          <pre>{JSON.stringify(analysis, null, 2)}</pre>
        </div>
      );
    }
    return null;
  };

  const renderAnalysisTypeDescription = (type) => {
    if (type === 'custom') {
      return (
        <div className="form-group custom-prompt-group">
          <label htmlFor="custom-prompt">Custom Prompt:</label>
          <textarea
            id="custom-prompt"
            value={customPrompt}
            onChange={(e) => setCustomPrompt(e.target.value)}
            placeholder="Enter your custom analysis prompt"
            rows="4"
          />
        </div>
      );
    }
    return (
      <div className="form-group">
        <p className="analysis-type-description">{analysisTypes[type]}</p>
      </div>
    );
  };

  const handleRefresh = () => {
    window.location.reload();
  };

  return (
    <div className="app-wrapper">
      <div className="app-container" ref={appRef}>
        <header className="app-header">
          <div className="logo-container" onClick={handleRefresh}>
            <FontAwesomeIcon icon={faRobot} className="app-logo" />
            <h1>FrameInsight AI</h1>
          </div>
        </header>
        <form onSubmit={handleSubmit} className="upload-form">
          <div className="form-group">
            <label htmlFor="file-upload">
              <FontAwesomeIcon icon={faFileVideo} /> Select Video File:
            </label>
            <input
              id="file-upload"
              type="file"
              onChange={(e) => setFile(e.target.files[0])}
              accept="video/*"
            />
          </div>
          <div className="form-group">
            <label htmlFor="analysis-type">Select Analysis Type:</label>
            <select
              id="analysis-type"
              value={analysisType}
              onChange={(e) => setAnalysisType(e.target.value)}
            >
              {Object.entries(analysisTypes).map(([key, value]) => (
                <option key={key} value={key}>{key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</option>
              ))}
            </select>
          </div>
          {renderAnalysisTypeDescription(analysisType)}
          <div className="button-group">
            <button type="submit" disabled={loading}>
              {loading ? (
                <>
                  <FontAwesomeIcon icon={faSpinner} spin /> Processing...
                </>
              ) : (
                <>
                  <FontAwesomeIcon icon={faUpload} /> Upload and Analyze
                </>
              )}
            </button>
            <button onClick={clearCache} className="clear-cache-btn" type="button">
              <FontAwesomeIcon icon={faTrashAlt} /> Clear Cache
            </button>
          </div>
        </form>
        {loading && (
          <div className="loading-container">
            <div className="loading-spinner">
              <FontAwesomeIcon icon={faSpinner} spin />
            </div>
            <p className="loading-message">{loadingMessages[loadingMessageIndex]}</p>
            <progress value={progress} max="100"></progress>
            <p>{Math.round(progress)}% complete</p>
          </div>
        )}
        {error && <p className="error">{error}</p>}
        {result && (
          <div className="result-container" ref={resultRef}>
            <h2>Analysis Result</h2>
            <p><strong>Analysis Type:</strong> <span className="highlight">{result.analysis_type}</span></p>
            {result.custom_prompt && <p><strong>Custom Prompt:</strong> <span className="highlight">{result.custom_prompt}</span></p>}
            {result.chunks ? (
              result.chunks.map((chunk, index) => (
                <div key={index} className="chunk-result">
                  <h3>Chunk {chunk.chunk_number} of {chunk.total_chunks}</h3>
                  <p><strong>Frames extracted:</strong> <span className="highlight">{chunk.frames_extracted}</span></p>
                  <h4>GPT-4 Analysis:</h4>
                  {renderAnalysis(chunk.analysis)}
                </div>
              ))
            ) : (
              <>
                <p><strong>Frames extracted:</strong> <span className="highlight">{result.frames_extracted}</span></p>
                <h3>GPT-4 Analysis:</h3>
                {renderAnalysis(result.analysis)}
              </>
            )}
            <div className="copy-button-container">
              <button onClick={() => copyToClipboard(result)} className="copy-button">
                <FontAwesomeIcon icon={faCopy} /> Copy to Clipboard
              </button>
            </div>
          </div>
        )}
      </div>
      <footer className={`app-footer ${hideFooter ? 'hide' : ''}`}>
        <div className="footer-content">
          <div className="social-links">
            <a href="https://twitter.com/frameinsightai" target="_blank" rel="noopener noreferrer">
              <FontAwesomeIcon icon={faTwitter} />
            </a>
            <a href="https://linkedin.com/company/frameinsightai" target="_blank" rel="noopener noreferrer">
              <FontAwesomeIcon icon={faLinkedin} />
            </a>
            <a href="https://github.com/frameinsightai" target="_blank" rel="noopener noreferrer">
              <FontAwesomeIcon icon={faGithub} />
            </a>
          </div>
          <div className="contact-info">
            <FontAwesomeIcon icon={faEnvelope} /> contact@frameinsightai.com
          </div>
          <div className="copyright">
            © 2024 FrameInsight AI. All rights reserved.
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
