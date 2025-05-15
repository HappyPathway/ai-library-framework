"""Tool selection logic for ailf.tooling."""
from typing import List, Optional, Dict, Any
from ailf.schemas.tooling import ToolDescription
import re  # For simple keyword matching as a start

class ToolSelector:
    """
    Selects the most appropriate tool based on a query and available tool descriptions.
    """

    def __init__(self, tools_data: Optional[List[ToolDescription]] = None, selection_strategy: str = "keyword_match"):
        """
        Initializes the ToolSelector.

        :param tools_data: List of tool descriptions to select from.
        :type tools_data: Optional[List[ToolDescription]]
        :param selection_strategy: The strategy to use for selecting tools.
                                   Currently supports: "keyword_match".
        :type selection_strategy: str
        """
        self.tools_data = tools_data or []
        self.selection_strategy = selection_strategy

    def select_tool(
        self, 
        query: str, 
        top_n: int = 1,
        score_threshold: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Selects the most appropriate tool(s) based on the query.

        :param query: The user query or task description.
        :type query: str
        :param top_n: Number of top matching tools to return (default: 1).
        :type top_n: int
        :param score_threshold: Minimum score threshold for tools to be included (0.0-1.0).
        :type score_threshold: float
        :return: List of dictionaries with tool information and matching score, sorted by score.
        :rtype: List[Dict[str, Any]]
        """
        if not self.tools_data:
            return []

        if self.selection_strategy == "keyword_match":
            return self._select_by_keyword_match(query, top_n, score_threshold)
        else:
            # Default to keyword match if strategy not recognized
            return self._select_by_keyword_match(query, top_n, score_threshold)

    def _select_by_keyword_match(
        self, 
        query: str, 
        top_n: int = 1,
        score_threshold: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Selects tools by matching keywords in the query against tool descriptions and keywords.

        :param query: The user query or task description.
        :type query: str
        :param top_n: Number of top matching tools to return.
        :type top_n: int
        :param score_threshold: Minimum score for tools to be included (0.0-1.0).
        :type score_threshold: float
        :return: List of dictionaries with tool information and matching score.
        :rtype: List[Dict[str, Any]]
        """
        query = query.lower()
        results = []

        for tool in self.tools_data:
            # Skip deprecated tools
            if getattr(tool, 'deprecated', False):
                continue

            # Calculate the match score
            score = self._calculate_keyword_match_score(query, tool)

            # Only include tools that meet the threshold
            if score >= score_threshold:
                results.append({
                    "tool": tool,
                    "score": score
                })

        # Sort by score (descending) and limit to top_n
        results = sorted(results, key=lambda x: x["score"], reverse=True)[:top_n]
        return results

    def _calculate_keyword_match_score(self, query: str, tool: ToolDescription) -> float:
        """
        Calculate a match score between the query and a tool description.

        :param query: The lowercase user query.
        :type query: str
        :param tool: The tool description.
        :type tool: ToolDescription
        :return: Match score between 0.0 and 1.0.
        :rtype: float
        """
        # Components to match against
        name = tool.name.lower()
        description = tool.description.lower()
        categories = [cat.lower() for cat in tool.categories]
        keywords = [kw.lower() for kw in tool.keywords]
        examples = [ex.lower() for ex in tool.usage_examples]

        # Count matches for name (highest importance)
        name_match = 1.0 if name in query or query in name else 0.0
        name_match_weight = 0.3  # 30% of total score

        # Description matches (medium importance)
        desc_matches = sum(1 for word in query.split() if word in description)
        desc_match = min(desc_matches / max(len(query.split()), 1), 1.0)
        desc_match_weight = 0.2  # 20% of total score

        # Category matches (medium importance)
        cat_matches = sum(1 for cat in categories if cat in query)
        cat_match = min(cat_matches / max(len(categories), 1), 1.0) if categories else 0.0
        cat_match_weight = 0.15  # 15% of total score

        # Keyword matches (high importance)
        keyword_matches = sum(1 for kw in keywords if kw in query)
        keyword_match = min(keyword_matches / max(len(keywords), 1), 1.0) if keywords else 0.0
        keyword_match_weight = 0.25  # 25% of total score

        # Example matches (low importance)
        example_matches = max((1 for ex in examples if query in ex), default=0) if examples else 0
        example_match = 1.0 if example_matches > 0 else 0.0
        example_match_weight = 0.1  # 10% of total score

        # Weighted average score
        final_score = (
            name_match * name_match_weight +
            desc_match * desc_match_weight +
            cat_match * cat_match_weight + 
            keyword_match * keyword_match_weight + 
            example_match * example_match_weight
        )

        return final_score
