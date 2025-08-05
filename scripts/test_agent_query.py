#!/usr/bin/env python3
"""
Test script using agent_query approach from paper-qa tutorials
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv
load_dotenv()

async def test_agent_query():
    """Test using agent_query as shown in paper-qa tutorials."""
    try:
        from paperqa import Settings, agent_query
        from paperqa.agents.tools import DEFAULT_TOOL_NAMES
        
        print("Testing agent_query approach...")
        
        # Check if PDF exists
        pdf_file = Path("./papers/2507.21046v3.pdf")
        if not pdf_file.exists():
            print(f"❌ PDF file not found: {pdf_file}")
            return False
            
        print(f"✅ PDF file found: {pdf_file}")
        
        # Create settings with clinical trials tool enabled
        settings = Settings(
            paper_directory="./papers",
            llm="openrouter/google/gemini-2.5-flash-lite",
            embedding="ollama/nomic-embed-text",
            embedding_config={
                "api_base": "http://localhost:11434"
            },
            agent={
                "tool_names": DEFAULT_TOOL_NAMES + ["clinical_trials_search"],
                "agent_llm": "openrouter/google/gemini-2.5-flash-lite",
                "agent_llm_config": {
                    "api_key": "${OPENROUTER_API_KEY}",
                    "base_url": "https://openrouter.ai/api/v1"
                }
            }
        )
        
        print(f"Settings created: LLM={settings.llm}, Embedding={settings.embedding}")
        print(f"Tool names: {settings.agent.tool_names}")
        
        # Use agent_query as shown in tutorials
        print("Querying with agent_query...")
        answer_response = await agent_query(
            query="What is this paper about?",
            settings=settings
        )
        
        print(f"✅ Query completed!")
        print(f"Answer: {answer_response.session.answer}")
        
        if answer_response.session.contexts:
            print(f"Contexts used: {len(answer_response.session.contexts)}")
        
        return True
        
    except Exception as e:
        print(f"❌ agent_query test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_predefined_settings():
    """Test using predefined settings."""
    try:
        from paperqa import Settings, agent_query
        
        print("\nTesting predefined settings...")
        
        # Try the search_only_clinical_trials setting
        answer_response = await agent_query(
            query="What is this paper about?",
            settings=Settings.from_name("search_only_clinical_trials")
        )
        
        print(f"✅ Predefined settings test completed!")
        print(f"Answer: {answer_response.session.answer}")
        
        return True
        
    except Exception as e:
        print(f"❌ Predefined settings test failed: {e}")
        return False

if __name__ == "__main__":
    success1 = asyncio.run(test_agent_query())
    success2 = asyncio.run(test_predefined_settings())
    sys.exit(0 if (success1 or success2) else 1) 