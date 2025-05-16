"""
Enhanced Tool Manager for registering and executing tools securely.

This module provides a unified ToolManager that handles both registration and execution
of tools with proper validation, security checks, and metrics. It's designed to be used
in AI agent systems to manage the lifecycle of tool execution.

Key Components:
    ToolManager: Main class for registering and executing tools
    ToolExecutionMetrics: Class for tracking tool execution statistics
    ToolExecutionError: Exception raised when tool execution fails
    ToolSecurityError: Exception raised when a security check fails

Example:
    >>> from ailf.tooling.manager_enhanced import ToolManager
    >>> from ailf.schemas.tooling import ToolDescription
    >>> 
    >>> # Create a tool manager
    >>> tool_manager = ToolManager()
    >>> 
    >>> # Register a tool
    >>> @tool_manager.register_tool_decorator(
    ...     ToolDescription(
    ...         name="calculate_sum",
    ...         description="Calculate the sum of two numbers",
    ...         input_schema_ref="my_schemas.CalculateInput"
    ...     )
    ... )
    ... def calculate_sum(a: int, b: int) -> int:
    ...     return a + b
    >>> 
    >>> # Execute a tool
    >>> result = await tool_manager.execute_tool("calculate_sum", {"a": 1, "b": 2})
    >>> assert result == 3
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
    """
    Custom exception for errors during tool execution.
    
    This exception is raised when a tool fails to execute properly due to issues like:
    - Input validation failures
    - Output validation failures
    - Errors during actual tool function execution
    - Problems with schema loading
    """
    pass

class ToolSecurityError(Exception):
    """
    Custom exception for security-related errors during tool execution.
    
    This exception is raised when a security check fails, such as:
    - Attempting to execute an unregistered tool
    - Detecting potentially dangerous input patterns
    - Violating security constraints defined for a tool
    """
    pass

def _load_model_from_ref(model_ref: str) -> Optional[Type[BaseModel]]:
    """
    Dynamically loads a Pydantic model class from a string reference.
    
    This helper function loads a Pydantic model class at runtime from a string path,
    enabling dynamic schema validation without requiring direct imports. This is
    especially useful when schemas are defined in separate modules that might not
    be known at compile time.

    :param model_ref: The string reference to the model class, in the format
                     "package.module.ClassName", e.g., "my_package.my_module.MyModel"
    :type model_ref: str
    :return: The loaded Pydantic model class, or None if loading fails
    :rtype: Optional[Type[BaseModel]]
    :raises ImportError: If the module cannot be imported (logged, not propagated)
    :raises AttributeError: If the class cannot be found in the module (logged, not propagated)
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
    """
    Metrics for tool execution.
    
    This class collects and maintains execution metrics for tools,
    including execution times, success/failure counts, and a limited
    execution history.
    """
    
    def __init__(self):
        """
        Initialize metrics collection.
        
        Sets up counters and data structures for tracking tool execution metrics.
        """
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
        Record a tool execution in the metrics history.
        
        This method logs execution details and maintains metrics counters.
        It also manages the execution history, keeping a limited number
        of recent executions for analysis purposes.
        
        :param tool_name: Name of the executed tool
        :type tool_name: str
        :param execution_time: Execution time in seconds
        :type execution_time: float
        :param success: Whether the execution was successful
        :type success: bool
        :param error_message: Error message if execution failed
        :type error_message: Optional[str]
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
        """
        Get the average execution time.
        
        :return: Average execution time in seconds. Returns 0.0 if no executions have occurred.
        :rtype: float
        """
        if self.execution_count == 0:
            return 0.0
        return self.total_execution_time / self.execution_count
    
    def get_success_rate(self) -> float:
        """
        Get the success rate as a decimal.
        
        :return: Success rate from 0.0 to 1.0. Returns 1.0 if no executions have occurred.
        :rtype: float
        """
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
        
        Creates a new tool manager instance with optional AI engine integration
        and metrics collection capabilities.
        
        :param ai_engine: Optional AI engine for enhanced pre/post-processing of tool inputs/outputs
        :type ai_engine: Optional[Any]
        :param enable_metrics: Whether to collect and track execution metrics
        :type enable_metrics: bool
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
        
        This is a convenient method for registering tools using a decorator pattern.
        It automatically detects whether the function is asynchronous and updates
        the tool description accordingly.
        
        :param description: The ToolDescription object for the tool
        :type description: ToolDescription
        :return: Decorator function that registers the decorated function as a tool
        :rtype: Callable
        :raises ValueError: If a tool with the same name is already registered
        
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
        
        :param tool_name: Name of the tool to retrieve description for
        :type tool_name: str
        :return: ToolDescription if found, None otherwise
        :rtype: Optional[ToolDescription]
        """
        return self._tool_descriptions.get(tool_name)
    
    def list_tools(self) -> List[ToolDescription]:
        """
        List descriptions of all registered tools.
        
        :return: List of tool descriptions for all registered tools
        :rtype: List[ToolDescription]
        """
        return list(self._tool_descriptions.values())
    
    def _perform_security_check(self, tool_name: str, tool_input: Dict[str, Any]) -> None:
        """
        Perform security checks on tool inputs.
        
        This method implements security validations before tool execution.
        It can be extended in subclasses to implement more sophisticated checks.
        
        :param tool_name: Name of the tool being executed
        :type tool_name: str
        :param tool_input: Input parameters for the tool
        :type tool_input: Dict[str, Any]
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
        
        This is the main entry point for tool execution. It handles the complete
        tool execution lifecycle:
        1. Tool lookup and security check
        2. Input validation against schema (if defined)
        3. Execution of the tool function
        4. Output validation against schema (if defined)
        5. Optional post-processing via AI engine
        6. Metrics collection

        :param tool_name: The name of the tool to execute
        :type tool_name: str
        :param tool_input: A dictionary of parameters for the tool
        :type tool_input: Dict[str, Any]
        :return: The result of the tool execution, potentially a Pydantic model instance if output schema is defined
        :rtype: Any
        :raises ToolExecutionError: If the tool is not found, input/output validation fails, or execution fails
        :raises ToolSecurityError: If a security check fails
        
        Example:
            >>> result = await tool_manager.execute_tool(
            ...     "calculate_sum", 
            ...     {"a": 10, "b": 5}
            ... )
            >>> print(result)  # 15
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
        
        This method attempts to validate the input parameters against the specified
        input schema (if any) using Pydantic. If validation succeeds, the validated
        data is returned. If no schema is provided, the original input is returned.
        
        :param tool_name: Name of the tool being validated
        :type tool_name: str
        :param tool_input: Input parameters for the tool
        :type tool_input: Dict[str, Any]
        :param tool_desc: Tool description containing input schema reference
        :type tool_desc: ToolDescription
        :return: Validated input data ready for tool execution
        :rtype: Dict[str, Any]
        :raises ToolExecutionError: If validation fails or schema loading fails
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
        
        Handles both synchronous and asynchronous tool functions. Synchronous
        functions are executed in a thread pool to avoid blocking the event loop.
        
        :param tool_func: The tool function to execute
        :type tool_func: Callable
        :param is_async: Whether the function is asynchronous
        :type is_async: bool
        :param input_data: Input parameters for the tool function
        :type input_data: Dict[str, Any]
        :return: Result from the tool function execution
        :rtype: Any
        :raises ToolExecutionError: If any exception occurs during execution
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
        
        This method ensures that the tool's output conforms to the expected schema.
        If a schema is defined but the output doesn't conform, validation will fail.
        The method handles different output types (raw, Pydantic models, dicts)
        and attempts to convert between them if necessary.
        
        :param tool_name: Name of the tool that produced the output
        :type tool_name: str
        :param result: Raw result from the tool execution
        :type result: Any
        :param tool_desc: Tool description containing output schema reference
        :type tool_desc: ToolDescription
        :return: Validated output, possibly converted to a Pydantic model
        :rtype: Any
        :raises ToolExecutionError: If validation fails or schema conversion fails
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
