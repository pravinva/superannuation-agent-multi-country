#!/usr/bin/env python3
"""
Intelligent Query Classifier - Embedding-Based Cascade
Replaces hardcoded keywords + ai_classify with semantic understanding
"""

import time
import re
import json
from typing import Dict, List, Optional
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementState
from databricks.sdk.service.serving import ChatMessage, ChatMessageRole

from config import SQL_WAREHOUSE_ID
from utils.lakehouse import get_workspace_client  # Use same workspace client as member cards


class EmbeddingCascadeClassifier:
    """
    3-stage cascade classifier for optimal accuracy/cost/latency:
    
    Stage 1: Regex patterns (80% of queries, <1ms, $0)
    Stage 2: Embedding similarity (15% of queries, ~100ms, ~$0.0001)
    Stage 3: LLM fallback (5% of queries, ~300ms, ~$0.001)
    """
    
    def __init__(self, 
                 prompts_registry=None,
                 enable_cache: bool = True,
                 embedding_model: str = "databricks-bge-large-en",
                 llm_endpoint: str = "databricks-claude-haiku-4"):
        """
        Initialize the cascade classifier.
        
        Args:
            prompts_registry: PromptsRegistry instance for archetype queries
            enable_cache: Enable query result caching
            embedding_model: Databricks embedding model to use
            llm_endpoint: LLM endpoint for fallback classification
        """
        # ✅ Use same workspace client and warehouse resolution as lakehouse.py
        from utils.lakehouse import get_workspace_client
        self.w = get_workspace_client()
        self.prompts_registry = prompts_registry
        self.enable_cache = enable_cache
        self.embedding_model = embedding_model
        self.llm_endpoint = llm_endpoint
        
        # Query cache
        self.cache = {} if enable_cache else None
        
        # Archetype embeddings (computed on first use)
        self._retirement_embeddings = None
        self._off_topic_embeddings = None
        
        # Classification thresholds (tunable)
        self.HIGH_CONFIDENCE_THRESHOLD = 0.75
        self.LOW_CONFIDENCE_THRESHOLD = 0.40
        
        # Metrics
        self.metrics = {
            'total_queries': 0,
            'stage1_hits': 0,  # Regex fast path
            'stage2_hits': 0,  # Embedding
            'stage3_hits': 0,  # LLM fallback
            'cache_hits': 0,
            'total_cost': 0.0,
            'total_latency_ms': 0.0
        }
        
        print("✅ EmbeddingCascadeClassifier initialized")
        print(f"   Embedding Model: {self.embedding_model}")
        print(f"   LLM Fallback: {self.llm_endpoint}")
        print(f"   Cache Enabled: {self.enable_cache}")
    
    def classify(self, user_query: str) -> Dict:
        """
        Main classification method with 3-stage cascade.
        
        Args:
            user_query: User's query to classify
            
        Returns:
            Classification result dictionary with:
            - is_on_topic: bool
            - confidence: float (0-1)
            - classification: str
            - method: str (which stage was used)
            - latency_ms: float
            - cost_usd: float
        """
        start_time = time.time()
        self.metrics['total_queries'] += 1
        
        # Check cache first
        if self.enable_cache and user_query in self.cache:
            self.metrics['cache_hits'] += 1
            result = self.cache[user_query].copy()
            result['cached'] = True
            result['latency_ms'] = 0.0
            return result
        
        # STAGE 1: Regex pattern matching (fast path)
        stage1_result = self._stage1_regex_classification(user_query)
        if stage1_result is not None:
            self.metrics['stage1_hits'] += 1
            latency_ms = (time.time() - start_time) * 1000
            result = {
                **stage1_result,
                'latency_ms': latency_ms,
                'cost_usd': 0.0,
                'cached': False
            }
            self._cache_result(user_query, result)
            self._update_metrics(result)
            return result
        
        # STAGE 2: Embedding similarity
        try:
            stage2_result = self._stage2_embedding_classification(user_query)
            if stage2_result is not None:
                self.metrics['stage2_hits'] += 1
                latency_ms = (time.time() - start_time) * 1000
                result = {
                    **stage2_result,
                    'latency_ms': latency_ms,
                    'cost_usd': 0.0001,
                    'cached': False
                }
                self._cache_result(user_query, result)
                self._update_metrics(result)
                return result
        except Exception as e:
            # ✅ Embedding failed - log warning but continue to Stage 3
            print(f"⚠️ Stage 2 embedding error: {e}")
            # Continue to Stage 3 LLM fallback
        
        # STAGE 3: LLM fallback (borderline cases OR if Stage 2 failed)
        stage3_result = self._stage3_llm_classification(user_query)
        self.metrics['stage3_hits'] += 1
        latency_ms = (time.time() - start_time) * 1000
        result = {
            **stage3_result,
            'latency_ms': latency_ms,
            'cost_usd': 0.001,
            'cached': False
        }
        self._cache_result(user_query, result)
        self._update_metrics(result)
        return result
    
    def _stage1_regex_classification(self, query: str) -> Optional[Dict]:
        """
        Stage 1: Fast regex pattern matching.
        
        Returns None if no definitive match found.
        """
        query_lower = query.lower()
        
        # High-precision retirement patterns
        # ✅ FIXED: Patterns now match word order flexibly
        retirement_patterns = [
            r'\b401[k(]',  # 401k, 401(k)
            # Match "superannuation" with retirement keywords anywhere in query
            r'\b(super|superannuation)\b.*\b(balance|withdraw|withdrawal|tax|contribution|amount|maximum|minimum|limit)\b',
            r'\b(balance|withdraw|withdrawal|tax|contribution|amount|maximum|minimum|limit)\b.*\b(super|superannuation)\b',
            # Match "pension" or "retirement" with keywords
            r'\b(pension|retirement)\s+(benefit|withdrawal|access|planning|income)',
            r'\b(benefit|withdrawal|access|planning|income)\s+(pension|retirement)',
            # Account types
            r'\b(epf|ppf|nps|eps|vpf)\b',  # India schemes
            r'\b(ira|roth|sep|simple)\b',  # US accounts
            r'\b(sipp|lgps|lisa)\b',  # UK schemes
            # Specific retirement concepts
            r'\bpreservation\s+age\b',
            r'\bearly\s+(access|withdrawal|retirement)',
            r'\bretirement\s+(corpus|savings|account)',
            # Benefits
            r'\b(centrelink|age\s+pension)\b',  # Australia benefits
            r'\bsocial\s+security\b',  # US benefits
            r'\bstate\s+pension\b',  # UK benefits
        ]
        
        # Clear off-topic patterns
        off_topic_patterns = [
            r'\b(weather|temperature|forecast)\b',
            r'\b(recipe|cook|food|meal)\b',
            r'\b(joke|funny|laugh)\b',
            r'\b(sport|game|match|score)\b',
            r'\b(movie|film|tv\s+show)\b',
            r'\b(login|password|forgot\s+password|reset\s+password)\b',
            r'\b(car|vehicle|drive|traffic)\b',
            r'\b(travel|flight|hotel|vacation)\b',
            r'\b(book|read|novel|library)\b',
            r'\bcapital\s+of\b',  # Geography questions
            r'\bhow\s+to\s+(fix|repair)\b',  # Technical help
        ]
        
        # Check retirement patterns
        for pattern in retirement_patterns:
            if re.search(pattern, query_lower):
                return {
                    'is_on_topic': True,
                    'confidence': 0.95,
                    'classification': 'retirement_query',
                    'method': 'regex_fast_path',
                    'matched_pattern': pattern
                }
        
        # Check off-topic patterns
        for pattern in off_topic_patterns:
            if re.search(pattern, query_lower):
                return {
                    'is_on_topic': False,
                    'confidence': 0.95,
                    'classification': 'off_topic',
                    'method': 'regex_fast_path',
                    'matched_pattern': pattern
                }
        
        return None  # No definitive match, move to stage 2
    
    def _stage2_embedding_classification(self, query: str) -> Optional[Dict]:
        """
        Stage 2: Semantic similarity using embeddings.
        
        Returns None if confidence is too low (borderline case).
        """
        try:
            # Get query embedding
            query_embedding = self._get_embedding(query)
            
            # Ensure archetypes are loaded
            if self._retirement_embeddings is None:
                self._load_archetype_embeddings()
            
            # Calculate similarity to retirement archetypes
            retirement_scores = [
                self._cosine_similarity(query_embedding, arch_emb)
                for arch_emb in self._retirement_embeddings
            ]
            max_retirement_score = max(retirement_scores) if retirement_scores else 0.0
            
            # Calculate similarity to off-topic archetypes
            off_topic_scores = [
                self._cosine_similarity(query_embedding, arch_emb)
                for arch_emb in self._off_topic_embeddings
            ]
            max_off_topic_score = max(off_topic_scores) if off_topic_scores else 0.0
            
            # High confidence retirement query
            if max_retirement_score > self.HIGH_CONFIDENCE_THRESHOLD:
                return {
                    'is_on_topic': True,
                    'confidence': max_retirement_score,
                    'classification': 'retirement_query',
                    'method': 'embedding_similarity',
                    'similarity_score': max_retirement_score
                }
            
            # Clear off-topic query
            if max_off_topic_score > max_retirement_score and max_retirement_score < self.LOW_CONFIDENCE_THRESHOLD:
                return {
                    'is_on_topic': False,
                    'confidence': max_off_topic_score,
                    'classification': 'off_topic',
                    'method': 'embedding_similarity',
                    'similarity_score': max_retirement_score
                }
            
            # Borderline case - needs LLM
            return None
            
        except Exception as e:
            print(f"⚠️ Stage 2 embedding error: {e}")
            return None  # Fall back to stage 3
    
    def _stage3_llm_classification(self, query: str) -> Dict:
        """
        Stage 3: LLM-based classification for borderline cases.
        """
        try:
            classification_prompt = f"""You are a retirement advisory classifier.

Determine if this query is about retirement/pensions/superannuation OR off-topic.

USER QUERY: "{query}"

RETIREMENT TOPICS:
- Retirement accounts: 401k, IRA, Superannuation, EPF, NPS, SIPP, pension
- Withdrawals, early access, hardship
- Tax on retirement withdrawals
- Benefits, projections, contributions
- Retirement planning advice

OFF-TOPIC EXAMPLES:
- General finance (loans, mortgages, credit cards, savings accounts)
- Investments (stocks, crypto, real estate - unless retirement-specific)
- General questions (weather, cooking, sports, entertainment)
- Technical support (login, password reset)

IMPORTANT: "Retirement party" or "retirement gift" = OFF-TOPIC (social events, not financial)

Respond in JSON:
{{
    "classification": "retirement_query" or "off_topic",
    "confidence": 0.0 to 1.0,
    "reasoning": "one sentence"
}}"""

            response = self.w.serving_endpoints.query(
                name=self.llm_endpoint,
                messages=[
                    ChatMessage(role=ChatMessageRole.USER, content=classification_prompt)
                ],
                max_tokens=150,
                temperature=0.0
            )
            
            response_content = response.choices[0].message.content
            
            # ✅ FIX: Handle GPT OSS structured response format
            # GPT OSS returns a list with chunks like:
            # [{'type': 'reasoning', ...}, {'type': 'text', 'text': '{...JSON...}'}]
            if isinstance(response_content, list):
                # Extract only 'text' type chunks and join them
                text_chunks = []
                for chunk in response_content:
                    if isinstance(chunk, dict):
                        if chunk.get('type') == 'text' and 'text' in chunk:
                            text_chunks.append(chunk['text'])
                        elif 'text' in chunk:  # Fallback: any dict with 'text' key
                            text_chunks.append(chunk['text'])
                    else:
                        # Fallback: just convert to string
                        text_chunks.append(str(chunk))
                response_text = ' '.join(text_chunks)
            elif isinstance(response_content, str):
                response_text = response_content
            else:
                response_text = str(response_content)
            
            # Extract JSON from response (handle markdown code blocks)
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(0))
            else:
                result = json.loads(response_text)
            
            return {
                'is_on_topic': result['classification'] == 'retirement_query',
                'confidence': result['confidence'],
                'classification': result['classification'],
                'method': 'llm_fallback',
                'reasoning': result.get('reasoning', '')
            }
            
        except Exception as e:
            print(f"❌ Stage 3 LLM error: {e}")
            # Default to on-topic to avoid false rejections
            return {
                'is_on_topic': True,
                'confidence': 0.5,
                'classification': 'unknown',
                'method': 'llm_fallback_error',
                'error': str(e)
            }
    
    def _get_embedding(self, text: str) -> List[float]:
        """
        Get embedding vector using Databricks AI functions.
        ✅ Uses same warehouse ID resolution as lakehouse.py for consistency.
        """
        # Escape single quotes for SQL
        escaped_text = text.replace("'", "''")
        
        query = f"""
        SELECT ai_generate_embedding(
            '{escaped_text}',
            '{self.embedding_model}'
        ) as embedding
        """
        
        # ✅ Use lakehouse.execute_sql_query for consistent warehouse ID handling
        # This uses the same warehouse ID resolution as member cards
        from utils.lakehouse import execute_sql_query
        
        try:
            df = execute_sql_query(query)
            
            if df.empty or 'embedding' not in df.columns:
                raise RuntimeError("Embedding generation failed - empty result")
            
            embedding_data = df.iloc[0]['embedding']
            
            # Handle different response formats
            if isinstance(embedding_data, str):
                return json.loads(embedding_data)
            elif isinstance(embedding_data, list):
                return embedding_data
            else:
                raise ValueError(f"Unexpected embedding format: {type(embedding_data)}")
                
        except ValueError as ve:
            # Warehouse ID not configured
            raise RuntimeError(f"Embedding generation failed: {str(ve)}")
        except Exception as e:
            # Get more details about the SQL error
            error_msg = str(e)
            if "StatementState.FAILED" in error_msg or "FAILED" in error_msg:
                # Check if it's a function availability issue
                if "ai_generate_embedding" in error_msg.lower() or "function" in error_msg.lower():
                    raise RuntimeError(
                        f"Embedding generation failed: The SQL warehouse may not support AI functions. "
                        f"Error: {error_msg}. "
                        f"Please ensure your warehouse supports ai_generate_embedding() and the model '{self.embedding_model}' is available."
                    )
                else:
                    raise RuntimeError(
                        f"Embedding generation failed: SQL execution error: {error_msg}. "
                        f"Warehouse may be unavailable or there's a connectivity issue."
                    )
            else:
                raise RuntimeError(f"Embedding generation failed: {error_msg}")
    
    def _load_archetype_embeddings(self):
        """
        Load or compute embeddings for archetype queries.
        """
        print("🔄 Loading archetype embeddings...")
        
        # Get archetype queries from prompts registry
        if self.prompts_registry:
            retirement_archetypes = self.prompts_registry.get_retirement_archetypes()
            off_topic_archetypes = self.prompts_registry.get_off_topic_archetypes()
        else:
            # Fallback archetypes
            retirement_archetypes = [
                "Can I withdraw money from my superannuation?",
                "How much tax will I pay on my 401k withdrawal?",
                "What is my pension benefit amount?",
                "How will my retirement savings grow over time?",
                "Am I eligible for early access to my retirement account?",
                "What are the EPF contribution rules?",
            ]
            off_topic_archetypes = [
                "What's the weather like today?",
                "How do I cook pasta?",
                "Tell me a joke",
                "What is the capital of France?",
                "Help me reset my password",
            ]
        
        # Compute embeddings
        self._retirement_embeddings = [
            self._get_embedding(arch) for arch in retirement_archetypes
        ]
        
        self._off_topic_embeddings = [
            self._get_embedding(arch) for arch in off_topic_archetypes
        ]
        
        print(f"✅ Loaded {len(self._retirement_embeddings)} retirement + {len(self._off_topic_embeddings)} off-topic archetypes")
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        Calculate cosine similarity between two vectors.
        """
        import math
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(b * b for b in vec2))
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)
    
    def _cache_result(self, query: str, result: Dict):
        """Cache classification result."""
        if self.enable_cache and len(self.cache) < 1000:  # Limit cache size
            self.cache[query] = result
    
    def _update_metrics(self, result: Dict):
        """Update classification metrics."""
        self.metrics['total_cost'] += result.get('cost_usd', 0.0)
        self.metrics['total_latency_ms'] += result.get('latency_ms', 0.0)
    
    def get_metrics(self) -> Dict:
        """Get classification metrics and statistics."""
        total = self.metrics['total_queries']
        
        if total == 0:
            return self.metrics
        
        return {
            **self.metrics,
            'stage1_percentage': (self.metrics['stage1_hits'] / total) * 100,
            'stage2_percentage': (self.metrics['stage2_hits'] / total) * 100,
            'stage3_percentage': (self.metrics['stage3_hits'] / total) * 100,
            'cache_hit_rate': (self.metrics['cache_hits'] / total) * 100,
            'avg_cost_usd': self.metrics['total_cost'] / total,
            'avg_latency_ms': self.metrics['total_latency_ms'] / total,
        }
    
    def print_metrics(self):
        """Print classification metrics in a readable format."""
        metrics = self.get_metrics()
        
        print("\n" + "=" * 70)
        print("📊 CLASSIFIER METRICS")
        print("=" * 70)
        print(f"Total Queries: {metrics['total_queries']}")
        print(f"Cache Hits: {metrics['cache_hits']} ({metrics.get('cache_hit_rate', 0):.1f}%)")
        print(f"\nStage Distribution:")
        print(f"  Stage 1 (Regex):     {metrics['stage1_hits']} ({metrics.get('stage1_percentage', 0):.1f}%)")
        print(f"  Stage 2 (Embedding): {metrics['stage2_hits']} ({metrics.get('stage2_percentage', 0):.1f}%)")
        print(f"  Stage 3 (LLM):       {metrics['stage3_hits']} ({metrics.get('stage3_percentage', 0):.1f}%)")
        print(f"\nPerformance:")
        print(f"  Avg Latency: {metrics.get('avg_latency_ms', 0):.1f}ms")
        print(f"  Avg Cost:    ${metrics.get('avg_cost_usd', 0):.6f}")
        print(f"  Total Cost:  ${metrics['total_cost']:.6f}")
        print("=" * 70 + "\n")


def printf(msg):
    """Print helper."""
    print(msg)

