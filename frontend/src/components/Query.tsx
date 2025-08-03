import React, { useState, useEffect } from 'react';
import axios from 'axios';

function Query() {
  const [query, setQuery] = useState('');
  const [answer, setAnswer] = useState('');
  const [loading, setLoading] = useState(false);
  const [selectedSource, setSelectedSource] = useState('all');
  const [backendStatus, setBackendStatus] = useState('Unknown');
  const [thinkingDetails, setThinkingDetails] = useState('');

  // Test backend connection on component mount
  useEffect(() => {
      const testBackend = async () => {
    try {
      await axios.get('http://127.0.0.1:8000/docs', {
        timeout: 5000
      });
      setBackendStatus('Connected');
      console.log('Backend connection successful');
    } catch (error: any) {
      setBackendStatus('Disconnected');
      console.error('Backend connection failed:', error);
    }
  };
    testBackend();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setAnswer('');
    setThinkingDetails('');

    try {
      console.log('Sending query:', { query, source: selectedSource });
      
      const response = await axios.post('http://127.0.0.1:8000/api/query', {
        query: query.trim(),
        source: selectedSource,
      }, {
        timeout: 120000, // 2 minutes timeout
        headers: {
          'Content-Type': 'application/json',
        }
      });
      
      console.log('Response received:', response.data);
      
      if (response.data && response.data.answer) {
        const answerText = response.data.answer.trim();
        console.log('Answer text:', answerText);
        
        // Show the actual PaperQA response instead of filtering it
        setAnswer(response.data.answer);

        // Set thinking details if available
        if (response.data.thinking_details) {
          setThinkingDetails(response.data.thinking_details);
        }
      } else {
        console.error('No answer in response:', response.data);
        setAnswer('No answer received from server. Check console for details.');
      }
    } catch (error: any) {
      console.error('Error fetching answer:', error);
      if (axios.isCancel(error)) {
        setAnswer('Request cancelled.');
      } else if (error.code === 'ECONNABORTED') {
        setAnswer('Request timed out. The query is taking too long to process.');
      } else if (error.response) {
        setAnswer(`Server error: ${error.response.status} - ${error.response.statusText}`);
      } else if (error.request) {
        setAnswer('Network error: Could not connect to server. Is the backend running?');
      } else {
        setAnswer('Error: ' + error.message);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="main-content">
      <div className="logo">PaperQA Discovery</div>
      
      {/* Backend Status */}
      <div style={{ fontSize: '12px', color: backendStatus === 'Connected' ? 'green' : 'red', marginBottom: '10px' }}>
        Backend Status: {backendStatus}
      </div>

      {/* Simple Chat Interface */}
      <div className="chat-container" style={{ maxWidth: '800px', margin: '0 auto' }}>
        
        {/* Source Selection */}
        <div className="source-selector" style={{ marginBottom: '20px', textAlign: 'center' }}>
          <label style={{ marginRight: '15px', fontSize: '14px' }}>
            <input
              type="radio"
              name="source"
              value="local"
              checked={selectedSource === 'local'}
              onChange={(e) => setSelectedSource(e.target.value)}
              style={{ marginRight: '5px' }}
            />
            Local Papers Only
          </label>
          <label style={{ marginRight: '15px', fontSize: '14px' }}>
            <input
              type="radio"
              name="source"
              value="public"
              checked={selectedSource === 'public'}
              onChange={(e) => setSelectedSource(e.target.value)}
              style={{ marginRight: '5px' }}
            />
            Public Sources Only
          </label>
          <label style={{ fontSize: '14px' }}>
            <input
              type="radio"
              name="source"
              value="all"
              checked={selectedSource === 'all'}
              onChange={(e) => setSelectedSource(e.target.value)}
              style={{ marginRight: '5px' }}
            />
            All Sources
          </label>
        </div>

        {/* Query Form */}
        <form onSubmit={handleSubmit} style={{ marginBottom: '20px' }}>
          <div style={{ display: 'flex', gap: '10px' }}>
            <input
              type="text"
              className="search-box"
              placeholder="Ask a question..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              style={{ flex: 1, padding: '12px', fontSize: '16px' }}
              disabled={loading}
            />
            <button
              type="submit"
              disabled={loading || !query.trim()}
              style={{
                padding: '12px 24px',
                backgroundColor: loading ? '#ccc' : '#007bff',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: loading ? 'not-allowed' : 'pointer',
                fontSize: '16px'
              }}
            >
              {loading ? 'Thinking...' : 'Ask'}
            </button>
          </div>
        </form>

        {/* Loading Indicator */}
        {loading && (
          <div className="loading-indicator" style={{ textAlign: 'center', margin: '20px 0' }}>
            <div style={{ fontSize: '18px', marginBottom: '10px' }}>🤔 Thinking...</div>
            <div style={{ fontSize: '14px', color: '#666' }}>
              This may take 30-60 seconds for complex queries
            </div>
          </div>
        )}

        {/* Answer */}
        {answer && !loading && (
          <div className="answer-container" style={{ 
            marginTop: '20px', 
            padding: '20px', 
            backgroundColor: '#f8f9fa', 
            borderRadius: '8px',
            border: '1px solid #e9ecef'
          }}>
            <h3 style={{ margin: '0 0 15px 0', color: '#495057' }}>Answer:</h3>
            <div className="formatted-answer" style={{ 
              fontSize: '16px', 
              lineHeight: '1.6',
              whiteSpace: 'pre-wrap'
            }}>
              {answer}
            </div>
          </div>
        )}

        {/* Thinking Details */}
        {thinkingDetails && !loading && (
          <div className="thinking-details-container" style={{
            marginTop: '20px',
            padding: '15px',
            backgroundColor: '#f0f8ff',
            borderRadius: '8px',
            border: '1px solid #b3d9ff'
          }}>
            <h4 style={{ margin: '0 0 10px 0', color: '#0066cc' }}>🤔 PaperQA Thinking Process:</h4>
            <pre style={{
              fontSize: '12px',
              color: '#333',
              whiteSpace: 'pre-wrap',
              wordWrap: 'break-word',
              margin: 0,
              fontFamily: 'monospace',
              maxHeight: '300px',
              overflowY: 'auto'
            }}>{thinkingDetails}</pre>
          </div>
        )}

        {/* Example Questions */}
        {!loading && !answer && (
          <div className="example-questions" style={{ 
            textAlign: 'center', 
            marginTop: '40px',
            color: '#666',
            fontSize: '14px'
          }}>
            <p>Try asking questions like:</p>
            <p>"What is PaperQA?" • "Summarize recent findings on KRAS inhibitors" • "What are the latest developments in AI?"</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default Query;
