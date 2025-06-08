"""
Search and RAG (Retrieval Augmented Generation) system for context enhancement.
Provides internet search capabilities and memory storage for analysis augmentation.
"""

import asyncio
import aiohttp
import requests
from typing import List, Dict, Any, Optional, Tuple
import json
import re
from datetime import datetime, timedelta
from urllib.parse import urlencode, urlparse
from bs4 import BeautifulSoup
import time
from dataclasses import dataclass, asdict
import hashlib
import os
import pickle

# Vector storage for RAG
try:
    import chromadb
    from sentence_transformers import SentenceTransformer
    VECTOR_STORAGE_AVAILABLE = True
except ImportError:
    VECTOR_STORAGE_AVAILABLE = False
    print("Warning: Vector storage libraries not available. RAG functionality will be limited.")

@dataclass
class SearchResult:
    """Structure for search results."""
    url: str
    title: str
    snippet: str
    content: str
    source: str
    timestamp: datetime
    relevance_score: float = 0.0

@dataclass
class ContextMemory:
    """Structure for stored context information."""
    id: str
    content: str
    source: str
    category: str  # e.g., 'market_data', 'competitive_intel', 'industry_trends'
    timestamp: datetime
    embedding: Optional[List[float]] = None

class SearchAndRAG:
    """Enhanced search and RAG system for strategic analysis."""
    
    def __init__(self, cache_dir: str = ".search_cache"):
        self.cache_dir = cache_dir
        self.memory_file = os.path.join(cache_dir, "context_memory.pkl")
        self.search_cache_file = os.path.join(cache_dir, "search_cache.pkl")
        
        # Create cache directory
        os.makedirs(cache_dir, exist_ok=True)
        
        # Initialize vector storage if available
        if VECTOR_STORAGE_AVAILABLE:
            self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
            self.chroma_client = chromadb.PersistentClient(path=os.path.join(cache_dir, "chroma_db"))
            self.collection = self.chroma_client.get_or_create_collection("strategy_context")
        else:
            self.embedder = None
            self.chroma_client = None
            self.collection = None
        
        # Load existing memory
        self.context_memory = self._load_memory()
        self.search_cache = self._load_search_cache()
    
    def _load_memory(self) -> List[ContextMemory]:
        """Load existing context memory from disk."""
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, 'rb') as f:
                    return pickle.load(f)
            except Exception as e:
                print(f"Error loading memory: {e}")
        return []
    
    def _save_memory(self):
        """Save context memory to disk."""
        try:
            with open(self.memory_file, 'wb') as f:
                pickle.dump(self.context_memory, f)
        except Exception as e:
            print(f"Error saving memory: {e}")
    
    def _load_search_cache(self) -> Dict[str, Any]:
        """Load search cache from disk."""
        if os.path.exists(self.search_cache_file):
            try:
                with open(self.search_cache_file, 'rb') as f:
                    return pickle.load(f)
            except Exception as e:
                print(f"Error loading search cache: {e}")
        return {}
    
    def _save_search_cache(self):
        """Save search cache to disk."""
        try:
            with open(self.search_cache_file, 'wb') as f:
                pickle.dump(self.search_cache, f)
        except Exception as e:
            print(f"Error saving search cache: {e}")
    
    def _generate_cache_key(self, query: str, search_type: str) -> str:
        """Generate cache key for search results."""
        content = f"{query}_{search_type}"
        return hashlib.md5(content.encode()).hexdigest()
    
    async def search_web(
        self, 
        query: str, 
        max_results: int = 5,
        use_cache: bool = True,
        cache_duration_hours: int = 24
    ) -> List[SearchResult]:
        """Search the web for relevant information."""
        
        cache_key = self._generate_cache_key(query, "web_search")
        
        # Check cache first
        if use_cache and cache_key in self.search_cache:
            cached_result = self.search_cache[cache_key]
            if datetime.now() - cached_result['timestamp'] < timedelta(hours=cache_duration_hours):
                return cached_result['results']
        
        try:
            # Use DuckDuckGo for search (no API key required)
            results = await self._duckduckgo_search(query, max_results)
            
            # Cache results
            if use_cache:
                self.search_cache[cache_key] = {
                    'results': results,
                    'timestamp': datetime.now()
                }
                self._save_search_cache()
            
            return results
            
        except Exception as e:
            print(f"Search error: {e}")
            return []
    
    async def _duckduckgo_search(self, query: str, max_results: int) -> List[SearchResult]:
        """Perform search using DuckDuckGo."""
        results = []
        
        try:
            # DuckDuckGo instant answer API
            params = {
                'q': query,
                'format': 'json',
                'no_html': '1',
                'skip_disambig': '1'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    'https://api.duckduckgo.com/',
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Extract results from DuckDuckGo response
                        if 'RelatedTopics' in data:
                            for i, topic in enumerate(data['RelatedTopics'][:max_results]):
                                if isinstance(topic, dict) and 'Text' in topic:
                                    result = SearchResult(
                                        url=topic.get('FirstURL', ''),
                                        title=f"Related Topic {i+1}",
                                        snippet=topic['Text'][:200] + "...",
                                        content=topic['Text'],
                                        source='DuckDuckGo',
                                        timestamp=datetime.now()
                                    )
                                    results.append(result)
                        
                        # Also check abstract
                        if 'Abstract' in data and data['Abstract']:
                            result = SearchResult(
                                url=data.get('AbstractURL', ''),
                                title='Abstract',
                                snippet=data['Abstract'][:200] + "...",
                                content=data['Abstract'],
                                source='DuckDuckGo',
                                timestamp=datetime.now()
                            )
                            results.append(result)
            
            return results
            
        except Exception as e:
            print(f"DuckDuckGo search error: {e}")
            return []
    
    async def search_company_info(self, company_name: str) -> List[SearchResult]:
        """Search for specific company information."""
        queries = [
            f"{company_name} company profile business model",
            f"{company_name} financial performance revenue",
            f"{company_name} strategy competitive position",
            f"{company_name} recent news developments"
        ]
        
        all_results = []
        for query in queries:
            results = await self.search_web(query, max_results=2)
            all_results.extend(results)
        
        return all_results
    
    async def search_market_data(self, industry: str, market: str = "") -> List[SearchResult]:
        """Search for market and industry data."""
        queries = [
            f"{industry} market size trends 2024",
            f"{industry} industry analysis competitive landscape",
            f"{market} {industry} growth projections",
            f"{industry} market challenges opportunities"
        ]
        
        all_results = []
        for query in queries:
            results = await self.search_web(query, max_results=2)
            all_results.extend(results)
        
        return all_results
    
    def store_context(
        self, 
        content: str, 
        source: str, 
        category: str,
        context_id: Optional[str] = None
    ) -> str:
        """Store context information in memory."""
        
        if not context_id:
            context_id = hashlib.md5(f"{content}_{source}_{datetime.now()}".encode()).hexdigest()
        
        # Generate embedding if available
        embedding = None
        if self.embedder:
            try:
                embedding = self.embedder.encode(content).tolist()
            except Exception as e:
                print(f"Error generating embedding: {e}")
        
        # Create context memory
        context = ContextMemory(
            id=context_id,
            content=content,
            source=source,
            category=category,
            timestamp=datetime.now(),
            embedding=embedding
        )
        
        # Store in memory
        self.context_memory.append(context)
        
        # Store in vector database if available
        if self.collection and embedding:
            try:
                self.collection.add(
                    embeddings=[embedding],
                    documents=[content],
                    metadatas=[{
                        'source': source,
                        'category': category,
                        'timestamp': context.timestamp.isoformat()
                    }],
                    ids=[context_id]
                )
            except Exception as e:
                print(f"Error storing in vector database: {e}")
        
        # Save to disk
        self._save_memory()
        
        return context_id
    
    def retrieve_relevant_context(
        self, 
        query: str, 
        top_k: int = 5,
        category_filter: Optional[str] = None
    ) -> List[ContextMemory]:
        """Retrieve relevant context for a query."""
        
        relevant_contexts = []
        
        if self.collection and self.embedder:
            try:
                # Generate query embedding
                query_embedding = self.embedder.encode(query).tolist()
                
                # Search in vector database
                where_filter = {"category": category_filter} if category_filter else None
                
                results = self.collection.query(
                    query_embeddings=[query_embedding],
                    n_results=top_k,
                    where=where_filter
                )
                
                # Convert results to ContextMemory objects
                for i, doc_id in enumerate(results['ids'][0]):
                    # Find the corresponding context in memory
                    for context in self.context_memory:
                        if context.id == doc_id:
                            relevant_contexts.append(context)
                            break
                            
            except Exception as e:
                print(f"Error retrieving from vector database: {e}")
        
        # Fallback to simple text matching if vector search fails
        if not relevant_contexts:
            query_lower = query.lower()
            for context in self.context_memory:
                if category_filter and context.category != category_filter:
                    continue
                
                if query_lower in context.content.lower():
                    relevant_contexts.append(context)
                    
                if len(relevant_contexts) >= top_k:
                    break
        
        return relevant_contexts
    
    async def enhance_analysis_with_context(
        self, 
        strategy_text: str, 
        perspective: str
    ) -> Tuple[str, List[SearchResult]]:
        """Enhance analysis with relevant context from search and memory."""
        
        # Determine what additional context might be useful
        context_needs = await self._analyze_context_needs(strategy_text, perspective)
        
        search_results = []
        context_summary = ""
        
        if context_needs:
            # Perform searches based on identified needs
            for need in context_needs:
                results = await self.search_web(need['query'], max_results=3)
                search_results.extend(results)
                
                # Store valuable results in memory
                for result in results:
                    if len(result.content) > 100:  # Only store substantial content
                        self.store_context(
                            content=result.content,
                            source=result.url or result.source,
                            category=need['category']
                        )
            
            # Retrieve relevant stored context
            stored_context = self.retrieve_relevant_context(strategy_text, top_k=3)
            
            # Compile context summary
            if search_results or stored_context:
                context_summary = self._compile_context_summary(search_results, stored_context)
        
        return context_summary, search_results
    
    async def _analyze_context_needs(
        self, 
        strategy_text: str, 
        perspective: str
    ) -> List[Dict[str, str]]:
        """Analyze what additional context might be useful for the analysis."""
        
        needs = []
        text_lower = strategy_text.lower()
        
        # Extract potential company names, industries, markets
        companies = self._extract_entities(strategy_text, 'companies')
        industries = self._extract_entities(strategy_text, 'industries')
        
        # Determine search needs based on perspective
        if perspective == 'market_forces':
            for industry in industries:
                needs.append({
                    'query': f"{industry} market trends competitive analysis 2024",
                    'category': 'market_data'
                })
        
        elif perspective == 'historical_analyst':
            for company in companies:
                needs.append({
                    'query': f"{company} business strategy case study lessons",
                    'category': 'historical_cases'
                })
        
        elif perspective == 'stakeholder_advocate':
            needs.append({
                'query': f"stakeholder management best practices {' '.join(industries)}",
                'category': 'stakeholder_intel'
            })
        
        elif perspective == 'risk_assessment':
            for industry in industries:
                needs.append({
                    'query': f"{industry} business risks regulatory challenges",
                    'category': 'risk_data'
                })
        
        # General strategic context
        if any(word in text_lower for word in ['launch', 'expand', 'enter']):
            needs.append({
                'query': f"market entry strategy best practices {' '.join(industries)}",
                'category': 'strategic_guidance'
            })
        
        return needs[:3]  # Limit to avoid too many searches
    
    def _extract_entities(self, text: str, entity_type: str) -> List[str]:
        """Extract entities (companies, industries) from text."""
        entities = []
        
        # Simple pattern matching for now
        # In production, you might use NER models
        
        if entity_type == 'companies':
            # Look for capitalized words that might be company names
            company_patterns = [
                r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s+(?:Inc|Corp|Ltd|LLC|Company|Co)\.?)\b',
                r'\b(?:Apple|Google|Microsoft|Amazon|Meta|Tesla|Netflix|Uber|Airbnb)\b'
            ]
            for pattern in company_patterns:
                matches = re.findall(pattern, text)
                entities.extend(matches)
        
        elif entity_type == 'industries':
            # Look for industry keywords
            industry_keywords = [
                'technology', 'healthcare', 'finance', 'retail', 'manufacturing',
                'automotive', 'energy', 'telecommunications', 'aerospace', 'biotechnology',
                'software', 'hardware', 'e-commerce', 'fintech', 'edtech'
            ]
            text_lower = text.lower()
            for keyword in industry_keywords:
                if keyword in text_lower:
                    entities.append(keyword)
        
        return list(set(entities))  # Remove duplicates
    
    def _compile_context_summary(
        self, 
        search_results: List[SearchResult], 
        stored_context: List[ContextMemory]
    ) -> str:
        """Compile a summary of relevant context for analysis enhancement."""
        
        summary_parts = []
        
        if search_results:
            summary_parts.append("RECENT MARKET INTELLIGENCE:")
            for result in search_results[:3]:  # Top 3 results
                summary_parts.append(f"• {result.title}: {result.snippet}")
        
        if stored_context:
            summary_parts.append("\nRELEVANT HISTORICAL CONTEXT:")
            for context in stored_context[:3]:  # Top 3 contexts
                summary_parts.append(f"• {context.category}: {context.content[:150]}...")
        
        return "\n".join(summary_parts) if summary_parts else ""
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get statistics about stored memory."""
        if not self.context_memory:
            return {"total_items": 0, "categories": {}}
        
        stats = {
            "total_items": len(self.context_memory),
            "categories": {},
            "oldest_item": min(c.timestamp for c in self.context_memory),
            "newest_item": max(c.timestamp for c in self.context_memory)
        }
        
        # Count by category
        for context in self.context_memory:
            category = context.category
            if category not in stats["categories"]:
                stats["categories"][category] = 0
            stats["categories"][category] += 1
        
        return stats
    
    def clear_old_memory(self, days_old: int = 30):
        """Clear memory items older than specified days."""
        cutoff_date = datetime.now() - timedelta(days=days_old)
        
        # Filter out old items
        self.context_memory = [
            context for context in self.context_memory 
            if context.timestamp > cutoff_date
        ]
        
        # Save updated memory
        self._save_memory()
        
        # Clean vector database if available
        if self.collection:
            try:
                # This is a simplified cleanup - ChromaDB might have better methods
                all_items = self.collection.get()
                old_ids = []
                
                for i, metadata in enumerate(all_items['metadatas']):
                    timestamp = datetime.fromisoformat(metadata['timestamp'])
                    if timestamp <= cutoff_date:
                        old_ids.append(all_items['ids'][i])
                
                if old_ids:
                    self.collection.delete(ids=old_ids)
                    
            except Exception as e:
                print(f"Error cleaning vector database: {e}")