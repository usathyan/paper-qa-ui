#!/usr/bin/env python3
"""
Focused Semantic Scholar API Test
Handles rate limiting and shows more relevant PICALM results
"""

import os
import requests
import time
import json
from typing import Dict, List, Optional
from datetime import datetime


class SemanticScholarAPI:
    """Simple wrapper for Semantic Scholar API with rate limiting"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.base_url = "https://api.semanticscholar.org/graph/v1"
        self.api_key = api_key or os.getenv("SEMANTIC_SCHOLAR_API_KEY")
        self.headers = {"x-api-key": self.api_key} if self.api_key else {}
        self.last_request_time = 0
        self.min_interval = 2.0  # 2 seconds between requests for non-API key users
    
    def _rate_limit(self):
        """Implement rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_interval:
            sleep_time = self.min_interval - time_since_last
            print(f"⏳ Rate limiting: waiting {sleep_time:.1f} seconds...")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def search_papers(self, query: str, limit: int = 10, offset: int = 0) -> Dict:
        """Search for papers with rate limiting"""
        self._rate_limit()
        
        endpoint = f"{self.base_url}/paper/search"
        
        params = {
            "query": query,
            "limit": min(limit, 100),
            "offset": offset,
            "fields": "title,abstract,year,citationCount,url,venue,publicationDate,authors"
        }
        
        print(f"🔍 Searching: '{query}'")
        
        try:
            response = requests.get(endpoint, params=params, headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Found {data.get('total', 0)} papers")
                return data
            elif response.status_code == 429:
                print(f"⚠️ Rate limited. Waiting 5 seconds...")
                time.sleep(5)
                return self.search_papers(query, limit, offset)  # Retry
            else:
                print(f"❌ Error {response.status_code}: {response.text}")
                return {"error": response.text, "status_code": response.status_code}
                
        except Exception as e:
            print(f"❌ Exception: {str(e)}")
            return {"error": str(e)}


def test_picalm_specific_queries():
    """Test specific PICALM-related queries"""
    
    print("🧪 Focused PICALM Search Test")
    print("=" * 50)
    
    api = SemanticScholarAPI()
    
    # More specific PICALM queries
    queries = [
        "PICALM protein structure",
        "PICALM endocytosis",
        "PICALM Alzheimer's disease genetics",
        "PICALM clathrin",
        "PICALM amyloid beta",
        "PICALM therapeutic target"
    ]
    
    all_papers = []
    
    for i, query in enumerate(queries):
        print(f"\n{'='*40}")
        print(f"Query {i+1}/{len(queries)}: {query}")
        print(f"{'='*40}")
        
        results = api.search_papers(query, limit=5)
        
        if "error" not in results:
            papers = results.get("data", [])
            
            for j, paper in enumerate(papers):
                print(f"\n📄 {j+1}. {paper.get('title', 'N/A')}")
                print(f"   Year: {paper.get('year', 'N/A')}")
                print(f"   Citations: {paper.get('citationCount', 0)}")
                print(f"   Venue: {paper.get('venue', 'N/A')}")
                
                if paper.get('abstract'):
                    abstract = paper['abstract'][:150] + "..." if len(paper['abstract']) > 150 else paper['abstract']
                    print(f"   Abstract: {abstract}")
                
                all_papers.append(paper)
        else:
            print(f"❌ Failed: {results['error']}")
    
    # Analysis
    print(f"\n{'='*50}")
    print("📊 ANALYSIS")
    print(f"{'='*50}")
    print(f"Total papers found: {len(all_papers)}")
    
    # Find papers with PICALM in title or abstract
    picalm_papers = []
    for paper in all_papers:
        title = paper.get('title', '').lower()
        abstract = paper.get('abstract', '').lower() if paper.get('abstract') else ''
        if 'picalm' in title or 'picalm' in abstract:
            picalm_papers.append(paper)
    
    print(f"Papers mentioning PICALM: {len(picalm_papers)}")
    
    if picalm_papers:
        print(f"\n🎯 RELEVANT PICALM PAPERS:")
        for i, paper in enumerate(picalm_papers[:5]):
            print(f"{i+1}. {paper.get('title', 'N/A')}")
            print(f"   Year: {paper.get('year', 'N/A')}")
            print(f"   Citations: {paper.get('citationCount', 0)}")
            print(f"   URL: {paper.get('url', 'N/A')}")
            print()


def test_alzheimers_specific():
    """Test Alzheimer's specific queries"""
    
    print("\n🧠 Alzheimer's Disease Specific Search")
    print("=" * 50)
    
    api = SemanticScholarAPI()
    
    queries = [
        "Alzheimer's disease PICALM gene",
        "PICALM Alzheimer's risk factor",
        "PICALM amyloid beta clearance",
        "PICALM endocytosis Alzheimer's"
    ]
    
    for query in queries:
        print(f"\n🔍 Testing: {query}")
        results = api.search_papers(query, limit=3)
        
        if "error" not in results:
            papers = results.get("data", [])
            print(f"Found {len(papers)} papers")
            
            for i, paper in enumerate(papers):
                title = paper.get('title', 'N/A')
                year = paper.get('year', 'N/A')
                citations = paper.get('citationCount', 0)
                print(f"  {i+1}. {title} ({year}) - {citations} citations")
        else:
            print(f"  ❌ Error: {results['error']}")


def test_structural_biology():
    """Test structural biology related queries"""
    
    print("\n🔬 Structural Biology Search")
    print("=" * 50)
    
    api = SemanticScholarAPI()
    
    queries = [
        "PICALM protein structure X-ray",
        "PICALM NMR structure",
        "PICALM cryo-EM structure",
        "PICALM domain structure"
    ]
    
    for query in queries:
        print(f"\n🔍 Testing: {query}")
        results = api.search_papers(query, limit=3)
        
        if "error" not in results:
            papers = results.get("data", [])
            print(f"Found {len(papers)} papers")
            
            for i, paper in enumerate(papers):
                title = paper.get('title', 'N/A')
                year = paper.get('year', 'N/A')
                citations = paper.get('citationCount', 0)
                print(f"  {i+1}. {title} ({year}) - {citations} citations")
        else:
            print(f"  ❌ Error: {results['error']}")


if __name__ == "__main__":
    print("🚀 Starting Focused Semantic Scholar Test")
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Test PICALM specific queries
        test_picalm_specific_queries()
        
        # Test Alzheimer's specific
        test_alzheimers_specific()
        
        # Test structural biology
        test_structural_biology()
        
        print(f"\n✅ Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc() 