#!/usr/bin/env python3
"""
Semantic Scholar API Test Script
Tests paper search functionality for PICALM and Alzheimer's research
Based on: https://www.semanticscholar.org/product/api/tutorial
"""

import os
import requests
import json
from typing import Dict, List, Optional
from datetime import datetime


class SemanticScholarAPI:
    """Simple wrapper for Semantic Scholar API"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.base_url = "https://api.semanticscholar.org/graph/v1"
        self.api_key = api_key or os.getenv("SEMANTIC_SCHOLAR_API_KEY")
        self.headers = {"x-api-key": self.api_key} if self.api_key else {}
    
    def search_papers(self, query: str, limit: int = 10, offset: int = 0, 
                     fields: str = "title,abstract,year,citationCount,url,venue,publicationDate") -> Dict:
        """
        Search for papers using Semantic Scholar API
        
        Args:
            query: Search query string
            limit: Number of results to return (max 100)
            offset: Number of results to skip
            fields: Comma-separated list of fields to return
            
        Returns:
            Dictionary containing search results
        """
        endpoint = f"{self.base_url}/paper/search"
        
        params = {
            "query": query,
            "limit": min(limit, 100),  # API limit is 100
            "offset": offset,
            "fields": fields
        }
        
        print(f"🔍 Searching for: '{query}'")
        print(f"📡 Endpoint: {endpoint}")
        print(f"🔑 Using API key: {'Yes' if self.api_key else 'No'}")
        
        try:
            response = requests.get(endpoint, params=params, headers=self.headers)
            
            print(f"📊 Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Found {data.get('total', 0)} total papers")
                print(f"📄 Returning {len(data.get('data', []))} papers")
                return data
            else:
                print(f"❌ Error: {response.status_code} - {response.text}")
                return {"error": response.text, "status_code": response.status_code}
                
        except Exception as e:
            print(f"❌ Exception: {str(e)}")
            return {"error": str(e)}
    
    def get_paper_details(self, paper_id: str, 
                         fields: str = "title,abstract,year,citationCount,url,venue,publicationDate,authors") -> Dict:
        """
        Get detailed information about a specific paper
        
        Args:
            paper_id: Semantic Scholar paper ID
            fields: Comma-separated list of fields to return
            
        Returns:
            Dictionary containing paper details
        """
        endpoint = f"{self.base_url}/paper/{paper_id}"
        
        params = {"fields": fields}
        
        print(f"📄 Getting details for paper: {paper_id}")
        
        try:
            response = requests.get(endpoint, params=params, headers=self.headers)
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ Error: {response.status_code} - {response.text}")
                return {"error": response.text, "status_code": response.status_code}
                
        except Exception as e:
            print(f"❌ Exception: {str(e)}")
            return {"error": str(e)}


def print_paper_summary(paper: Dict, index: int = 0):
    """Print a formatted summary of a paper"""
    print(f"\n📄 Paper {index + 1}:")
    print(f"   Title: {paper.get('title', 'N/A')}")
    print(f"   Year: {paper.get('year', 'N/A')}")
    print(f"   Citations: {paper.get('citationCount', 0)}")
    print(f"   Venue: {paper.get('venue', 'N/A')}")
    print(f"   URL: {paper.get('url', 'N/A')}")
    
    if paper.get('abstract'):
        abstract = paper['abstract']
        if len(abstract) > 200:
            abstract = abstract[:200] + "..."
        print(f"   Abstract: {abstract}")
    
    if paper.get('authors'):
        authors = [author.get('name', 'N/A') for author in paper['authors']]
        print(f"   Authors: {', '.join(authors[:3])}{'...' if len(authors) > 3 else ''}")


def test_picalm_alzheimers_search():
    """Test function to search for PICALM and Alzheimer's papers"""
    
    print("🧪 Semantic Scholar API Test - PICALM & Alzheimer's Search")
    print("=" * 60)
    
    # Initialize API client
    api = SemanticScholarAPI()
    
    # Test queries
    test_queries = [
        "PICALM Alzheimer's disease",
        "PICALM functional domains drug targets",
        "PICALM structure characterization",
        "PICALM small molecule modulators",
        "PICALM peptide modulators",
        "PICALM beta amyloid",
        "PICALM endocytosis Alzheimer's"
    ]
    
    all_results = []
    
    for i, query in enumerate(test_queries):
        print(f"\n{'='*50}")
        print(f"Test {i+1}/{len(test_queries)}: {query}")
        print(f"{'='*50}")
        
        # Search for papers
        results = api.search_papers(query, limit=5, offset=0)
        
        if "error" not in results:
            papers = results.get("data", [])
            print(f"\n📊 Results for '{query}':")
            
            for j, paper in enumerate(papers):
                print_paper_summary(paper, j)
                all_results.append({
                    "query": query,
                    "paper": paper
                })
        else:
            print(f"❌ Search failed: {results['error']}")
        
        print(f"\n⏳ Waiting 1 second before next query...")
        import time
        time.sleep(1)  # Be nice to the API
    
    # Summary
    print(f"\n{'='*60}")
    print("📈 SEARCH SUMMARY")
    print(f"{'='*60}")
    print(f"Total queries tested: {len(test_queries)}")
    print(f"Total papers found: {len(all_results)}")
    
    # Show unique papers
    unique_papers = {}
    for result in all_results:
        paper_id = result["paper"].get("paperId")
        if paper_id and paper_id not in unique_papers:
            unique_papers[paper_id] = result["paper"]
    
    print(f"Unique papers: {len(unique_papers)}")
    
    # Show top cited papers
    if unique_papers:
        print(f"\n🏆 TOP CITED PAPERS:")
        sorted_papers = sorted(unique_papers.values(), 
                             key=lambda x: x.get("citationCount", 0), 
                             reverse=True)
        
        for i, paper in enumerate(sorted_papers[:5]):
            print(f"{i+1}. {paper.get('title', 'N/A')}")
            print(f"   Citations: {paper.get('citationCount', 0)}")
            print(f"   Year: {paper.get('year', 'N/A')}")
            print(f"   URL: {paper.get('url', 'N/A')}")
            print()


def test_specific_paper_search():
    """Test searching for specific paper types"""
    
    print("\n🔬 TESTING SPECIFIC PAPER SEARCHES")
    print("=" * 50)
    
    api = SemanticScholarAPI()
    
    # More specific queries
    specific_queries = [
        "PICALM structural biology X-ray crystallography",
        "PICALM NMR spectroscopy structure",
        "PICALM drug discovery screening",
        "PICALM therapeutic target validation",
        "PICALM clinical trials Alzheimer's"
    ]
    
    for query in specific_queries:
        print(f"\n🔍 Testing: {query}")
        results = api.search_papers(query, limit=3)
        
        if "error" not in results:
            papers = results.get("data", [])
            print(f"Found {len(papers)} papers")
            
            for i, paper in enumerate(papers):
                print(f"  {i+1}. {paper.get('title', 'N/A')} ({paper.get('year', 'N/A')})")
        else:
            print(f"  ❌ Error: {results['error']}")
        
        import time
        time.sleep(1)


if __name__ == "__main__":
    print("🚀 Starting Semantic Scholar API Test")
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test basic search functionality
    test_picalm_alzheimers_search()
    
    # Test more specific searches
    test_specific_paper_search()
    
    print(f"\n✅ Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n💡 Tips for better results:")
    print("   - Use specific technical terms")
    print("   - Include methodology terms (X-ray, NMR, etc.)")
    print("   - Add publication year ranges")
    print("   - Use quotes for exact phrases")
    print("   - Consider using Semantic Scholar API key for higher rate limits") 