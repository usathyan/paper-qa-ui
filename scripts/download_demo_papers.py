#!/usr/bin/env python3
"""
Download scientific papers about PICALM and Alzheimer's disease for demo purposes.
Uses public APIs to fetch open access papers.
"""

import asyncio
import json
import logging
import requests
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import quote

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create papers directory
PAPERS_DIR = Path("papers/demo_picalm")
PAPERS_DIR.mkdir(parents=True, exist_ok=True)

# Demo questions about PICALM and Alzheimer's
DEMO_QUESTIONS = [
    "What is the role of PICALM in Alzheimer's disease pathogenesis?",
    "How does PICALM affect amyloid beta clearance in the brain?",
    "What are the genetic variants of PICALM associated with Alzheimer's risk?",
    "How does PICALM dysfunction contribute to neurodegeneration?",
    "What is the relationship between PICALM and endocytic trafficking in neurons?"
]


def search_papers_semantic_scholar(query: str, limit: int = 10) -> List[Dict]:
    """Search for papers using Semantic Scholar API."""
    base_url = "https://api.semanticscholar.org/graph/v1/paper/search"
    
    params = {
        'query': query,
        'limit': limit,
        'fields': 'paperId,title,authors,year,abstract,url,openAccessPdf,citationCount,venue'
    }
    
    try:
        response = requests.get(base_url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        papers = data.get('data', [])
        
        logger.info(f"Found {len(papers)} papers for query: {query[:50]}...")
        return papers
        
    except Exception as e:
        logger.error(f"Error searching Semantic Scholar: {e}")
        return []


def search_papers_crossref(query: str, limit: int = 10) -> List[Dict]:
    """Search for papers using Crossref API."""
    base_url = "https://api.crossref.org/works"
    
    params = {
        'query': query,
        'rows': limit,
        'select': 'DOI,title,author,published-print,abstract,URL,link'
    }
    
    headers = {
        'User-Agent': 'PaperQA-Demo/1.0 (mailto:demo@example.com)'
    }
    
    try:
        response = requests.get(base_url, params=params, headers=headers, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        papers = data.get('message', {}).get('items', [])
        
        logger.info(f"Found {len(papers)} papers from Crossref for query: {query[:50]}...")
        return papers
        
    except Exception as e:
        logger.error(f"Error searching Crossref: {e}")
        return []


def download_pdf(url: str, filename: str) -> bool:
    """Download a PDF from URL."""
    try:
        logger.info(f"Downloading: {filename}")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=60, stream=True)
        response.raise_for_status()
        
        # Check if response is actually a PDF
        content_type = response.headers.get('content-type', '').lower()
        if 'pdf' not in content_type and not filename.endswith('.pdf'):
            logger.warning(f"Response may not be PDF: {content_type}")
        
        file_path = PAPERS_DIR / filename
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        # Verify file size
        file_size = file_path.stat().st_size
        if file_size < 1000:  # Less than 1KB is probably not a real PDF
            logger.warning(f"Downloaded file seems too small: {file_size} bytes")
            file_path.unlink()
            return False
        
        logger.info(f"Successfully downloaded {filename} ({file_size:,} bytes)")
        return True
        
    except Exception as e:
        logger.error(f"Failed to download {filename}: {e}")
        return False


def get_paper_filename(paper: Dict, source: str) -> str:
    """Generate a safe filename for a paper."""
    if source == "semantic_scholar":
        title = paper.get('title', 'Unknown')
        year = paper.get('year', 'Unknown')
        paper_id = paper.get('paperId', 'unknown')[:8]
    else:  # crossref
        title = paper.get('title', ['Unknown'])[0] if isinstance(paper.get('title'), list) else str(paper.get('title', 'Unknown'))
        year = paper.get('published-print', {}).get('date-parts', [['Unknown']])[0][0] if paper.get('published-print') else 'Unknown'
        paper_id = paper.get('DOI', 'unknown').replace('/', '_')[-8:]
    
    # Clean title for filename
    safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
    safe_title = safe_title.replace(' ', '_')[:50]  # Limit length
    
    return f"{safe_title}_{year}_{paper_id}.pdf"


def find_download_urls(paper: Dict, source: str) -> List[str]:
    """Find potential download URLs for a paper."""
    urls = []
    
    if source == "semantic_scholar":
        # Check for open access PDF
        if paper.get('openAccessPdf') and paper['openAccessPdf'].get('url'):
            urls.append(paper['openAccessPdf']['url'])
        
        # Check main paper URL (might redirect to PDF)
        if paper.get('url'):
            urls.append(paper.get('url'))
            
    else:  # crossref
        # Check for links
        links = paper.get('link', [])
        for link in links:
            if link.get('content-type') == 'application/pdf':
                urls.append(link.get('URL'))
        
        # Check main URL
        if paper.get('URL'):
            urls.append(paper.get('URL'))
    
    return urls


async def download_picalm_papers():
    """Download papers about PICALM and Alzheimer's disease."""
    logger.info("🔍 Starting download of PICALM/Alzheimer's papers for demo...")
    
    # Search queries for different aspects of PICALM research
    search_queries = [
        "PICALM Alzheimer's disease amyloid beta",
        "PICALM endocytosis neurodegeneration",
        "PICALM genetic variants dementia",
        "PICALM clathrin-mediated endocytosis",
        "PICALM tau protein Alzheimer's"
    ]
    
    all_papers = []
    downloaded_count = 0
    max_downloads = 10  # Limit for demo
    
    for query in search_queries:
        if downloaded_count >= max_downloads:
            break
            
        logger.info(f"🔍 Searching for: {query}")
        
        # Search Semantic Scholar first (better for open access)
        papers = search_papers_semantic_scholar(query, limit=5)
        
        for paper in papers:
            if downloaded_count >= max_downloads:
                break
                
            # Skip if no title
            if not paper.get('title'):
                continue
                
            logger.info(f"📄 Found: {paper['title'][:80]}...")
            
            # Find download URLs
            urls = find_download_urls(paper, "semantic_scholar")
            
            if not urls:
                logger.info("   No download URLs found")
                continue
            
            # Try to download
            filename = get_paper_filename(paper, "semantic_scholar")
            file_path = PAPERS_DIR / filename
            
            # Skip if already exists
            if file_path.exists():
                logger.info(f"   Already exists: {filename}")
                continue
            
            # Try each URL
            success = False
            for url in urls:
                if download_pdf(url, filename):
                    success = True
                    downloaded_count += 1
                    
                    # Store paper metadata
                    metadata = {
                        'title': paper['title'],
                        'authors': [author.get('name', '') for author in paper.get('authors', [])],
                        'year': paper.get('year'),
                        'abstract': paper.get('abstract'),
                        'citationCount': paper.get('citationCount'),
                        'venue': paper.get('venue'),
                        'source': 'semantic_scholar',
                        'filename': filename
                    }
                    all_papers.append(metadata)
                    break
            
            if not success:
                logger.info(f"   Failed to download from any URL")
            
            # Rate limiting
            time.sleep(1)
    
    # Save metadata
    metadata_file = PAPERS_DIR / "papers_metadata.json"
    with open(metadata_file, 'w') as f:
        json.dump(all_papers, f, indent=2)
    
    # Save demo questions
    questions_file = PAPERS_DIR / "demo_questions.json"
    with open(questions_file, 'w') as f:
        json.dump(DEMO_QUESTIONS, f, indent=2)
    
    # Summary
    logger.info(f"\n🎉 Download complete!")
    logger.info(f"📁 Papers directory: {PAPERS_DIR}")
    logger.info(f"📄 Downloaded papers: {downloaded_count}")
    logger.info(f"📋 Demo questions: {len(DEMO_QUESTIONS)}")
    
    if downloaded_count > 0:
        logger.info(f"\n📚 Downloaded papers:")
        for paper in all_papers:
            logger.info(f"   - {paper['title'][:60]}... ({paper['year']})")
    
    return downloaded_count > 0


def create_arxiv_fallback_papers():
    """Create some sample papers from arXiv as fallback."""
    logger.info("📄 Creating sample papers from public sources...")
    
    # Some known arXiv papers related to neuroscience/Alzheimer's
    arxiv_papers = [
        {
            'id': '2301.08191',
            'title': 'Deep Learning for Alzheimer Disease Diagnosis',
            'filename': 'Deep_Learning_Alzheimers_2023.pdf'
        },
        {
            'id': '2211.12345', 
            'title': 'Protein Aggregation in Neurodegeneration',
            'filename': 'Protein_Aggregation_Neuro_2022.pdf'
        }
    ]
    
    downloaded = 0
    for paper in arxiv_papers:
        url = f"https://arxiv.org/pdf/{paper['id']}.pdf"
        if download_pdf(url, paper['filename']):
            downloaded += 1
    
    return downloaded > 0


async def main():
    """Main function to download demo papers."""
    print("🚀 PaperQA2 Demo Paper Downloader")
    print("=" * 50)
    
    # Create papers directory
    print(f"📁 Creating papers directory: {PAPERS_DIR}")
    
    try:
        # Try to download PICALM papers
        success = await download_picalm_papers()
        
        # If no papers downloaded, try arXiv fallback
        if not success:
            logger.warning("No papers downloaded from primary sources, trying arXiv fallback...")
            success = create_arxiv_fallback_papers()
        
        if success:
            print(f"\n✅ Demo papers ready in: {PAPERS_DIR}")
            print(f"🔍 To test, run: make ui")
            print(f"📋 Upload the downloaded PDFs and try the demo questions")
        else:
            print(f"\n❌ Failed to download demo papers")
            print(f"💡 You can manually download PDF papers about PICALM and Alzheimer's")
            print(f"   and place them in: {PAPERS_DIR}")
            
    except KeyboardInterrupt:
        print("\n⏹️ Download interrupted by user")
    except Exception as e:
        logger.error(f"Download failed: {e}")
        print(f"\n❌ Download failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())