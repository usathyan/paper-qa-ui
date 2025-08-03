import React, { useState, useEffect, useRef, useCallback } from 'react';
import axios from 'axios';

interface Paper {
  docname: string;
  citation: string;
}

function Library() {
  const [papers, setPapers] = useState<Paper[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const fetchPapers = useCallback(async () => {
    console.log('Fetching papers...');
    try {
      const response = await axios.get('http://127.0.0.1:8000/api/papers');
      setPapers(response.data);
      console.log('Fetched papers:', response.data);
    } catch (error) {
      console.error('Error fetching papers:', error);
    }
  }, []);

  useEffect(() => {
    fetchPapers();
  }, [fetchPapers]);

  const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    console.log('handleFileChange called');
    const file = event.target.files && event.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    try {
      await axios.post('http://127.0.0.1:8000/api/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      // Refresh the paper list after upload
      fetchPapers();
      console.log('File uploaded, fetching papers...');
    } catch (error) {
      console.error('Error uploading file:', error);
    }
  };

  const handleAddPaperClick = () => {
    fileInputRef.current?.click();
  };

  const handleDeleteClick = async (docname: string) => {
    try {
      await axios.delete(`http://127.0.0.1:8000/api/papers/${docname}`);
      // Refresh the paper list after deletion
      fetchPapers();
    } catch (error) {
      console.error('Error deleting paper:', error);
    }
  };

  return (
    <div className="container">
      <h1 className="page-title">My Library</h1>
      <div className="toolbar">
        <div className="search-library">
          <input type="text" placeholder="Search my papers..." />
        </div>
        <input
          type="file"
          ref={fileInputRef}
          style={{ display: 'none' }}
          onChange={handleFileChange}
          accept=".pdf"
        />
        <button className="add-paper-btn" onClick={handleAddPaperClick}>+ Add Paper</button>
      </div>

      <table className="paper-table">
        <thead>
          <tr>
            <th>Name</th>
            <th>Citation</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {papers.map((paper) => (
            <tr key={paper.docname}>
              <td>{paper.docname}</td>
              <td>{paper.citation}</td>
              <td className="actions">
                <a href="#">View</a>
                <a href="#" onClick={() => handleDeleteClick(paper.docname)}>Delete</a>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default Library;
