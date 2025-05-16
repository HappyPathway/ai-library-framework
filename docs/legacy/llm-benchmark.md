# Plan: LLM Model Selection Tool via Benchmark Leaderboards

This document outlines the plan to implement a tool that allows an AI agent to leverage LLM benchmark leaderboard statistics to inform its decision-making process when selecting a model for a specific task.

## 1. Goals

*   Enable agents to dynamically choose or recommend LLMs based on their performance on relevant benchmarks.
*   Provide a structured way to fetch, parse, and interpret leaderboard data.
*   Allow agents to consider task-specific requirements when evaluating models.
*   Create a reusable and extensible tool for model selection.

## 2. Core Components

The implementation will involve the following key components, primarily within the `utils/ai/` and `schemas/ai.py` modules:

### 2.1. Pydantic Schemas (`schemas/ai.py`)

Define clear Pydantic models to represent:
*   `BenchmarkIdentifier`: Uniquely identifies a benchmark (name, metric, task categories).
*   `ModelBenchmarkScore`: A model's score on a specific benchmark (model name, benchmark identifier, score, source URL, ranking).
*   `LeaderboardData`: Structured data from a single leaderboard (name, source URL, last updated, list of `ModelBenchmarkScore`).
*   `ModelRecommendationRequest`: Input for the tool, specifying task details (description, type, preferred benchmarks, constraints, top N results).
*   `ModelRecommendation`: A single recommended model (name, reasoning, supporting scores, suitability score).
*   `ModelRecommendationResponse`: Output of the tool, containing a list of recommendations and any errors.

### 2.2. Leaderboard Parser Utility (`utils/ai/leaderboard_parser.py`)

*   **`fetch_leaderboard_data(leaderboard_url: str, parser_func: callable)`**:
    *   Fetches content from a given leaderboard URL.
    *   Uses a provided `parser_func` to process the content.
    *   Handles HTTP errors and general exceptions.
*   **`_parse_open_llm_leaderboard_api(json_string: str, source_url: str)`**:
    *   Specific parser for the Hugging Face Open LLM Leaderboard JSON API (`https://datasets-server.huggingface.co/first-rows?dataset=open-llm-leaderboard%2Fresults&config=default&split=train`).
    *   Maps JSON fields to `ModelBenchmarkScore` and `BenchmarkIdentifier`, including pre-defined `task_categories` for known benchmarks.
    *   Handles potential JSON decoding errors.
*   **(Future)** Additional parser functions for other leaderboards (HTML or API-based) can be added here.

### 2.3. Model Recommender Tool (`utils/ai/tools/model_recommender_tool.py`)

*   **`ModelRecommenderTool` Class**:
    *   `__init__(self, leaderboard_urls: Optional[List[str]])`: Initializes with a list of leaderboard URLs to consult.
    *   `_get_all_leaderboard_data(self)`: Fetches and caches data from all configured leaderboards using `fetch_leaderboard_data` and the appropriate parser.
    *   `_filter_scores_by_task(self, scores: List[ModelBenchmarkScore], request: ModelRecommendationRequest)`:
        *   Filters the collected benchmark scores based on the task description, task type, and preferred benchmarks from the request.
        *   Matches against `benchmark.task_categories`.
    *   `_rank_models(self, relevant_scores: List[ModelBenchmarkScore], top_n: int)`:
        *   Aggregates scores for each model from the relevant benchmarks.
        *   Calculates a heuristic suitability score.
        *   Ranks models and selects the top N.
        *   Generates a reasoning string for each recommendation.
    *   `async recommend_model(self, request: ModelRecommendationRequest) -> ModelRecommendationResponse`:
        *   Orchestrates the process: fetch data, filter scores, rank models.
        *   Returns a `ModelRecommendationResponse`.

## 3. Implementation Steps

1.  **Schema Definition:**
    *   Implement all Pydantic models listed in section 2.1 in `schemas/ai.py`.
    *   Ensure comprehensive docstrings and field descriptions.

2.  **Leaderboard Parser Implementation:**
    *   Implement `fetch_leaderboard_data` in `utils/ai/leaderboard_parser.py`.
    *   Implement `_parse_open_llm_leaderboard_api` with careful mapping of JSON fields and pre-defined `task_categories` for benchmarks like MMLU, ARC, HellaSwag, etc.
    *   Add robust error logging.

3.  **Model Recommender Tool Implementation:**
    *   Implement the `ModelRecommenderTool` class in `utils/ai/tools/model_recommender_tool.py`.
    *   Develop the logic for `_filter_scores_by_task`, focusing on matching request keywords with benchmark `task_categories`.
    *   Develop the ranking logic in `_rank_models`, considering average scores and number of relevant benchmarks.
    *   Implement the main `recommend_model` orchestration method.
    *   Include basic caching for fetched leaderboard data.

4.  **Tool Registration and Agent Integration:**
    *   The `ModelRecommenderTool` will be designed to be easily integrated into an agent's toolset (e.g., via AILF's `ToolManager` or a similar mechanism in Kagent).
    *   The agent will invoke the `recommend_model` method, providing a `ModelRecommendationRequest`.
    *   The agent will then use the `ModelRecommendationResponse` to make decisions (e.g., select a model for a subsequent task, present recommendations to a user).

5.  **Testing:**
    *   **Unit Tests (`tests/unit/utils/ai/`)**:
        *   Test Pydantic schema validation.
        *   Test the `_parse_open_llm_leaderboard_api` with sample JSON data (mocking the API response).
        *   Test the `_filter_scores_by_task` logic with various inputs.
        *   Test the `_rank_models` logic.
        *   Test the `ModelRecommenderTool.recommend_model` method by mocking `fetch_leaderboard_data_from_api`.
    *   **Integration Tests (`tests/integration/utils/ai/`)**:
        *   Test `fetch_leaderboard_data_from_api` with a live (but potentially rate-limited or controlled) call to the Hugging Face API endpoint to ensure the parser works with real data structure. (Use with caution to avoid actual network dependency in CI if possible, or use VCR.py).

6.  **Documentation:**
    *   Update this plan document as implementation progresses.
    *   Add Sphinx-style docstrings to all new classes, methods, and functions.
    *   Create a user guide in `docs/guides/` explaining how to use the `ModelRecommenderTool` and configure leaderboards.
    *   Generate API documentation for the new modules.

## 4. Key Considerations & Future Enhancements

*   **Parser Maintainability:** The JSON API is more stable than HTML scraping, but API structures can change.
*   **Benchmark Understanding:** The accuracy of `task_categories` assigned to benchmarks is crucial. This may require ongoing research and updates.
*   **Advanced Filtering/Ranking:**
    *   Implement more sophisticated NLP for matching task descriptions to benchmark categories.
    *   Allow weighting of benchmarks.
    *   Incorporate other model metadata (size, license, cost) if available.
*   **Dynamic Leaderboard Discovery:** Instead of hardcoding URLs, explore ways to discover relevant leaderboards.
*   **Caching Strategy:** Implement a more robust caching mechanism with TTL for leaderboard data.
*   **Configuration:** Externalize leaderboard URLs and parser-specific configurations.
*   **Error Handling:** Provide detailed error messages in the `ModelRecommendationResponse`.
*   **Full Dataset Access:** Investigate how to access the full dataset from `open-llm-leaderboard/results` if the `/first-rows` endpoint is insufficient. This might involve using the `datasets` library directly.

## 5. Timeline (Estimate)

*   **Week 1:** Schema definition, Leaderboard Parser (API version).
*   **Week 2:** Model Recommender Tool (filtering and ranking logic).
*   **Week 3:** Unit testing, initial agent integration PoC.
*   **Week 4:** Integration testing, documentation, refinement.

This plan provides a roadmap for developing a valuable tool that enhances an agent's intelligence by allowing it to make data-driven decisions about LLM selection.