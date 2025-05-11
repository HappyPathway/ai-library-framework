"""Enhanced tool selection logic for ailf.tooling, including RAG-based selection."""
from typing import List, Optional, Dict, Any, Tuple, Union
import re  # For simple keyword matching
import numpy as np
from ailf.schemas.tooling import ToolDescription

class ToolSelector:
    """
    Selects the most appropriate tool based on a query and available tool descriptions.
    
    This enhanced version supports both keyword-based and RAG-based (embedding similarity)
    tool selection strategies.
    """

    def __init__(self, 
                 selection_strategy: str = "keyword_match", 
                 embedding_model: Optional[Any] = None):
        """
        Initialize the ToolSelector.

        :param selection_strategy: Strategy for selecting tools: "keyword_match", "rag", or "hybrid"
        :type selection_strategy: str
        :param embedding_model: Optional model for creating embeddings for RAG selection
        :type embedding_model: Optional[Any]
        """
        self.selection_strategy = selection_strategy
        self.embedding_model = embedding_model
        
        if selection_strategy in ["rag", "hybrid"] and embedding_model is None:
            import logging
            logging.warning(
                f"Strategy '{selection_strategy}' selected but no embedding_model provided. "
                f"Falling back to keyword_match."
            )
            self.selection_strategy = "keyword_match"

    def select_tool(
        self,
        query: str,
        available_tools: List[ToolDescription],
        threshold: float = 0.1,  # General threshold for selection confidence
        top_k: int = 1  # Number of top tools to return
    ) -> List[Tuple[ToolDescription, float]]:
        """
        Selects tool(s) from the available list based on the query.

        :param query: User query or task description
        :type query: str
        :param available_tools: List of ToolDescription objects
        :type available_tools: List[ToolDescription]
        :param threshold: Minimum score for a tool to be selected
        :type threshold: float
        :param top_k: Number of top tools to return (default: 1)
        :type top_k: int
        :return: List of (tool, score) tuples, sorted by score (descending)
        :rtype: List[Tuple[ToolDescription, float]]
        """
        if not available_tools:
            return []

        if self.selection_strategy == "keyword_match":
            return self._select_by_keyword_match(query, available_tools, threshold, top_k)
        elif self.selection_strategy == "rag":
            return self._select_by_rag(query, available_tools, threshold, top_k)
        elif self.selection_strategy == "hybrid":
            # Combine both strategies with a weighted average
            keyword_results = self._select_by_keyword_match(query, available_tools, 0, len(available_tools))
            rag_results = self._select_by_rag(query, available_tools, 0, len(available_tools))
            
            # Create dictionaries for easy lookup
            keyword_dict = {tool: score for tool, score in keyword_results}
            rag_dict = {tool: score for tool, score in rag_results}
            
            # Combine scores (with weights favoring RAG)
            combined_scores = []
            for tool in available_tools:
                keyword_score = keyword_dict.get(tool, 0)
                rag_score = rag_dict.get(tool, 0)
                # Weight RAG higher (70%) than keyword matching (30%)
                combined_score = 0.3 * keyword_score + 0.7 * rag_score
                combined_scores.append((tool, combined_score))
            
            # Sort and filter by threshold
            combined_scores.sort(key=lambda x: x[1], reverse=True)
            result = [(tool, score) for tool, score in combined_scores if score >= threshold]
            return result[:top_k]
        else:
            return []

    def _select_by_keyword_match(
        self,
        query: str,
        available_tools: List[ToolDescription],
        threshold: float = 0.1,
        top_k: int = 1
    ) -> List[Tuple[ToolDescription, float]]:
        """
        Select tools by matching keywords from the query against tool metadata.
        
        :param query: The query to match against
        :param available_tools: Available tool descriptions
        :param threshold: Minimum score threshold
        :param top_k: Maximum number of tools to return
        :return: List of (tool, score) tuples
        """
        scores = []
        query_tokens = set(re.findall(r'\w+', query.lower()))

        if not query_tokens:
            return []

        max_possible_score = 0  # For normalization
        for token in query_tokens:
            max_possible_score += 3  # Name weight
            max_possible_score += 1  # Description weight
            max_possible_score += 2  # Keywords weight
            max_possible_score += 0.5  # Examples weight
        
        if max_possible_score == 0:
            max_possible_score = 1  # Avoid division by zero

        for tool in available_tools:
            current_score = 0

            # Match against tool name
            tool_name_tokens = set(re.findall(r'\w+', tool.name.lower()))
            current_score += len(query_tokens.intersection(tool_name_tokens)) * 3

            # Match against tool description
            tool_desc_tokens = set(re.findall(r'\w+', tool.description.lower()))
            current_score += len(query_tokens.intersection(tool_desc_tokens))

            # Match against tool keywords
            tool_keywords_tokens = set()
            for kw in tool.keywords:
                tool_keywords_tokens.update(re.findall(r'\w+', kw.lower()))
            current_score += len(query_tokens.intersection(tool_keywords_tokens)) * 2

            # Match against usage examples
            for example in tool.usage_examples:
                example_tokens = set(re.findall(r'\w+', example.lower()))
                current_score += len(query_tokens.intersection(example_tokens)) * 0.5
            
            # Normalize score to 0-1 range
            normalized_score = current_score / max_possible_score
            scores.append((tool, normalized_score))

        # Sort by score in descending order
        scores.sort(key=lambda x: x[1], reverse=True)
        
        # Filter by threshold and limit to top_k
        result = [(tool, score) for tool, score in scores if score >= threshold]
        return result[:top_k]

    def _select_by_rag(
        self,
        query: str,
        available_tools: List[ToolDescription],
        threshold: float = 0.1,
        top_k: int = 1
    ) -> List[Tuple[ToolDescription, float]]:
        """
        Select tools using RAG (embedding similarity).
        
        :param query: The query to match against
        :param available_tools: Available tool descriptions
        :param threshold: Minimum similarity threshold
        :param top_k: Maximum number of tools to return
        :return: List of (tool, similarity_score) tuples
        :raises NotImplementedError: If embedding_model is None
        """
        if self.embedding_model is None:
            raise NotImplementedError("RAG selection requires an embedding model")
        
        # Create query embedding
        query_embedding = self._get_embedding(query)
        if query_embedding is None:
            return []
        
        scores = []
        for tool in available_tools:
            # First check if the tool already has a combined embedding
            if tool.combined_embedding:
                tool_embedding = tool.combined_embedding
            # If not, try creating a combined embedding from name, description, keywords
            else:
                tool_text = f"{tool.name} {tool.description} {' '.join(tool.keywords)}"
                tool_embedding = self._get_embedding(tool_text)
            
            if tool_embedding:
                similarity = self._calculate_similarity(query_embedding, tool_embedding)
                scores.append((tool, similarity))
            else:
                scores.append((tool, 0.0))  # No embedding available
        
        # Sort by similarity in descending order
        scores.sort(key=lambda x: x[1], reverse=True)
        
        # Filter by threshold and limit to top_k
        result = [(tool, score) for tool, score in scores if score >= threshold]
        return result[:top_k]

    def _get_embedding(self, text: str) -> Optional[List[float]]:
        """
        Get embedding for a text using the embedding model.
        
        :param text: Text to embed
        :return: Embedding vector or None if embedding fails
        """
        if self.embedding_model is None:
            return None
        
        try:
            # This implementation will depend on your specific embedding model
            # Common implementations might be:
            # 1. For OpenAI embeddings:
            #    return self.embedding_model.embed_query(text)
            # 2. For HuggingFace models:
            #    return self.embedding_model.encode(text).tolist()
            # 3. For SentenceTransformers:
            #    return self.embedding_model.encode(text, convert_to_tensor=False).tolist()
            
            # Placeholder implementation:
            return self.embedding_model.get_embedding(text)
        except Exception as e:
            import logging
            logging.error(f"Error creating embedding: {e}")
            return None

    def _calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Calculate cosine similarity between two embedding vectors.
        
        :param embedding1: First embedding vector
        :param embedding2: Second embedding vector
        :return: Similarity score (0-1)
        """
        try:
            # Convert to numpy arrays for efficient calculation
            a = np.array(embedding1)
            b = np.array(embedding2)
            
            # Calculate cosine similarity
            cos_sim = np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
            return float(cos_sim)
        except Exception as e:
            import logging
            logging.error(f"Error calculating similarity: {e}")
            return 0.0
    
    @staticmethod
    def create_with_registry_client(
        registry_client: Any,
        selection_strategy: str = "keyword_match",
        embedding_model: Optional[Any] = None
    ) -> "ToolSelector":
        """
        Create a ToolSelector with integration to a registry client.
        
        :param registry_client: Client for accessing the tool registry
        :param selection_strategy: Selection strategy 
        :param embedding_model: Optional model for creating embeddings
        :return: Configured ToolSelector instance
        """
        selector = ToolSelector(selection_strategy, embedding_model)
        selector.registry_client = registry_client
        return selector
    
    async def select_from_registry(
        self,
        query: str,
        query_registry: bool = True,
        local_tools: Optional[List[ToolDescription]] = None,
        registry_query_params: Optional[Dict[str, Any]] = None,
        threshold: float = 0.1,
        top_k: int = 1
    ) -> List[Tuple[ToolDescription, float]]:
        """
        Select tools by combining local tools and tools from the registry.
        
        :param query: User query or task description
        :param query_registry: Whether to query the registry for additional tools
        :param local_tools: List of local tool descriptions
        :param registry_query_params: Additional parameters for registry queries
        :param threshold: Minimum score threshold
        :param top_k: Maximum number of tools to return
        :return: List of (tool, score) tuples
        :raises AttributeError: If registry_client is not set
        """
        if not hasattr(self, 'registry_client'):
            raise AttributeError("registry_client not set. Use create_with_registry_client to create this instance.")
        
        # Start with local tools if provided
        available_tools = local_tools or []
        
        # Add tools from registry if requested
        if query_registry:
            try:
                params = registry_query_params or {}
                registry_tools = await self.registry_client.discover_tools(query=query, **params)
                available_tools.extend(registry_tools)
            except Exception as e:
                import logging
                logging.error(f"Error querying registry for tools: {e}")
        
        # Process combined tool list
        return self.select_tool(query, available_tools, threshold, top_k)
