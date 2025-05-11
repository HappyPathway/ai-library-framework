"""
Enhanced Tool Manager for registering and executing tools securely.

This module provides a unified ToolManager that handles both registration and execution
of tools with proper validation, security checks, and metrics.
"""
import importlib
import inspect
import logging
from typing import Any, Callable, Dict, List, Optional, Type, Union
import asyncio
import time

from pydantic import BaseModel, ValidationError

from ailf.schemas.tooling import ToolDescription

# Set up proper logging
logger = logging.getLogger(__name__)

class ToolExecutionError(Exception):
    """Custom exception for errors during tool execution."""
    pass

class ToolSecurityError(Exception):
    """Custom exception for security-related errors during tool execution."""
    pass

def _load_model_from_ref(model_ref: str) -> Optional[Type[BaseModel]]:
    """
    Dynamically loads a Pydantic model class from a string reference.

    :param model_ref: The string reference, e.g., "my_package.my_module.MyModel".
    :type model_ref: str
    :return: The loaded Pydantic model class, or None if loading fails.
    :rtype: Optional[Type[BaseModel]]
    """
    if not model_ref:
        return None
    try:
        module_path, class_name = model_ref.rsplit('.', 1)
        module = importlib.import_module(module_path)
        model_class = getattr(module, class_name)
        if not issubclass(model_class, BaseModel):
            logger.warning(f"Warning: {model_ref} is not a Pydantic BaseModel subclass.")
            return None
        return model_class
    except (ImportError, AttributeError, ValueError) as e:
        logger.error(f"Error loading model from ref '{model_ref}': {e}")
        return None

class ToolExecutionMetrics:
    """Metrics for tool execution."""
    
    def __init__(self):
        """Initialize metrics collection."""
        self.execution_count = 0
        self.total_execution_time = 0.0
        self.success_count = 0
        self.error_count = 0
        self.execution_history = []  # Limited history of recent executions
        self.max_history_items = 100
    
    def record_execution(self, 
                         tool_name: str, 
                         execution_time: float, 
                         success: bool, 
                         error_message: Optional[str] = None):
        """
        Record a tool execution.
        
        :param tool_name: Name of the executed tool
        :param execution_time: Execution time in seconds
        :param success: Whether the execution was successful
        :param error_message: Error message if execution failed
        """
        self.execution_count += 1
        self.total_execution_time += execution_time
        
        if success:
            self.success_count += 1
        else:
            self.error_count += 1
        
        # Record history
        entry = {
            "tool_name": tool_name,
            "execution_time": execution_time,
            "success": success,
            "timestamp": time.time()
        }
        if error_message:
            entry["error_message"] = error_message
        
        self.execution_history.append(entry)
        
        # Limit the history size
        if len(self.execution_history) > self.max_history_items:
            self.execution_history = self.execution_history[-self.max_history_items:]
    
    def get_avg_execution_time(self) -> float:
        """Get the average execution time."""
        if self.execution_count == 0:
            return 0.0
        return self.total_execution_time / self.execution_count
    
    def get_success_rate(self) -> float:
        """Get the success rate as a decimal (0.0 to 1.0)."""
        if self.execution_count == 0:
            return 1.0
        return self.success_count / self.execution_count

class ToolManager:
    """
    Enhanced manager for registering and executing tools securely.
    
    This class handles:
    - Tool registration with auto-detection of async functions
    - Input validation using Pydantic schemas
    - Secure execution with proper error handling
    - Output validation using Pydantic schemas
    - Collection of execution metrics
    - Optional integration with AIEngine for pre/post-processing
    """
    
    def __init__(self, ai_engine: Optional[Any] = None, enable_metrics: bool = True):
        """
        Initialize the ToolManager.
        
        :param ai_engine: Optional AI engine for enhanced processing
        :param enable_metrics: Whether to collect execution metrics
        """
        self.ai_engine = ai_engine
        self._tool_functions: Dict[str, Callable] = {}
        self._tool_descriptions: Dict[str, ToolDescription] = {}
        self.enable_metrics = enable_metrics
        self.metrics = ToolExecutionMetrics() if enable_metrics else None
    
    def register_tool(self, tool_function: Callable, description: ToolDescription) -> None:
        """
        Register a tool function along with its description.
        The `is_async` field in the provided `ToolDescription` instance will be
        updated based on introspection of the `tool_function`.

        :param tool_function: The actual callable function for the tool.
        :type tool_function: Callable
        :param description: The ToolDescription object for the tool.
        :type description: ToolDescription
        :raises ValueError: If a tool with the same name is already registered.
        """
        if description.name in self._tool_functions:
            raise ValueError(f"Tool with name '{description.name}' already registered.")

        # Auto-detect and set is_async based on the tool_function, updating the description instance.
        detected_is_async = inspect.iscoroutinefunction(tool_function)
        if description.is_async != detected_is_async:
            logger.info(f"Tool '{description.name}': is_async flag updated by ToolManager. "
                        f"Was: {description.is_async}, Detected: {detected_is_async}.")
            description.is_async = detected_is_async
        
        # Security check - we could implement additional checks here for unsafe operations
        # e.g., checking tool_function source for certain patterns, etc.
        
        self._tool_functions[description.name] = tool_function
        self._tool_descriptions[description.name] = description  # Store the (potentially updated) description
        logger.info(f"Tool '{description.name}' registered successfully.")
    
    def register_tool_decorator(self, description: ToolDescription):
        """
        Decorator for registering tool functions.
        
        :param description: The ToolDescription object for the tool.
        :return: Decorator function
        
        Example:
        ```python
        @tool_manager.register_tool_decorator(
            ToolDescription(
                name="summarize_text",
                description="Summarizes the provided text",
                keywords=["summary", "text", "summarize"],
                input_schema_ref="my_tools.schemas.SummarizeInput"
            )
        )
        def summarize_text(text: str, max_length: int = 100) -> str:
            # Implementation
            return summary
        ```
        """
        def decorator(func):
            self.register_tool(func, description)
            return func
        return decorator
    
    def get_tool_description(self, tool_name: str) -> Optional[ToolDescription]:
        """
        Get the description of a registered tool.
        
        :param tool_name: Name of the tool
        :return: ToolDescription if found, None otherwise
        """
        return self._tool_descriptions.get(tool_name)
    
    def list_tools(self) -> List[ToolDescription]:
        """
        List descriptions of all registered tools.
        
        :return: List of tool descriptions
        """
        return list(self._tool_descriptions.values())
    
    def _perform_security_check(self, tool_name: str, tool_input: Dict[str, Any]) -> None:
        """
        Perform security checks on tool inputs.
        
        :param tool_name: Name of the tool being executed
        :param tool_input: Input parameters for the tool
        :raises ToolSecurityError: If a security issue is detected
        """
        # Basic example security checks - these should be tailored to your specific needs
        if tool_name not in self._tool_functions:
            raise ToolSecurityError(f"Attempted to execute unknown tool: {tool_name}")
            
        # Additional security checks can be implemented here
        # For example, checking for malicious input patterns, restricting certain operations, etc.
    
    async def execute_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> Any:
        """
        Execute a registered tool by its name.

        :param tool_name: The name of the tool to execute.
        :type tool_name: str
        :param tool_input: A dictionary of parameters for the tool.
        :type tool_input: Dict[str, Any]
        :return: The result of the tool execution, potentially a Pydantic model instance if output schema is defined.
        :rtype: Any
        :raises ToolExecutionError: If the tool is not found, input/output validation fails, or execution fails.
        :raises ToolSecurityError: If a security check fails.
        """
        if tool_name not in self._tool_functions:
            logger.error(f"Tool '{tool_name}' not found.")
            raise ToolExecutionError(f"Tool '{tool_name}' not found.")

        tool_func = self._tool_functions[tool_name]
        tool_desc = self._tool_descriptions[tool_name]
        start_time = time.time()
        error_message = None
        success = False

        try:
            # Security check
            self._perform_security_check(tool_name, tool_input)
            
            # Pre-processing with AI engine if available
            if self.ai_engine and hasattr(self.ai_engine, 'preprocess_tool_input'):
                try:
                    tool_input = await self.ai_engine.preprocess_tool_input(
                        tool_name, tool_input, tool_desc)
                except Exception as e:
                    logger.warning(f"AI engine preprocessing failed for tool {tool_name}: {e}")
                    # Continue without preprocessing
            
            # Input validation
            validated_input_data = await self._validate_input(tool_name, tool_input, tool_desc)
            
            # Execute the tool function
            result = await self._execute_tool_function(tool_func, tool_desc.is_async, validated_input_data)
            
            # Output validation
            validated_result = await self._validate_output(tool_name, result, tool_desc)
            
            # Post-processing with AI engine if available
            if self.ai_engine and hasattr(self.ai_engine, 'postprocess_tool_output'):
                try:
                    validated_result = await self.ai_engine.postprocess_tool_output(
                        tool_name, validated_result, tool_desc)
                except Exception as e:
                    logger.warning(f"AI engine postprocessing failed for tool {tool_name}: {e}")
                    # Continue with original result
            
            success = True
            return validated_result
            
        except (ToolExecutionError, ToolSecurityError) as e:
            error_message = str(e)
            raise
        except Exception as e:
            error_message = f"Unexpected error during execution of tool {tool_name}: {e}"
            logger.exception(error_message)
            raise ToolExecutionError(error_message) from e
        finally:
            # Record metrics if enabled
            if self.enable_metrics and self.metrics:
                execution_time = time.time() - start_time
                self.metrics.record_execution(
                    tool_name=tool_name,
                    execution_time=execution_time,
                    success=success,
                    error_message=error_message
                )
    
    async def _validate_input(self, tool_name: str, tool_input: Dict[str, Any], 
                         tool_desc: ToolDescription) -> Dict[str, Any]:
        """
        Validate tool input using the input schema if available.
        
        :param tool_name: Name of the tool
        :param tool_input: Input parameters
        :param tool_desc: Tool description
        :return: Validated input data
        :raises ToolExecutionError: If validation fails
        """
        validated_input_data = tool_input
        InputModel = _load_model_from_ref(tool_desc.input_schema_ref) if tool_desc.input_schema_ref else None
        
        if InputModel:
            try:
                # If tool_input is already an instance of the model, use it directly
                if isinstance(tool_input, InputModel):
                    validated_model_instance = tool_input
                else:
                    validated_model_instance = InputModel(**tool_input)
                validated_input_data = validated_model_instance.model_dump()
            except ValidationError as ve:
                logger.error(f"Input validation failed for tool {tool_name}: {ve}")
                raise ToolExecutionError(f"Input validation failed for tool {tool_name}: {ve}") from ve
            except Exception as e:
                logger.error(f"Error preparing input for tool '{tool_name}': {e}")
                raise ToolExecutionError(f"Error preparing input for tool '{tool_name}': {e}")
        else:
            logger.debug(f"No input schema ref for tool {tool_name} or schema not loaded. "
                       f"Proceeding without Pydantic input validation.")
        
        return validated_input_data
    
    async def _execute_tool_function(self, tool_func: Callable, is_async: bool, 
                                input_data: Dict[str, Any]) -> Any:
        """
        Execute the tool function with the given input data.
        
        :param tool_func: The tool function to execute
        :param is_async: Whether the function is async
        :param input_data: Input parameters
        :return: Function result
        """
        try:
            if is_async:
                return await tool_func(**input_data)
            else:
                # Run sync functions in a thread pool to avoid blocking
                return await asyncio.to_thread(tool_func, **input_data)
        except Exception as e:
            raise ToolExecutionError(f"Error during tool execution: {e}") from e
    
    async def _validate_output(self, tool_name: str, result: Any, 
                          tool_desc: ToolDescription) -> Any:
        """
        Validate the tool output using the output schema if available.
        
        :param tool_name: Name of the tool
        :param result: Raw tool result
        :param tool_desc: Tool description
        :return: Validated output
        :raises ToolExecutionError: If validation fails
        """
        OutputModel = _load_model_from_ref(tool_desc.output_schema_ref) if tool_desc.output_schema_ref else None
        
        if OutputModel:
            try:
                if isinstance(result, OutputModel):
                    return result  # Already the correct Pydantic model instance
                elif isinstance(result, BaseModel):  # Another Pydantic model
                    logger.debug(f"Tool {tool_name} returned a Pydantic model of type "
                               f"{type(result).__name__}, expected {OutputModel.__name__}. "
                               f"Attempting conversion.")
                    return OutputModel(**result.model_dump())
                elif isinstance(result, dict):
                    return OutputModel(**result)
                else:
                    # Try direct validation for simple cases
                    return OutputModel.model_validate(result)

            except ValidationError as ve:
                logger.error(f"Output validation failed for tool {tool_name}: {ve}")
                raise ToolExecutionError(f"Output validation failed for tool {tool_name}: {ve}") from ve
            except Exception as e:
                logger.error(f"Error validating output for tool '{tool_name}': {e}")
                raise ToolExecutionError(f"Error validating output for tool '{tool_name}': {e}")
        else:
            logger.debug(f"No output schema ref for tool {tool_name} or schema not loaded. "
                       f"Returning raw result.")
        
        return result
