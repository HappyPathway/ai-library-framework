import importlib
import inspect
import time
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Type, Union
import asyncio

from pydantic import BaseModel, ValidationError

from ailf.schemas.tooling import ToolDescription, ToolUsageMetadata
# Optional: from ailf.ai_engine import AIEngine # If AI engine integration is needed later

# Logger placeholder
# import logging
# logger = logging.getLogger(__name__)

class ToolExecutionError(Exception):
    """Custom exception for errors during tool execution."""
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
            # logger.warning(f"Warning: {model_ref} is not a Pydantic BaseModel subclass.")
            print(f"Warning: {model_ref} is not a Pydantic BaseModel subclass.") # Replaced logger with print for now
            return None
        return model_class
    except (ImportError, AttributeError, ValueError) as e:
        # logger.error(f"Error loading model from ref '{model_ref}': {e}")
        print(f"Error loading model from ref '{model_ref}': {e}") # Replaced logger with print for now
        return None

class ToolManager:
    """
    Manages the registration and execution of tools.
    It stores tool functions and their descriptions, handles input/output validation
    using Pydantic schemas, and auto-detects async tool functions.
    """
    def __init__(self, ai_engine: Optional[Any] = None): # ai_engine is kept for potential future use
        """
        Initialize the ToolManager.

        :param ai_engine: Optional AI engine instance for AI-assisted tool operations
        :type ai_engine: Optional[Any]
        """
        self.tools: Dict[str, Dict[str, Any]] = {}
        self.ai_engine = ai_engine
    
    @property
    def tool_names(self) -> List[str]:
        """Get a list of all registered tool names."""
        return list(self.tools.keys())
    
    @property
    def tools_data(self) -> List[ToolDescription]:
        """Get a list of all tool descriptions."""
        return [self.tools[name]["description"] for name in self.tools]
    
    def register_tool(
        self,
        tool_description: ToolDescription,
        tool_callable: Callable,
        overwrite: bool = False
    ) -> None:
        """
        Register a tool with its description and callable.
        
        :param tool_description: The tool's metadata
        :type tool_description: ToolDescription
        :param tool_callable: The function that implements the tool
        :type tool_callable: Callable
        :param overwrite: Whether to overwrite if a tool with the same name already exists
        :type overwrite: bool
        :raises ValueError: If a tool with the same name exists and overwrite=False
        """
        name = tool_description.name
        
        # Check if tool exists
        if name in self.tools and not overwrite:
            raise ValueError(f"Tool with name '{name}' already exists. Use overwrite=True to replace it.")
        
        # Determine if the callable is async
        is_async = asyncio.iscoroutinefunction(tool_callable)
        
        # Store the tool
        self.tools[name] = {
            "description": tool_description,
            "callable": tool_callable,
            "is_async": is_async
        }
    
    async def execute_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        validate_inputs: bool = True,
        validate_outputs: bool = True
    ) -> Any:
        """
        Execute a registered tool with the given arguments.
        
        :param tool_name: The name of the tool to execute
        :type tool_name: str
        :param arguments: The arguments to pass to the tool
        :type arguments: Dict[str, Any]
        :param validate_inputs: Whether to validate inputs against input_schema_ref
        :type validate_inputs: bool
        :param validate_outputs: Whether to validate outputs against output_schema_ref
        :type validate_outputs: bool
        :return: The result of the tool execution
        :rtype: Any
        :raises ToolExecutionError: If the tool execution fails
        :raises KeyError: If the tool name is not found
        """
        # Verify the tool exists
        if tool_name not in self.tools:
            raise KeyError(f"Tool '{tool_name}' not found. Available tools: {', '.join(self.tools.keys())}")
        
        tool = self.tools[tool_name]
        tool_func = tool["callable"]
        description = tool["description"]
        is_async = tool["is_async"]
        
        # Record start time for performance measurement
        start_time = time.time()
        
        try:
            # Input validation
            cleaned_arguments = self._validate_inputs(description, arguments) if validate_inputs else arguments
            
            # Execute the tool
            if is_async:
                # This is an async function
                result = await tool_func(**cleaned_arguments)
            else:
                # This is a sync function, wrap it to not block
                result = await asyncio.to_thread(tool_func, **cleaned_arguments)
            
            # Output validation
            if validate_outputs and description.output_schema_ref:
                result = self._validate_outputs(description, result)
            
            # Log usage
            self._log_tool_usage(
                tool_name=tool_name,
                description=description,
                execution_time_ms=(time.time() - start_time) * 1000,
                success=True,
                inputs=arguments,
                outputs=result,
                error=None
            )
            
            return result
            
        except Exception as e:
            # Calculate execution time and log failure
            execution_time_ms = (time.time() - start_time) * 1000
            self._log_tool_usage(
                tool_name=tool_name,
                description=description,
                execution_time_ms=execution_time_ms,
                success=False,
                inputs=arguments,
                outputs=None,
                error=str(e)
            )
            
            # Re-raise as ToolExecutionError
            raise ToolExecutionError(f"Error executing tool '{tool_name}': {str(e)}") from e
    
    def _validate_inputs(self, description: ToolDescription, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate tool inputs against its input schema.
        
        :param description: Tool description containing input_schema_ref
        :type description: ToolDescription
        :param arguments: Arguments to validate
        :type arguments: Dict[str, Any]
        :return: Validated and potentially transformed arguments
        :rtype: Dict[str, Any]
        :raises ValidationError: If validation fails
        """
        if description.input_schema_ref:
            # Load the input schema model
            input_model = _load_model_from_ref(description.input_schema_ref)
            
            if input_model:
                # Create and validate the model instance
                try:
                    validated = input_model(**arguments)
                    return validated.model_dump() if hasattr(validated, 'model_dump') else validated.dict()
                except ValidationError as e:
                    error_msg = f"Input validation failed for tool '{description.name}': {str(e)}"
                    print(error_msg)  # Replace with logger
                    raise ValidationError(error_msg, model=input_model)
        
        # If no schema or validation not possible, return arguments unchanged
        return arguments
    
    def _validate_outputs(self, description: ToolDescription, outputs: Any) -> Any:
        """
        Validate tool outputs against its output schema.
        
        :param description: Tool description containing output_schema_ref
        :type description: ToolDescription
        :param outputs: Outputs to validate
        :type outputs: Any
        :return: Validated and potentially transformed outputs
        :rtype: Any
        :raises ValidationError: If validation fails
        """
        if description.output_schema_ref:
            output_model = _load_model_from_ref(description.output_schema_ref)
            
            if output_model:
                try:
                    if isinstance(outputs, dict):
                        validated = output_model(**outputs)
                    elif isinstance(outputs, output_model):
                        # Already a model instance
                        validated = outputs
                    else:
                        # Try to create a model from the output
                        validated = output_model(__root__=outputs)
                    
                    # Return the validated model
                    return validated
                except ValidationError as e:
                    error_msg = f"Output validation failed for tool '{description.name}': {str(e)}"
                    print(error_msg)  # Replace with logger
                    raise ValidationError(error_msg, model=output_model)
        
        # If no schema or validation not possible, return outputs unchanged
        return outputs
    
    def _log_tool_usage(
        self,
        tool_name: str,
        description: ToolDescription,
        execution_time_ms: float,
        success: bool,
        inputs: Dict[str, Any],
        outputs: Any,
        error: Optional[str]
    ) -> None:
        """
        Log information about tool usage for monitoring and analytics.
        
        :param tool_name: Name of the executed tool
        :type tool_name: str
        :param description: Tool description
        :type description: ToolDescription
        :param execution_time_ms: Execution time in milliseconds
        :type execution_time_ms: float
        :param success: Whether the execution was successful
        :type success: bool
        :param inputs: Tool inputs
        :type inputs: Dict[str, Any]
        :param outputs: Tool outputs
        :type outputs: Any
        :param error: Error message if execution failed
        :type error: Optional[str]
        """
        # For now, just create the log data - in a real implementation we'd send this to a logging or monitoring system
        usage_data = ToolUsageMetadata(
            tool_id=description.id,
            tool_name=tool_name,
            timestamp=datetime.utcnow().isoformat(),
            execution_time_ms=execution_time_ms,
            success=success,
            error_message=error,
            input_summary=inputs,  # In a real system we might sanitize sensitive data here
            output_summary=outputs if success else None  # Only include output if successful
        )
        
        # For debugging, print the usage data
        # print(f"Tool usage: {usage_data.json()}")
        
        # Update usage stats in the tool registry
        if tool_name in self.tools:
            self.tools[tool_name]["usage_count"] = self.tools[tool_name].get("usage_count", 0) + 1
            self.tools[tool_name]["last_used"] = usage_data.timestamp
