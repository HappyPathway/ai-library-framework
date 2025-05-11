"""Enhanced AgentRouter implementation for ailf.routing."""
import asyncio
import inspect
import logging
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

from pydantic import BaseModel, Field

from ailf.schemas.interaction import AnyInteractionMessage
from ailf.schemas.routing import RouteDecision, RouteDecisionContext

# Set up proper logging
logger = logging.getLogger(__name__)

class RouteRule(BaseModel):
    """
    Definition of a routing rule for the AgentRouter.
    """
    name: str
    description: str = ""
    priority: int = 0  # Higher priority rules are evaluated first
    
    # These fields define the rule matching criteria
    match_system: Optional[str] = None  # Match target system
    match_type: Optional[str] = None  # Match message type
    match_keywords: List[str] = Field(default_factory=list)  # Keywords in content
    match_attributes: Dict[str, Any] = Field(default_factory=dict)  # Custom attributes
    
    # Target definition
    target_handler: Optional[str] = None  # Internal handler name
    target_agent_id: Optional[str] = None  # External agent ID
    
    # Optional handler for complex matching logic
    custom_match_handler: Optional[str] = None  # Reference to a function in internal_handlers
    
    class Config:
        arbitrary_types_allowed = True

class AgentRouter:
    """
    Enhanced AgentRouter for directing incoming messages to appropriate handlers or agents.
    
    Features:
    - Rule-based routing
    - LLM-driven routing decisions
    - Support for both internal handlers and external delegation
    - Customizable matching logic
    """
    
    def __init__(
        self, 
        ai_engine: Optional[Any] = None, 
        internal_handlers: Optional[Dict[str, Callable]] = None,
        debug_mode: bool = False
    ):
        """
        Initialize the AgentRouter.
        
        :param ai_engine: Optional AI engine for LLM-driven routing
        :param internal_handlers: Dictionary of handler functions
        :param debug_mode: Enable debug logging
        """
        self.ai_engine = ai_engine
        self.internal_handlers: Dict[str, Callable] = internal_handlers or {}
        self.routing_rules: List[RouteRule] = []
        self.debug_mode = debug_mode
    
    def add_internal_handler(self, handler_name: str, handler_function: Callable) -> None:
        """
        Register an internal handler function.
        
        :param handler_name: Name of the handler
        :param handler_function: Function to handle messages
        """
        if handler_name in self.internal_handlers:
            logger.warning(f"Handler '{handler_name}' already registered. Overwriting.")
        self.internal_handlers[handler_name] = handler_function
        logger.info(f"Registered internal handler: {handler_name}")
    
    def add_routing_rule(self, rule: RouteRule) -> None:
        """
        Add a routing rule.
        
        :param rule: The rule configuration
        """
        # Check that the target_handler exists if specified
        if rule.target_handler and rule.target_handler not in self.internal_handlers:
            logger.warning(f"Rule '{rule.name}' specifies non-existent handler: {rule.target_handler}")
        
        # Add the rule, maintaining sorted order by priority
        self.routing_rules.append(rule)
        self.routing_rules.sort(key=lambda r: -r.priority)  # Sort by priority (descending)
        logger.info(f"Added routing rule: {rule.name}")
    
    def handler_decorator(self, name: Optional[str] = None, **rule_kwargs):
        """
        Decorator to register a handler function and optionally create a rule.
        
        :param name: Optional custom name for the handler
        :param rule_kwargs: Optional arguments for creating a RouteRule
        :return: Decorator function
        
        Example:
        ```python
        @router.handler_decorator(match_type="query")
        async def handle_query(message: AnyInteractionMessage):
            # Handle query messages
            return response
        ```
        """
        def decorator(func):
            handler_name = name or func.__name__
            self.add_internal_handler(handler_name, func)
            
            # If rule arguments are provided, create a rule
            if rule_kwargs:
                rule = RouteRule(
                    name=f"auto_{handler_name}",
                    target_handler=handler_name,
                    **rule_kwargs
                )
                self.add_routing_rule(rule)
            
            return func
        return decorator
    
    async def _match_rule(self, rule: RouteRule, message: AnyInteractionMessage) -> bool:
        """
        Check if a message matches a routing rule.
        
        :param rule: Routing rule
        :param message: Message to test
        :return: True if the message matches the rule
        """
        # Check custom match handler first
        if rule.custom_match_handler and rule.custom_match_handler in self.internal_handlers:
            handler = self.internal_handlers[rule.custom_match_handler]
            try:
                if inspect.iscoroutinefunction(handler):
                    return await handler(message, rule)
                else:
                    return handler(message, rule)
            except Exception as e:
                logger.error(f"Error in custom match handler {rule.custom_match_handler}: {e}")
                return False
        
        # System match
        if rule.match_system and (
            not hasattr(message, 'header') or 
            not hasattr(message.header, 'target_system') or 
            message.header.target_system != rule.match_system
        ):
            return False
        
        # Type match
        if rule.match_type:
            message_type = getattr(message, 'type', None)
            if not message_type or message_type != rule.match_type:
                return False
        
        # Keywords match (if message has content field)
        if rule.match_keywords and hasattr(message, 'content'):
            content = message.content
            if isinstance(content, str):
                content_lower = content.lower()
                if not any(keyword.lower() in content_lower for keyword in rule.match_keywords):
                    return False
            else:
                # If content isn't a string, check if it has a 'text' attribute
                text = getattr(content, 'text', None)
                if isinstance(text, str):
                    text_lower = text.lower()
                    if not any(keyword.lower() in text_lower for keyword in rule.match_keywords):
                        return False
                else:
                    # If no text field to match against, keywords can't match
                    return False
        
        # Attributes match (can check arbitrary attributes)
        for key, value in rule.match_attributes.items():
            parts = key.split('.')
            obj = message
            
            # Navigate nested attributes
            for part in parts:
                if hasattr(obj, part):
                    obj = getattr(obj, part)
                else:
                    return False
            
            # Check if the final value matches
            if obj != value:
                return False
        
        # All checks passed
        return True
    
    async def make_route_decision(
        self, 
        message: AnyInteractionMessage, 
        context_override: Optional[RouteDecisionContext] = None
    ) -> RouteDecision:
        """
        Decide where to route the incoming message.
        
        :param message: Incoming message
        :param context_override: Optional custom context
        :return: Routing decision
        """
        # Use provided context or create one
        if context_override:
            decision_context = context_override
        else:
            decision_context = RouteDecisionContext(
                incoming_message=message,
                available_internal_handlers=list(self.internal_handlers.keys()),
                known_external_agents=[],
                routing_rules={rule.name: rule.dict() for rule in self.routing_rules}
            )
        
        # Method 1: Try rule-based routing first
        for rule in self.routing_rules:
            if await self._match_rule(rule, message):
                if self.debug_mode:
                    logger.debug(f"Message matched rule: {rule.name}")
                return RouteDecision(
                    target_handler=rule.target_handler,
                    target_agent_id=rule.target_agent_id,
                    confidence=1.0,
                    reasoning=f"Matched rule: {rule.name}"
                )
        
        # Method 2: Direct routing based on message header
        if hasattr(message, 'header') and hasattr(message.header, 'target_system'):
            target = message.header.target_system
            if target and target in self.internal_handlers:
                if self.debug_mode:
                    logger.debug(f"Message explicitly routed to: {target}")
                return RouteDecision(
                    target_handler=target,
                    confidence=0.9,
                    reasoning="Explicitly targeted handler in message header"
                )
        
        # Method 3: LLM-driven routing if AI engine is available
        if self.ai_engine and hasattr(self.ai_engine, 'analyze'):
            try:
                # This method requires AI engine with an analyze method that returns a RouteDecision
                llm_decision = await self.ai_engine.analyze(
                    decision_context,
                    output_schema=RouteDecision
                )
                
                # Validate the LLM decision - make sure the target handler exists
                if (llm_decision.target_handler and 
                    llm_decision.target_handler in self.internal_handlers):
                    if self.debug_mode:
                        logger.debug(f"LLM routing decision: {llm_decision.target_handler} "
                                    f"(confidence: {llm_decision.confidence})")
                    return llm_decision
                elif llm_decision.target_agent_id:
                    # External agent routing
                    if self.debug_mode:
                        logger.debug(f"LLM routing to external agent: {llm_decision.target_agent_id} "
                                    f"(confidence: {llm_decision.confidence})")
                    return llm_decision
            except Exception as e:
                logger.error(f"Error getting LLM routing decision: {e}")
        
        # Method 4: Fallback to default handlers
        for handler_name in ["default_handler", "catch_all_handler"]:
            if handler_name in self.internal_handlers:
                if self.debug_mode:
                    logger.debug(f"Using fallback handler: {handler_name}")
                return RouteDecision(
                    target_handler=handler_name,
                    confidence=0.5,
                    reasoning=f"Fallback to {handler_name}"
                )
        
        # No route found
        logger.info("No suitable route found for message")
        return RouteDecision(
            confidence=0.0,
            reasoning="No suitable route found"
        )
    
    async def route_message(
        self, 
        message: AnyInteractionMessage
    ) -> Union[Any, RouteDecision, None]:
        """
        Route a message by making a decision and executing the appropriate action.
        
        :param message: Incoming message
        :return: Result of handler, RouteDecision for external routing, or None
        """
        decision = await self.make_route_decision(message)
        
        if decision.target_handler and decision.target_handler in self.internal_handlers:
            # Route to internal handler
            handler_func = self.internal_handlers[decision.target_handler]
            logger.info(f"Routing message to internal handler: {decision.target_handler}")
            
            # Execute handler
            if inspect.iscoroutinefunction(handler_func):
                return await handler_func(message)
            else:
                return handler_func(message)
        
        elif decision.target_agent_id:
            # Return decision for external routing
            logger.info(f"Message should be routed to external agent: {decision.target_agent_id}")
            return decision
        
        else:
            # No action taken
            logger.info(f"No route action taken. Reasoning: {decision.reasoning}")
            return None
