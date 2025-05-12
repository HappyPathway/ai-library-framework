"""Adaptive Learning Manager for AILF agents.

This module is responsible for using insights from performance analysis
to adapt and improve agent behavior, particularly focusing on prompt
optimization and strategy refinement.
"""

import logging
import time
import copy
import uuid
from typing import Any, Dict, Optional, List, Tuple, Set

from ailf.feedback.performance_analyzer import PerformanceAnalyzer
from ailf.cognition.prompt_library import PromptLibrary

logger = logging.getLogger(__name__)

class AdaptiveLearningManager:
    """
    Manages the adaptive learning loop for an AI agent.

    It uses data from the PerformanceAnalyzer to suggest or make changes
    to agent configurations, especially prompt templates, to improve performance.
    """

    def __init__(self, 
                 performance_analyzer: PerformanceAnalyzer,
                 prompt_library: Optional[PromptLibrary] = None,
                 config: Optional[Dict[str, Any]] = None,
                 ai_engine: Optional[Any] = None):
        """
        Initialize the AdaptiveLearningManager.

        :param performance_analyzer: An instance of PerformanceAnalyzer to get insights.
        :type performance_analyzer: PerformanceAnalyzer
        :param prompt_library: An instance of a prompt management system (PromptLibrary).
        :type prompt_library: Optional[PromptLibrary]
        :param config: Configuration dictionary for the manager.
        :type config: Optional[Dict[str, Any]]
        :param ai_engine: An optional AI engine for generating prompt improvements.
        :type ai_engine: Optional[Any]
        """
        self.performance_analyzer = performance_analyzer
        self.prompt_library = prompt_library
        self.config = config or {}
        self.ai_engine = ai_engine  # For LLM-based optimizations
        self._optimization_history = []  # Track optimization actions
        self._pending_optimizations = {}  # Store optimizations that haven't been applied yet
        logger.info("AdaptiveLearningManager initialized.")

    async def apply_insights_to_behavior(self, insights: Dict[str, Any]) -> None:
        """
        Apply insights from performance analysis to modify agent behavior.
        
        This is a high-level method that might orchestrate other specific
        adaptation methods.

        :param insights: A dictionary of insights, likely from PerformanceAnalyzer.
        :type insights: Dict[str, Any]
        """
        logger.info(f"Applying insights to behavior: {insights}")
        # Placeholder: Logic to interpret insights and trigger changes
        # For example, if insights show a particular prompt is underperforming,
        # it might trigger optimize_prompts for that prompt_template_id.
        if "prompt_analysis" in insights:
            for prompt_id, stats in insights["prompt_analysis"].items():
                if stats.get("error_rate", 0) > self.config.get("prompt_error_threshold", 0.5):
                    logger.warning(f"Prompt {prompt_id} has high error rate: {stats['error_rate']}. Optimizing prompt template.")
                    await self.optimize_prompts(prompt_template_id=prompt_id, metrics=stats)
        
        # Generate and collect prompt modification suggestions
        suggestions = await self.suggest_prompt_modifications(insights.get("prompt_analysis"))
        
        # Store suggestions as pending optimizations if they aren't already being tracked
        for template_id, suggestion in suggestions.items():
            if template_id not in self._pending_optimizations:
                self._pending_optimizations[template_id] = {
                    "suggestion": suggestion,
                    "timestamp": time.time(),
                    "metrics": insights.get("prompt_analysis", {}).get(template_id, {}),
                    "status": "pending"
                }
        
        # If auto-optimization is enabled, apply pending optimizations
        if self.config.get("auto_optimize_prompts", False):
            await self.apply_prompt_optimizations()

    async def optimize_prompts(self, 
                               prompt_template_id: str, 
                               metrics: Dict[str, Any]) -> Optional[str]:
        """
        Implement prompt self-correction and optimization using performance metrics.

        This could involve trying variations, adjusting parameters, or using an LLM
        to rewrite the prompt.

        :param prompt_template_id: The ID of the prompt template to optimize.
        :type prompt_template_id: str
        :param metrics: Performance metrics for this prompt.
        :type metrics: Dict[str, Any]
        :return: The new version ID of the optimized prompt, or None if no change made.
        :rtype: Optional[str]
        """
        logger.info(f"Attempting to optimize prompt: {prompt_template_id} based on metrics: {metrics}")
        if not self.prompt_library:
            logger.warning("Prompt library not available, cannot optimize prompts.")
            return None

        # Extract template ID and version from combined prompt key (e.g., "weather_query_v1.0")
        parts = prompt_template_id.split("_v")
        template_id = parts[0]
        version = parts[1] if len(parts) > 1 else None
        
        # Get current template
        current_template = self.prompt_library.get_template(template_id, version=version)
        if not current_template:
            logger.error(f"Could not find template {template_id} version {version} for optimization.")
            return None
            
        # Determine optimization strategy based on metrics
        new_template = None
        modification_made = False
        
        # Strategy 1: Improve clarity for high error rates
        if metrics.get("error_rate", 0) > self.config.get("error_rate_threshold", 0.3):
            logger.info(f"High error rate for {prompt_template_id}. Improving clarity.")
            # Apply clarity improvements
            if current_template.system_prompt:
                improved_system = f"{current_template.system_prompt}\nPlease be very specific and clear in your response."
                current_template.system_prompt = improved_system
                modification_made = True
            
        # Strategy 2: Add more specific instruction for low feedback
        if metrics.get("average_feedback_score") is not None and metrics["average_feedback_score"] < self.config.get("feedback_optimization_threshold", 0.5):
            logger.info(f"Low feedback for {prompt_template_id}. Enhancing instructions for better results.")
            # Enhance instructions
            current_template.description = f"{current_template.description} (Optimized for better user satisfaction)"
            modification_made = True
            
        # Strategy 3: Add examples for complex prompts with low success rate
        if metrics.get("successful_outcomes", 0) / metrics.get("total_uses", 1) < 0.7:
            logger.info(f"Low success rate for {prompt_template_id}. Adding examples might help.")
            # In a real implementation, you would add examples or enhance the template
            # based on successful interactions
            
        # Update the template if modifications were made
        if modification_made:
            try:
                # Add optimization tracking information
                current_template.updated_by_component = "AdaptiveLearningManager"
                current_template.optimization_source = "performance_metrics"
                current_template.optimization_metrics = metrics
                current_template.updated_at = time.time()
                
                # Create version notes
                version_notes = f"Automated optimization based on performance metrics: " \
                               f"Error rate: {metrics.get('error_rate', 'N/A')}, " \
                               f"Feedback score: {metrics.get('average_feedback_score', 'N/A')}"
                current_template.version_notes = version_notes
                
                # Update the template in the prompt library
                updated_template = self.prompt_library.update_template(
                    template_id, 
                    current_template.dict(),
                    version_notes=version_notes
                )
                
                if updated_template:
                    logger.info(f"Successfully optimized template {template_id} to version {updated_template.version}")
                    
                    # Record this optimization in history
                    self._optimization_history.append({
                        "template_id": template_id,
                        "original_version": version or "1.0",
                        "new_version": updated_template.version,
                        "timestamp": time.time(),
                        "metrics": metrics,
                        "changes": version_notes
                    })
                    
                    return str(updated_template.version)
                else:
                    logger.error(f"Failed to update template {template_id} in prompt library.")
            except Exception as e:
                logger.error(f"Failed to update template {template_id}: {str(e)}")
                
        return None

    async def manage_ab_testing(self, 
                                prompt_template_id: str, 
                                variations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Facilitate A/B testing of prompt variations.

        This would involve setting up the test, routing traffic, and collecting
        data for comparison.

        :param prompt_template_id: The ID of the prompt template to test.
        :type prompt_template_id: str
        :param variations: A list of variations to test (e.g., different instructions, parameters).
        :type variations: List[Dict[str, Any]]
        :return: A dictionary containing the test configuration and variation IDs.
        :rtype: Dict[str, Any]
        """
        logger.info(f"Setting up A/B test for prompt: {prompt_template_id} with variations: {variations}")
        if not self.prompt_library:
            logger.warning("Prompt library not available, cannot manage A/B tests for prompts.")
            return {"success": False, "error": "Prompt library not available"}
        
        try:
            # 1. Get the base template
            base_template = self.prompt_library.get_template(prompt_template_id)
            if not base_template:
                logger.error(f"Cannot find base template {prompt_template_id} for A/B testing")
                return {"success": False, "error": f"Template {prompt_template_id} not found"}
                
            # 2. Register each variation as a new version in the prompt library
            variation_ids = []
            for i, variation in enumerate(variations):
                # Create a variation ID that indicates it's part of an A/B test
                variation_id = f"{prompt_template_id}_ab_test_{i+1}"
                
                # Create a copy of the base template with modifications
                # Note: In a real implementation, we would need to properly deep copy 
                # the template and modify its attributes based on the variation
                modified_template = copy.deepcopy(base_template)
                
                # Apply the variation's changes to the modified template
                if "system_prompt" in variation:
                    modified_template.system_prompt = variation["system_prompt"]
                if "user_prompt_template" in variation:
                    modified_template.user_prompt_template = variation["user_prompt_template"]
                
                # Add metadata to track this as part of an A/B test
                modified_template.updated_by_component = "AdaptiveLearningManager"
                modified_template.optimization_source = "ab_testing"
                modified_template.version_notes = f"A/B testing variation {i+1}"
                
                # Add the variation to the prompt library
                self.prompt_library.add_new_template_version(prompt_template_id, modified_template)
                variation_ids.append(variation_id)
                
                logger.info(f"Registered A/B test variation {i+1} for {prompt_template_id} as {variation_id}")
            
            # 3. Store A/B test configuration
            test_config = {
                "test_id": f"test_{prompt_template_id}_{len(variations)}",
                "base_template": prompt_template_id,
                "variations": variation_ids,
                "start_time": int(time.time()),
                "status": "active",
                "metrics": {
                    "interactions": 0,
                    "success_rates": {},
                    "error_rates": {},
                    "feedback_scores": {}
                }
            }
            
            # In a real implementation, this would be stored in a database or other persistent storage
            # For now, we'll store it in memory as part of the config
            if "ab_tests" not in self.config:
                self.config["ab_tests"] = {}
            self.config["ab_tests"][test_config["test_id"]] = test_config
            
            logger.info(f"Successfully set up A/B test {test_config['test_id']} with {len(variations)} variations")
            return {
                "success": True,
                "test_id": test_config["test_id"],
                "variations": variation_ids
            }
            
        except Exception as e:
            logger.error(f"Failed to set up A/B test for {prompt_template_id}: {str(e)}")
            return {"success": False, "error": str(e)}

    async def suggest_prompt_modifications(self, 
                                         prompt_analysis_results: Optional[Dict[str, Any]] = None
                                         ) -> Dict[str, str]:
        """
        Suggest modifications to prompt templates based on analysis.

        This method does not apply changes but generates suggestions for human review
        or for other automated processes.

        :param prompt_analysis_results: The output from PerformanceAnalyzer.analyze_prompt_success.
        :type prompt_analysis_results: Optional[Dict[str, Any]]
        :return: A dictionary of prompt_template_id to suggested modification.
        :rtype: Dict[str, str]
        """
        suggestions = {}
        if not prompt_analysis_results:
            logger.info("No prompt analysis results to suggest modifications from.")
            return suggestions

        for prompt_key, stats in prompt_analysis_results.items():
            suggestion_text = []
            if stats.get("error_count", 0) > stats.get("total_uses", 0) * 0.3: # e.g. >30% error rate
                suggestion_text.append(f"High error rate ({stats['error_count']}/{stats['total_uses']}). Review for clarity or robustness.")
            
            avg_feedback = stats.get("average_feedback_score")
            if avg_feedback is not None and avg_feedback < self.config.get("feedback_suggestion_threshold", 0.2): # e.g. on a -1 to 1 scale
                suggestion_text.append(f"Low average feedback score ({avg_feedback:.2f}). Consider rephrasing or simplifying.")
            
            if not stats.get("successful_outcomes", 0) and stats.get("total_uses", 0) > 5 : # No successes after several uses
                 suggestion_text.append(f"No successful outcomes in {stats['total_uses']} uses. Major revision might be needed.")

            if suggestion_text:
                suggestions[prompt_key] = " ".join(suggestion_text)
                logger.info(f"Suggestion for {prompt_key}: {' '.join(suggestion_text)}")
        
        return suggestions

    async def suggest_prompt_improvements(self, underperforming_prompts: Dict[str, Any]) -> Dict[str, Any]:
        """
        Suggest improvements for underperforming prompts.
        
        This method would typically use an LLM or predefined strategies to generate
        improvements for the identified underperforming prompts.
        
        :param underperforming_prompts: Dictionary of underperforming prompts with their metrics.
        :type underperforming_prompts: Dict[str, Any]
        :return: Dictionary of suggested improvements by template ID.
        :rtype: Dict[str, Any]
        """
        if not underperforming_prompts:
            logger.info("No underperforming prompts to suggest improvements for.")
            return {}
            
        # In a real implementation, this would use an LLM (self.ai_engine) to suggest improvements
        # For this implementation, we'll use predefined strategies based on metrics
        
        suggestions = {}
        for prompt_id, data in underperforming_prompts.items():
            template_id = data["template_id"]
            current_text = data.get("current_text")
            
            if not current_text:
                logger.warning(f"No current text available for prompt {prompt_id}, skipping.")
                continue
                
            # Apply simple improvement strategies based on metrics
            improved_text = current_text
            reasoning = []
            
            # Strategy 1: Add more detail for high error rates
            if data.get("error_rate", 0) > 0.3:
                improved_text = improved_text.replace("{", "detailed {")
                reasoning.append("Added 'detailed' to request more information.")
                
            # Strategy 2: Use question format for low success rates
            if data.get("success_rate", 0) < 0.6 and not improved_text.strip().endswith("?"):
                # Convert statement to question if it's not already a question
                if not "?" in improved_text:
                    improved_text = f"What is {improved_text.lower()}?"
                    reasoning.append("Converted to question format for better engagement.")
            
            # Only include if we actually made changes
            if improved_text != current_text:
                suggestions[template_id] = {
                    "improved_text": improved_text,
                    "reasoning": " ".join(reasoning)
                }
                
        logger.info(f"Generated improvement suggestions for {len(suggestions)} prompts.")
        return suggestions
        
    def apply_prompt_improvements(self, improvements: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply suggested improvements to prompts in the prompt library.
        
        :param improvements: Dictionary of improvements by template ID.
        :type improvements: Dict[str, Any]
        :return: Dictionary of results for each template ID.
        :rtype: Dict[str, Any]
        """
        if not improvements:
            logger.info("No improvements to apply.")
            return {}
            
        if not self.prompt_library:
            logger.warning("Prompt library not available, cannot apply improvements.")
            return {"error": "Prompt library not available"}
            
        results = {}
        for template_id, improvement in improvements.items():
            try:
                # Get the latest version of the template
                template = self.prompt_library.get_template(template_id)
                if not template:
                    logger.error(f"Template {template_id} not found, cannot apply improvements.")
                    results[template_id] = {"status": "error", "message": "Template not found"}
                    continue
                    
                # Apply the improvement
                improved_text = improvement.get("improved_text")
                if not improved_text:
                    logger.warning(f"No improved text for template {template_id}, skipping.")
                    results[template_id] = {"status": "skipped", "message": "No improved text"}
                    continue
                
                # Prepare updated content
                update_content = {
                    "user_prompt_template": improved_text,
                    "updated_by_component": "AdaptiveLearningManager",
                    "optimization_source": "automated_improvement",
                    "updated_at": time.time()
                }
                
                # Create version notes
                version_notes = f"Automated improvement: {improvement.get('reasoning', 'No reasoning provided')}"
                
                # Update the template
                updated_template = self.prompt_library.update_template(
                    template_id, 
                    update_content,
                    version_notes=version_notes
                )
                
                if updated_template:
                    logger.info(f"Successfully updated template {template_id} to version {updated_template.version}")
                    results[template_id] = {
                        "status": "success", 
                        "version": updated_template.version,
                        "message": f"Updated to version {updated_template.version}"
                    }
                    
                    # Record this optimization in history
                    self._optimization_history.append({
                        "template_id": template_id,
                        "original_version": template.version,
                        "new_version": updated_template.version,
                        "timestamp": time.time(),
                        "changes": version_notes
                    })
                else:
                    logger.error(f"Failed to update template {template_id} in prompt library.")
                    results[template_id] = {"status": "error", "message": "Failed to update template"}
                
            except Exception as e:
                logger.error(f"Error applying improvement to {template_id}: {str(e)}")
                results[template_id] = {"status": "error", "message": str(e)}
                
        return results

    async def apply_prompt_optimizations(self, max_optimizations: int = None) -> Dict[str, Any]:
        """
        Apply pending optimizations to prompt templates in the prompt library.
        
        This method represents the key automated step in the end-to-end workflow,
        taking insights from the AdaptiveLearningManager and actually implementing
        them in the PromptLibrary.
        
        :param max_optimizations: Maximum number of optimizations to apply in one run.
        :type max_optimizations: Optional[int]
        :return: Dictionary of results.
        :rtype: Dict[str, Any]
        """
        if not self.prompt_library:
            logger.warning("Prompt library not available, cannot apply optimizations.")
            return {"status": "error", "message": "Prompt library not available"}
        
        # Check if there are any pending optimizations
        if not self._pending_optimizations:
            logger.info("No pending optimizations to apply.")
            return {"status": "success", "applied": 0, "message": "No pending optimizations"}
        
        # Sort pending optimizations by priority (can be enhanced with more complex prioritization)
        prioritized_optimizations = sorted(
            self._pending_optimizations.items(),
            key=lambda x: x[1].get("metrics", {}).get("error_rate", 0),
            reverse=True  # Higher error rate = higher priority
        )
        
        if max_optimizations:
            prioritized_optimizations = prioritized_optimizations[:max_optimizations]
        
        applied_count = 0
        failed_count = 0
        results = {}
        
        # Process each optimization
        for template_id, optimization_data in prioritized_optimizations:
            # Skip if already processed
            if optimization_data.get("status") == "applied":
                continue
                
            logger.info(f"Applying optimization to template: {template_id}")
            
            try:
                # Get the template
                template = self.prompt_library.get_template(template_id)
                if not template:
                    logger.error(f"Template {template_id} not found, cannot apply optimization.")
                    results[template_id] = {"status": "error", "message": "Template not found"}
                    failed_count += 1
                    continue
                
                # Generate the improvement based on metrics
                original_prompt = template.user_prompt_template
                metrics = optimization_data.get("metrics", {})
                
                # Use AI engine if available, otherwise use rule-based approach
                if self.ai_engine and self.config.get("use_ai_for_improvements", True):
                    # Implementation would depend on your AI engine interface
                    # This is a placeholder for the AI-based optimization
                    improved_prompt = await self._generate_ai_improvement(
                        template, 
                        metrics,
                        optimization_data.get("suggestion", "")
                    )
                else:
                    # Rule-based improvement
                    improved_prompt = self._generate_rule_based_improvement(
                        template, 
                        metrics,
                        optimization_data.get("suggestion", "")
                    )
                
                # Only update if there's actually a change
                if improved_prompt == original_prompt:
                    logger.info(f"No changes needed for template {template_id}")
                    self._pending_optimizations[template_id]["status"] = "skipped"
                    results[template_id] = {"status": "skipped", "message": "No changes needed"}
                    continue
                
                # Prepare the update
                update_content = {
                    "user_prompt_template": improved_prompt,
                    "updated_by_component": "AdaptiveLearningManager",
                    "optimization_source": "automated_optimization",
                    "optimization_metrics": metrics,
                    "updated_at": time.time()
                }
                
                # Create version notes
                version_notes = f"Automated optimization based on performance metrics: " \
                               f"Error rate: {metrics.get('error_rate', 'N/A')}, " \
                               f"Feedback score: {metrics.get('average_feedback_score', 'N/A')}"
                
                # Update the template
                updated_template = self.prompt_library.update_template(
                    template_id,
                    update_content,
                    version_notes=version_notes
                )
                
                if updated_template:
                    logger.info(f"Successfully updated template {template_id} to version {updated_template.version}")
                    self._pending_optimizations[template_id]["status"] = "applied"
                    self._pending_optimizations[template_id]["applied_at"] = time.time()
                    self._pending_optimizations[template_id]["new_version"] = updated_template.version
                    
                    results[template_id] = {
                        "status": "success",
                        "version": updated_template.version,
                        "message": f"Updated to version {updated_template.version}"
                    }
                    
                    # Record in optimization history
                    self._optimization_history.append({
                        "template_id": template_id,
                        "original_version": template.version,
                        "new_version": updated_template.version,
                        "timestamp": time.time(),
                        "metrics": metrics,
                        "changes": version_notes,
                        "optimization_id": str(uuid.uuid4())
                    })
                    
                    applied_count += 1
                else:
                    logger.error(f"Failed to update template {template_id}")
                    results[template_id] = {"status": "error", "message": "Failed to update template"}
                    failed_count += 1
            
            except Exception as e:
                logger.error(f"Error optimizing template {template_id}: {str(e)}")
                results[template_id] = {"status": "error", "message": str(e)}
                failed_count += 1
        
        # Prepare the summary response
        summary = {
            "status": "success" if failed_count == 0 else "partial",
            "applied": applied_count,
            "failed": failed_count,
            "details": results
        }
        
        logger.info(f"Applied {applied_count} optimizations, {failed_count} failed.")
        return summary

    async def _generate_ai_improvement(self, 
                                      template, 
                                      metrics: Dict[str, Any],
                                      suggestion: str) -> str:
        """
        Generate an improved prompt using the AI engine.
        
        :param template: The template to improve.
        :type template: PromptTemplateV1
        :param metrics: Performance metrics for the template.
        :type metrics: Dict[str, Any]
        :param suggestion: Suggestion text for improvement.
        :type suggestion: str
        :return: Improved prompt text.
        :rtype: str
        """
        # This would be implemented based on your AI engine's interface
        # For now, return the original as a placeholder
        if not self.ai_engine:
            return template.user_prompt_template
            
        try:
            # Example of how this might look with a generic AI engine interface
            system_prompt = """
            You are an expert prompt engineer. Improve the given prompt template based on 
            the performance metrics and suggestions provided. The improved prompt should:
            1. Be clearer and more specific
            2. Address any issues identified in the metrics (high error rate, low feedback)
            3. Maintain the original intent and functionality
            4. Keep all placeholders (variables in {curly braces})
            """
            
            user_prompt = f"""
            Original prompt template: "{template.user_prompt_template}"
            
            Performance metrics:
            - Error rate: {metrics.get('error_rate', 'N/A')}
            - Feedback score: {metrics.get('average_feedback_score', 'N/A')}
            - Success rate: {metrics.get('success_rate', 'N/A')}
            
            Suggestion: {suggestion}
            
            Please provide an improved version of the prompt template.
            """
            
            response = await self.ai_engine.generate_text(
                system_prompt=system_prompt,
                user_prompt=user_prompt
            )
            
            # Process the response to extract just the improved template
            # This would need to be adjusted based on your AI engine's output format
            improved_template = response.strip()
            
            logger.info(f"Generated AI improvement for template: {template.template_id}")
            return improved_template
            
        except Exception as e:
            logger.error(f"Error generating AI improvement: {str(e)}")
            # Fall back to the original template
            return template.user_prompt_template

    def _generate_rule_based_improvement(self, 
                                       template, 
                                       metrics: Dict[str, Any],
                                       suggestion: str) -> str:
        """
        Generate an improved prompt using rule-based strategies.
        
        :param template: The template to improve.
        :type template: PromptTemplateV1
        :param metrics: Performance metrics for the template.
        :type metrics: Dict[str, Any]
        :param suggestion: Suggestion text for improvement.
        :type suggestion: str
        :return: Improved prompt text.
        :rtype: str
        """
        prompt = template.user_prompt_template
        
        # Strategy 1: Improve clarity for high error rates
        if metrics.get("error_rate", 0) > 0.3:
            prompt = prompt.replace("provide", "provide detailed")
            prompt = prompt.replace("tell me", "explain in detail")
            
        # Strategy 2: Add structure for low success rates
        if metrics.get("success_rate", 0) < 0.6:
            if not prompt.lower().startswith("please"):
                prompt = f"Please {prompt.lower()}"
            if not "step by step" in prompt.lower():
                prompt = prompt.replace(".", ". Please provide a step-by-step response.")
        
        # Strategy 3: Add specificity for low feedback scores
        if metrics.get("average_feedback_score", 1.0) < 0.5:
            prompt = prompt.replace(".", ". Be specific and precise in your answer.")
            
        return prompt

    async def run_learning_cycle(self, auto_optimize: bool = False) -> Dict[str, Any]:
        """
        Run a full adaptive learning cycle: analyze, suggest, (potentially) adapt.
        This creates a continuous feedback loop for prompt strategy refinement.
        
        :param auto_optimize: If True, automatically apply optimizations to underperforming prompts.
        :type auto_optimize: bool
        :return: A dictionary containing insights and actions taken.
        :rtype: Dict[str, Any]
        """
        logger.info("Starting new adaptive learning cycle.")
        
        # 1. Analyze performance using all analyzer capabilities
        prompt_analysis = self.performance_analyzer.analyze_prompt_success()
        general_metrics = self.performance_analyzer.get_general_metrics()
        correlations = self.performance_analyzer.find_prompt_correlations()
        
        insights = {
            "prompt_analysis": prompt_analysis,
            "general_metrics": general_metrics,
            "correlations": correlations,
        }

        # 2. Generate suggestions based on insights
        suggestions = await self.suggest_prompt_modifications(prompt_analysis)
        
        # 3. Track which prompts were optimized or set for A/B testing
        optimized_prompts = []
        ab_test_configs = []
        
        # 4. Apply insights / Potentially adapt behavior
        await self.apply_insights_to_behavior(insights)
        
        # 5. Optionally perform automatic optimizations for underperforming prompts
        if auto_optimize:
            # If auto_optimize flag is set, immediately apply any pending optimizations
            optimization_results = await self.apply_prompt_optimizations()
            optimized_prompts = [
                {"template_id": tid, "result": result}
                for tid, result in optimization_results.get("details", {}).items()
                if result.get("status") == "success"
            ]
        
        # 6. Complete the learning cycle and return results
        results = {
            "timestamp": time.time(),
            "cycle_id": str(uuid.uuid4()),
            "insights": insights,
            "suggestions": suggestions,
            "optimized_prompts": optimized_prompts,
            "ab_tests_created": ab_test_configs,
            "general_metrics": general_metrics,
            "auto_optimize": auto_optimize
        }
        
        logger.info(f"Adaptive learning cycle completed. Optimized {len(optimized_prompts)} prompts, created {len(ab_test_configs)} A/B tests.")
        return results

    def identify_underperforming_prompts(self, config: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Identify prompt templates that are underperforming based on success rate metrics.
        
        :param config: Configuration for identifying underperforming prompts.
                      Can include 'success_rate_threshold' and 'min_sample_size'.
        :type config: Dict[str, Any]
        :return: A dictionary of underperforming prompt IDs with their metrics.
        :rtype: Dict[str, Any]
        """
        config = config or self.config
        success_rate_threshold = config.get("success_rate_threshold", 0.7)
        min_sample_size = config.get("min_sample_size", 5)
        
        # Get prompt analysis data
        prompt_analysis = self.performance_analyzer.analyze_prompt_success()
        if not prompt_analysis:
            logger.warning("No prompt analysis data available to identify underperforming prompts.")
            return {}
        
        underperforming = {}
        for prompt_id, stats in prompt_analysis.items():
            total_uses = stats.get("total_uses", 0)
            successful_outcomes = stats.get("successful_outcomes", 0)
            
            # Only consider prompts with enough usage data
            if total_uses >= min_sample_size:
                success_rate = successful_outcomes / total_uses if total_uses > 0 else 0
                
                # Check if this prompt is underperforming
                if success_rate < success_rate_threshold:
                    # Parse prompt ID to extract template ID and version
                    parts = prompt_id.split("_v")
                    template_id = parts[0]
                    version = parts[1] if len(parts) > 1 else "1.0"
                    
                    # Get the current prompt text if available
                    current_text = None
                    if self.prompt_library:
                        template = self.prompt_library.get_template(template_id, version=version)
                        if template and hasattr(template, 'user_prompt_template'):
                            current_text = template.user_prompt_template
                    
                    underperforming[prompt_id] = {
                        "template_id": template_id,
                        "version": version,
                        "success_rate": success_rate,
                        "error_rate": stats.get("error_count", 0) / total_uses if total_uses > 0 else 0,
                        "total_uses": total_uses,
                        "current_text": current_text
                    }
        
        logger.info(f"Identified {len(underperforming)} underperforming prompts.")
        return underperforming

    async def run_adaptation_cycle(self, 
                              auto_apply: bool = False, 
                              min_sample_size: int = 5, 
                              success_rate_threshold: float = 0.7) -> Dict[str, Any]:
        """
        Run a complete adaptation cycle that identifies underperforming prompts,
        suggests improvements, and optionally applies them.
        
        :param auto_apply: Whether to automatically apply suggested improvements.
        :type auto_apply: bool
        :param min_sample_size: Minimum sample size for considering a prompt.
        :type min_sample_size: int
        :param success_rate_threshold: Success rate threshold below which prompts are considered underperforming.
        :type success_rate_threshold: float
        :return: Dictionary with results of the adaptation cycle.
        :rtype: Dict[str, Any]
        """
        logger.info("Starting adaptation cycle...")
        
        # 1. Identify underperforming prompts
        config = {
            "min_sample_size": min_sample_size,
            "success_rate_threshold": success_rate_threshold
        }
        underperforming = self.identify_underperforming_prompts(config)
        
        # 2. Suggest improvements
        suggestions = await self.suggest_prompt_improvements(underperforming)
        
        # 3. Apply improvements if auto_apply is True
        applied_results = {}
        if auto_apply and suggestions:
            applied_results = self.apply_prompt_improvements(suggestions)
            
        # 4. Return results
        return {
            "cycle_id": str(uuid.uuid4()),
            "timestamp": time.time(),
            "underperforming_prompts": underperforming,
            "suggested_improvements": suggestions,
            "applied_results": applied_results,
            "auto_apply": auto_apply
        }

    def get_optimization_history(self, template_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get history of optimizations applied to templates.
        
        :param template_id: Optional template ID to filter history.
        :type template_id: Optional[str]
        :return: List of optimization records.
        :rtype: List[Dict[str, Any]]
        """
        if template_id:
            # Filter history by template_id
            return [
                record for record in self._optimization_history 
                if record["template_id"] == template_id
            ]
        
        return self._optimization_history

    def get_pending_optimizations(self) -> Dict[str, Any]:
        """
        Get all pending optimizations that haven't been applied yet.
        
        :return: Dictionary of pending optimizations.
        :rtype: Dict[str, Any]
        """
        # Filter to only include those with status "pending"
        return {
            template_id: data for template_id, data in self._pending_optimizations.items()
            if data.get("status") == "pending"
        }

    async def __aenter__(self):
        # Placeholder for any setup needed when used as a context manager
        logger.info("AdaptiveLearningManager entering context.")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Placeholder for any cleanup
        logger.info("AdaptiveLearningManager exiting context.")

