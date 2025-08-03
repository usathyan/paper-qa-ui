import React, { useState } from 'react';
import axios from 'axios';

function Query() {
  const [query, setQuery] = useState('');
  const [answer, setAnswer] = useState('');
  const [loading, setLoading] = useState(false);
  const [selectedSource, setSelectedSource] = useState('public');
  const [thinkingDetails, setThinkingDetails] = useState('');
  const [useStreaming, setUseStreaming] = useState(true);
  const [streamingUpdates, setStreamingUpdates] = useState<string[]>([]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setAnswer('');
    setThinkingDetails('');
    setStreamingUpdates([]);

    if (useStreaming) {
      // Use streaming endpoint
      try {
        console.log('Sending streaming query:', { query, source: selectedSource });
        
        const response = await fetch('http://127.0.0.1:8000/api/query/stream', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            query: query.trim(),
            source: selectedSource,
          }),
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const reader = response.body?.getReader();
        if (!reader) {
          throw new Error('No response body');
        }

        const decoder = new TextDecoder();
        let finalAnswer = '';

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const chunk = decoder.decode(value);
          const lines = chunk.split('\n');

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const data = JSON.parse(line.slice(6));
                console.log('Streaming update:', data);

                switch (data.type) {
                  case 'thinking':
                    setStreamingUpdates(prev => [...prev, `🤔 ${data.content}`]);
                    break;
                  case 'evidence':
                    setStreamingUpdates(prev => [...prev, `📄 ${data.content}`]);
                    break;
                  case 'answer':
                    finalAnswer = data.content;
                    setAnswer(data.content);
                    break;
                  case 'complete':
                    setStreamingUpdates(prev => [...prev, `✅ ${data.content}`]);
                    break;
                  case 'error':
                    setAnswer(`Error: ${data.content}`);
                    break;
                }
              } catch (e) {
                console.error('Error parsing streaming data:', e);
              }
            }
          }
        }

        if (!finalAnswer) {
          setAnswer('No answer received from streaming endpoint.');
        }

      } catch (error: any) {
        console.error('Error in streaming query:', error);
        setAnswer(`Streaming error: ${error.message}`);
      } finally {
        setLoading(false);
      }
    } else {
      // Use regular endpoint
      try {
        console.log('Sending regular query:', { query, source: selectedSource });
        
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
    }
  };

  return (
    <div className="main-content">
      <div className="logo">PaperQA Discovery</div>

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

        {/* Streaming Toggle */}
        <div className="streaming-toggle" style={{ marginBottom: '20px', textAlign: 'center' }}>
          <label style={{ fontSize: '14px', cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={useStreaming}
              onChange={(e) => setUseStreaming(e.target.checked)}
              style={{ marginRight: '5px' }}
            />
            🚀 Enable Real-time Streaming (See AI thinking process)
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

        {/* Streaming Updates */}
        {useStreaming && streamingUpdates.length > 0 && (
          <div className="streaming-updates" style={{
            marginTop: '20px',
            padding: '15px',
            backgroundColor: '#f0f8ff',
            borderRadius: '8px',
            border: '1px solid #b3d9ff',
            maxHeight: '300px',
            overflowY: 'auto'
          }}>
            <h4 style={{ margin: '0 0 10px 0', color: '#0066cc' }}>🔄 Real-time Updates:</h4>
            <div style={{
              fontSize: '14px',
              lineHeight: '1.4'
            }}>
              {streamingUpdates.map((update, index) => (
                <div key={index} style={{
                  marginBottom: '8px',
                  padding: '4px 0',
                  borderBottom: index < streamingUpdates.length - 1 ? '1px solid #e6f3ff' : 'none'
                }}>
                  {update}
                </div>
              ))}
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
