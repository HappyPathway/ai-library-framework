"""OpenAI Engine Implementation.

This module provides a concrete implementation of the AIEngineBase interface
for the OpenAI API, supporting GPT models.
"""
import asyncio
import json
import random
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Type, TypeVar, Union

try:
    import httpx
    from openai import AsyncOpenAI, BadRequestError, APIError, RateLimitError
    from pydantic import BaseModel, ValidationError, Field
except ImportError:
    raise ImportError(
        "OpenAI dependencies not installed. "
        "Install them with: pip install openai httpx pydantic"
    )

from ailf.core.ai_engine_base import AIEngineBase
from ailf.schemas.openai_entities import (
    Assistant, Thread, ThreadMessage, Run, RunStep, File, Tool
)
from ailf.schemas.embedding import CreateEmbeddingResponse, Embedding
from ailf.schemas.vector_store import (
    VectorStore, VectorStoreSearchResponse, VectorStoreFile, VectorStoreDeleted,
    VectorStoreSearchResult
)


T = TypeVar('T', bound=BaseModel)


class OpenAIEngine(AIEngineBase):
    """OpenAI implementation of AIEngineBase.
    
    This class provides a concrete implementation of AIEngineBase for OpenAI's GPT models,
    using the official OpenAI Python client.
    
    Example:
        ```python
        engine = OpenAIEngine(
            api_key="your_api_key",
            model="gpt-4",
            config={"temperature": 0.2}
        )
        
        # Simple text generation
        response = await engine.generate("Explain quantum computing")
        
        # Schema-based generation
        class Person(BaseModel):
            name: str
            age: int
            bio: str
            
        person = await engine.generate_with_schema(
            "Generate a fictional character",
            Person
        )
        print(f"{person.name}, {person.age} years old")
        print(person.bio)
        ```
    """
    
    def __init__(self, 
                api_key: str, 
                model: str = "gpt-4o", 
                config: Optional[Dict[str, Any]] = None,
                organization: Optional[str] = None):
        """Initialize OpenAI engine.
        
        Args:
            api_key: OpenAI API key
            model: Model name/identifier (e.g., 'gpt-4o', 'gpt-3.5-turbo')
            config: Optional configuration dictionary
            organization: Optional organization ID
        """
        self.api_key = api_key
        self.model = model
        self.organization = organization
        super().__init__(config)
        
    def _get_default_config(self) -> Dict[str, Any]:
        """Get OpenAI-specific default configuration.
        
        Returns:
            Dict[str, Any]: Default configuration dictionary
        """
        config = super()._get_default_config()
        config.update({
            "temperature": 0.7,
            "max_tokens": 1000,
            "top_p": 1.0,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0,
            "stream": False,
            "default_system_message": "You are a helpful, accurate, and concise assistant.",
        })
        return config
        
    def _initialize(self) -> None:
        """Initialize the OpenAI client."""
        self.client = AsyncOpenAI(
            api_key=self.api_key, 
            organization=self.organization
        )
        
        # Log initialization
        self.logger.info(
            "Initialized OpenAI engine with model %s", 
            self.model
        )
        
    def _prepare_message_params(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Prepare parameters for chat completion request.
        
        Args:
            prompt: The user prompt
            **kwargs: Additional parameters
            
        Returns:
            Dict[str, Any]: Parameters for the OpenAI API call
        """
        # Start with config values and override with kwargs
        params = {k: v for k, v in self.config.items() if k in [
            "temperature", 
            "max_tokens", 
            "top_p", 
            "frequency_penalty", 
            "presence_penalty",
            "stream"
        ]}
        
        params.update({k: v for k, v in kwargs.items() if k in [
            "temperature", 
            "max_tokens", 
            "top_p", 
            "frequency_penalty", 
            "presence_penalty",
            "stream",
            "stop",
            "tools",
            "tool_choice"
        ]})
        
        # Create message array
        messages = []
        
        # Add system message if provided or use default
        system_message = kwargs.get("system_message", 
                                  self.config.get("default_system_message"))
        if system_message:
            messages.append({"role": "system", "content": system_message})
            
        # Add conversation history if provided
        history = kwargs.get("history", [])
        if history:
            messages.extend(history)
            
        # Add the user prompt
        messages.append({"role": "user", "content": prompt})
        
        # Create final parameters dictionary
        final_params = {
            "model": kwargs.get("model", self.model),
            "messages": messages,
            **params
        }
        
        return final_params
        
    async def _make_request(self, params: Dict[str, Any]) -> Any:
        """Make an API request with retry logic.
        
        Args:
            params: Request parameters
            
        Returns:
            Any: API response
            
        Raises:
            Exception: On repeated failure after retries
        """
        retry_count = self.config.get("retry_count", 3)
        retry_delay = self.config.get("retry_delay", 1.0)
        timeout = self.config.get("timeout", 60.0)
        
        for attempt in range(retry_count + 1):
            try:
                start_time = time.time()
                response = await self.client.chat.completions.create(
                    **params,
                    timeout=timeout
                )
                elapsed = time.time() - start_time
                
                return response, elapsed
                
            except RateLimitError as e:
                # For rate limit errors, use exponential backoff
                self.logger.warning(
                    "OpenAI rate limit hit (attempt %d/%d)", 
                    attempt + 1, 
                    retry_count + 1
                )
                if attempt < retry_count:
                    # Calculate exponential backoff with jitter
                    delay = retry_delay * (2 ** attempt) + (0.1 * random.random())
                    await asyncio.sleep(delay)
                else:
                    raise e
                    
            except (APIError, httpx.ReadTimeout) as e:
                # For server errors, also retry with backoff
                self.logger.warning(
                    "OpenAI API error: %s (attempt %d/%d)", 
                    str(e),
                    attempt + 1, 
                    retry_count + 1
                )
                if attempt < retry_count:
                    # Linear backoff for other errors
                    delay = retry_delay * (attempt + 1)
                    await asyncio.sleep(delay)
                else:
                    raise e
                    
            except Exception as e:
                # Don't retry other exceptions
                raise e
        
    def _handle_response(self, response: Any) -> str:
        """Extract text from OpenAI API response.
        
        Args:
            response: OpenAI API response object
            
        Returns:
            str: Extracted text content
        """
        if hasattr(response, "choices") and response.choices:
            message = response.choices[0].message
            if message.content:
                return message.content
            # Handle tool calls or function calls if content is None
            return json.dumps({
                "tool_calls": [
                    {"function": tc.function.to_dict(), "id": tc.id, "type": tc.type}
                    for tc in message.tool_calls
                ] if hasattr(message, "tool_calls") and message.tool_calls else []
            })
        return str(response)
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count for a piece of text.
        
        This is a simple approximation. For accurate token counting,
        you should use the official tokenizer.
        
        Args:
            text: Text to estimate tokens for
            
        Returns:
            int: Estimated token count
        """
        # Simple estimation: ~4 chars per token (very approximate)
        return len(text) // 4
        
    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate a response for the given prompt.
        
        Args:
            prompt: The prompt to send to OpenAI
            **kwargs: Additional parameters for the API call
            
        Returns:
            str: The generated response
            
        Raises:
            Exception: On API or validation errors
        """
        # Validate the prompt
        prompt = self._validate_prompt(prompt)
        
        try:
            # Prepare API parameters
            params = self._prepare_message_params(prompt, **kwargs)
            
            # Make the API request
            response, elapsed = await self._make_request(params)
            
            # Extract and return the response text
            result = self._handle_response(response)
            
            # Log the request
            self._log_request(
                prompt, 
                result, 
                {
                    "model": params["model"],
                    "latency": elapsed,
                    "tokens": self._estimate_tokens(prompt) + self._estimate_tokens(result),
                }
            )
            
            return result
            
        except Exception as e:
            self._handle_error(e, prompt)
            # If we get here, fail_on_error is False
            return f"Error: {str(e)}"
            
    async def generate_with_schema(self, 
                                 prompt: str, 
                                 output_schema: Type[T],
                                 **kwargs) -> T:
        """Generate a structured response based on the provided schema.
        
        Args:
            prompt: The prompt to send to OpenAI
            output_schema: Pydantic model class for response validation
            **kwargs: Additional parameters for the API call
            
        Returns:
            T: The structured response as a Pydantic model instance
            
        Raises:
            ValidationError: If the response cannot be parsed into the schema
        """
        # Inject schema information into the prompt
        schema_json = output_schema.schema_json(indent=2)
        enhanced_prompt = f"""
        Based on the following request, please provide a response formatted according to this JSON schema:
        
        {schema_json}
        
        Your response must be valid JSON that conforms to this schema.
        
        Request: {prompt}
        """
        
        # Set system message for better formatting
        system_message = kwargs.pop("system_message", 
                                  "You are a helpful assistant that always responds with valid JSON according to the requested schema.")
        
        # Lower temperature for more deterministic outputs
        temperature = kwargs.pop("temperature", 0.2)
        
        try:
            # Generate the response
            response = await self.generate(
                enhanced_prompt,
                system_message=system_message,
                temperature=temperature,
                **kwargs
            )
            
            # Extract JSON from response, handling code blocks
            if "```json" in response:
                # Extract JSON from code block
                json_text = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                # Extract from generic code block
                json_text = response.split("```")[1].strip()
            else:
                # Assume the whole response is JSON
                json_text = response
                
            # Parse and validate with the schema
            try:
                data = json.loads(json_text)
                result = output_schema.parse_obj(data)
                return result
            except (json.JSONDecodeError, ValidationError) as e:
                self.logger.error(
                    "Failed to parse response as JSON: %s", 
                    str(e),
                    response=response
                )
                
                # Try to fix common JSON issues and retry
                corrected_json = self._attempt_json_correction(response)
                if corrected_json:
                    try:
                        data = json.loads(corrected_json)
                        result = output_schema.parse_obj(data)
                        return result
                    except (json.JSONDecodeError, ValidationError):
                        pass
                
                # If still failing, try one more time with an explicit fix request
                retry_prompt = f"""
                The previous response couldn't be parsed as valid JSON for this schema:
                
                {schema_json}
                
                Please provide ONLY the JSON object with no explanation or code formatting.
                """
                
                response = await self.generate(
                    retry_prompt,
                    system_message="You must respond with only valid JSON that matches the schema, nothing else.",
                    temperature=0.1,  # Lower temperature for more deterministic output
                    **kwargs
                )
                
                # Try to parse the corrected response
                try:
                    data = json.loads(response)
                    result = output_schema.parse_obj(data)
                    return result
                except (json.JSONDecodeError, ValidationError) as e:
                    self.logger.error(
                        "Failed to parse corrected response: %s", 
                        str(e),
                        response=response
                    )
                    raise ValidationError(
                        f"Could not parse OpenAI response as valid JSON for the schema: {str(e)}",
                        output_schema
                    )
                    
        except Exception as e:
            self._handle_error(e, prompt)
            # If we reach here, fail_on_error is False
            raise ValidationError(
                f"Error generating schema-based response: {str(e)}",
                output_schema
            )
            
    def _attempt_json_correction(self, text: str) -> Optional[str]:
        """Attempt to correct common JSON formatting issues.
        
        Args:
            text: Text to correct
            
        Returns:
            Optional[str]: Corrected JSON text, or None if correction failed
        """
        # Try to extract JSON content if it's embedded in other text
        if "{" in text and "}" in text:
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                text = text[start:end]
                
        # Replace single quotes with double quotes
        text = text.replace("'", '"')
        
        # Try to fix trailing commas
        text = text.replace(",\n}", "\n}")
        text = text.replace(",\n]", "\n]")
        
        # Try to fix missing quotes around keys
        import re
        text = re.sub(r'(\s*)(\w+)(\s*):', r'\1"\2"\3:', text)
        
        # Try to verify it's valid JSON
        try:
            json.loads(text)
            return text
        except json.JSONDecodeError:
            return None
            
    # === Assistants API Factory Methods ===
    
    async def create_assistant(self, 
                             name: str, 
                             instructions: str,
                             model: Optional[str] = None,
                             tools: Optional[List[Dict[str, Any]]] = None,
                             file_ids: Optional[List[str]] = None,
                             metadata: Optional[Dict[str, str]] = None) -> Assistant:
        """Create a new OpenAI Assistant.
        
        Args:
            name: Assistant name
            instructions: Instructions for the assistant
            model: Optional model override (defaults to self.model)
            tools: Optional list of tools (e.g., code_interpreter, retrieval, function)
            file_ids: Optional list of file IDs to attach
            metadata: Optional metadata dictionary
        
        Returns:
            Assistant: The created assistant object
            
        Raises:
            Exception: On API errors
        """
        try:
            api_response = await self.client.beta.assistants.create(
                name=name,
                instructions=instructions,
                model=model or self.model,
                tools=tools or [],
                file_ids=file_ids or [],
                metadata=metadata or {}
            )
            
            assistant = Assistant.parse_obj(api_response.model_dump())
            self.logger.info("Created OpenAI Assistant: %s", assistant.id)
            return assistant
            
        except Exception as e:
            self._handle_error(e, f"Failed to create assistant: {name}")
            raise
    
    async def get_assistant(self, assistant_id: str) -> Assistant:
        """Retrieve an existing assistant.
        
        Args:
            assistant_id: ID of the assistant to retrieve
            
        Returns:
            Assistant: The assistant object
            
        Raises:
            Exception: On API errors
        """
        try:
            api_response = await self.client.beta.assistants.retrieve(assistant_id)
            return Assistant.parse_obj(api_response.model_dump())
        except Exception as e:
            self._handle_error(e, f"Failed to retrieve assistant: {assistant_id}")
            raise
    
    async def create_thread(self, 
                          messages: Optional[List[Dict[str, Any]]] = None,
                          metadata: Optional[Dict[str, str]] = None) -> Thread:
        """Create a new thread for assistant interactions.
        
        Args:
            messages: Optional initial messages for the thread
            metadata: Optional metadata for the thread
            
        Returns:
            Thread: The created thread object
            
        Raises:
            Exception: On API errors
        """
        try:
            api_response = await self.client.beta.threads.create(
                messages=messages or [],
                metadata=metadata or {}
            )
            
            thread = Thread.parse_obj(api_response.model_dump())
            self.logger.info("Created OpenAI Thread: %s", thread.id)
            return thread
            
        except Exception as e:
            self._handle_error(e, "Failed to create thread")
            raise
    
    async def get_thread(self, thread_id: str) -> Thread:
        """Retrieve an existing thread.
        
        Args:
            thread_id: ID of the thread to retrieve
            
        Returns:
            Thread: The thread object
            
        Raises:
            Exception: On API errors
        """
        try:
            api_response = await self.client.beta.threads.retrieve(thread_id)
            return Thread.parse_obj(api_response.model_dump())
        except Exception as e:
            self._handle_error(e, f"Failed to retrieve thread: {thread_id}")
            raise
    
    async def add_message(self, 
                        thread_id: str, 
                        content: str,
                        role: str = "user",
                        file_ids: Optional[List[str]] = None,
                        metadata: Optional[Dict[str, str]] = None) -> ThreadMessage:
        """Add a message to an existing thread.
        
        Args:
            thread_id: ID of the thread
            content: Message content
            role: Role for the message (typically 'user')
            file_ids: Optional list of file IDs to attach
            metadata: Optional metadata for the message
            
        Returns:
            ThreadMessage: The created message object
            
        Raises:
            Exception: On API errors
        """
        try:
            api_response = await self.client.beta.threads.messages.create(
                thread_id=thread_id,
                role=role,
                content=content,
                file_ids=file_ids or [],
                metadata=metadata or {}
            )
            
            return ThreadMessage.parse_obj(api_response.model_dump())
            
        except Exception as e:
            self._handle_error(e, f"Failed to add message to thread {thread_id}")
            raise
    
    async def get_thread_messages(self, 
                                thread_id: str,
                                limit: int = 20) -> List[ThreadMessage]:
        """Get messages from a thread.
        
        Args:
            thread_id: ID of the thread
            limit: Maximum number of messages to retrieve
            
        Returns:
            List[ThreadMessage]: List of messages
            
        Raises:
            Exception: On API errors
        """
        try:
            api_response = await self.client.beta.threads.messages.list(
                thread_id=thread_id,
                limit=limit
            )
            
            return [ThreadMessage.parse_obj(msg.model_dump()) for msg in api_response.data]
            
        except Exception as e:
            self._handle_error(e, f"Failed to get messages for thread {thread_id}")
            raise
    
    async def create_run(self, 
                       thread_id: str, 
                       assistant_id: str,
                       instructions: Optional[str] = None,
                       tools: Optional[List[Dict[str, Any]]] = None,
                       metadata: Optional[Dict[str, str]] = None) -> Run:
        """Create a new run for an assistant on a thread.
        
        Args:
            thread_id: ID of the thread
            assistant_id: ID of the assistant to use
            instructions: Optional override instructions for this run
            tools: Optional override tools for this run
            metadata: Optional metadata for the run
            
        Returns:
            Run: The created run object
            
        Raises:
            Exception: On API errors
        """
        try:
            params = {
                "assistant_id": assistant_id,
                "metadata": metadata or {}
            }
            
            if instructions is not None:
                params["instructions"] = instructions
                
            if tools is not None:
                params["tools"] = tools
            
            api_response = await self.client.beta.threads.runs.create(
                thread_id=thread_id,
                **params
            )
            
            run = Run.parse_obj(api_response.model_dump())
            self.logger.info("Created run %s for thread %s with assistant %s", 
                            run.id, thread_id, assistant_id)
            return run
            
        except Exception as e:
            self._handle_error(e, f"Failed to create run for thread {thread_id}")
            raise
    
    async def get_run(self, thread_id: str, run_id: str) -> Run:
        """Get the status of a run.
        
        Args:
            thread_id: ID of the thread
            run_id: ID of the run
            
        Returns:
            Run: The run object with current status
            
        Raises:
            Exception: On API errors
        """
        try:
            api_response = await self.client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run_id
            )
            
            return Run.parse_obj(api_response.model_dump())
            
        except Exception as e:
            self._handle_error(e, f"Failed to get run status for {run_id}")
            raise
    
    async def wait_for_run_completion(self, 
                                   thread_id: str, 
                                   run_id: str,
                                   poll_interval: float = 1.0,
                                   timeout: float = 300.0) -> Run:
        """Wait for a run to complete and return its status.
        
        Args:
            thread_id: ID of the thread
            run_id: ID of the run
            poll_interval: How often to check status (seconds)
            timeout: Maximum time to wait (seconds)
            
        Returns:
            Run: Final run status
            
        Raises:
            TimeoutError: If the run does not complete within the timeout
            Exception: On API errors
        """
        start_time = time.time()
        terminal_states = ["completed", "failed", "cancelled", "expired"]
        
        while True:
            run = await self.get_run(thread_id, run_id)
            
            if run.status in terminal_states:
                return run
                
            if time.time() - start_time > timeout:
                self.logger.warning("Run %s timed out after %.1f seconds", run_id, timeout)
                raise TimeoutError(f"Run {run_id} did not complete within timeout")
                
            await asyncio.sleep(poll_interval)
    
    async def upload_file(self, 
                        file_path: str,
                        purpose: str = "assistants") -> File:
        """Upload a file to OpenAI for use with assistants.
        
        Args:
            file_path: Path to the file
            purpose: Purpose of the file
            
        Returns:
            File: The uploaded file object
            
        Raises:
            Exception: On API errors
        """
        try:
            with open(file_path, "rb") as f:
                api_response = await self.client.files.create(
                    file=f,
                    purpose=purpose
                )
                
            file = File.parse_obj(api_response.model_dump())
            self.logger.info("Uploaded file: %s", file.id)
            return file
            
        except Exception as e:
            self._handle_error(e, f"Failed to upload file {file_path}")
            raise
    
    async def get_file(self, file_id: str) -> File:
        """Get file information.
        
        Args:
            file_id: ID of the file
            
        Returns:
            File: The file object
            
        Raises:
            Exception: On API errors
        """
        try:
            api_response = await self.client.files.retrieve(file_id)
            return File.parse_obj(api_response.model_dump())
        except Exception as e:
            self._handle_error(e, f"Failed to retrieve file {file_id}")
            raise
            
    async def interact_with_assistant(self,
                                    assistant_id: str,
                                    message: str,
                                    thread_id: Optional[str] = None,
                                    wait_for_completion: bool = True,
                                    timeout: float = 300.0,
                                    poll_interval: float = 1.0) -> Dict[str, Any]:
        """Send a message to an assistant and get the response.
        
        This method provides a complete assistant interaction workflow:
        1. Create a thread if not provided
        2. Add the message to the thread
        3. Create a run with the assistant
        4. Wait for the run to complete
        5. Return the assistant's response
        
        Args:
            assistant_id: ID of the assistant
            message: Message to send
            thread_id: Optional thread ID (creates new thread if None)
            wait_for_completion: Whether to wait for the run to complete
            timeout: Maximum time to wait for completion (seconds)
            poll_interval: How often to check status (seconds)
            
        Returns:
            Dict[str, Any]: Result with thread_id, run_id, status, and messages
            
        Raises:
            TimeoutError: If the run does not complete within the timeout
            Exception: On API errors
        """
        # Create a thread if none provided
        if thread_id is None:
            thread = await self.create_thread()
            thread_id = thread.id
            
        # Add the message to the thread
        await self.add_message(thread_id, message)
        
        # Create a run
        run = await self.create_run(thread_id, assistant_id)
        
        if wait_for_completion:
            # Wait for the run to complete
            run = await self.wait_for_run_completion(
                thread_id, 
                run.id,
                timeout=timeout,
                poll_interval=poll_interval
            )
            
            # Get the messages
            messages = await self.get_thread_messages(thread_id)
            
            # Return the results
            return {
                "thread_id": thread_id,
                "run_id": run.id,
                "status": run.status,
                "messages": messages
            }
        else:
            # Return immediately with run info
            return {
                "thread_id": thread_id,
                "run_id": run.id,
                "status": run.status
            }
            
    # === Embeddings API Methods ===
    
    async def create_embedding(self, 
                             input_text: Union[str, List[str]],
                             model: Optional[str] = "text-embedding-3-small",
                             encoding_format: Optional[str] = None,
                             dimensions: Optional[int] = None,
                             user: Optional[str] = None) -> CreateEmbeddingResponse:
        """Generate embeddings for text using OpenAI's embedding models.
        
        Args:
            input_text: Single string or list of strings to generate embeddings for
            model: Embedding model to use (defaults to "text-embedding-3-small")
            encoding_format: Optional encoding format ("float" or "base64")
            dimensions: Optional output dimensions for the embedding
            user: Optional user identifier for tracking
            
        Returns:
            CreateEmbeddingResponse: Object containing embeddings and usage info
            
        Raises:
            Exception: On API errors
        """
        try:
            params = {
                "input": input_text,
                "model": model,
            }
            
            if encoding_format:
                params["encoding_format"] = encoding_format
                
            if dimensions:
                params["dimensions"] = dimensions
                
            if user:
                params["user"] = user
            
            api_response = await self.client.embeddings.create(**params)
            
            embedding_response = CreateEmbeddingResponse.parse_obj(api_response.model_dump())
            
            # Log the request
            self.logger.info(
                "Generated embeddings with model %s (tokens: %d)", 
                model,
                api_response.usage.total_tokens
            )
            
            return embedding_response
            
        except Exception as e:
            self._handle_error(e, f"Failed to create embeddings")
            raise
    
    async def batch_create_embeddings(self, 
                                   texts: List[str], 
                                   batch_size: int = 100,
                                   **kwargs) -> List[List[float]]:
        """Create embeddings for a large batch of texts by splitting into smaller batches.
        
        Args:
            texts: List of strings to generate embeddings for
            batch_size: Maximum number of texts per batch
            **kwargs: Additional arguments to pass to create_embedding
            
        Returns:
            List[List[float]]: List of embedding vectors
            
        Raises:
            Exception: On API errors
        """
        # Split texts into batches
        batches = [
            texts[i:i + batch_size]
            for i in range(0, len(texts), batch_size)
        ]
        
        embeddings = []
        
        # Process each batch
        for batch in batches:
            response = await self.create_embedding(batch, **kwargs)
            
            # Extract embeddings and order by index
            batch_embeddings = sorted(
                response.data, 
                key=lambda x: x.index
            )
            
            # Append to results
            embeddings.extend([emb.embedding for emb in batch_embeddings])
        
        return embeddings
        
    # === Vector Store API Methods ===
    
    async def create_vector_store(self, 
                                name: str,
                                description: Optional[str] = None,
                                metadata: Optional[Dict[str, Any]] = None) -> VectorStore:
        """Create a new vector store.
        
        Args:
            name: Name of the vector store
            description: Optional description
            metadata: Optional metadata dictionary
            
        Returns:
            VectorStore: The created vector store
            
        Raises:
            Exception: On API errors
        """
        try:
            # Build parameters directly in the API call to avoid type issues
            api_response = await self.client.vector_stores.create(
                name=name,
                description=description,
                metadata=metadata
            )
            
            vector_store = VectorStore.parse_obj(api_response.model_dump())
            self.logger.info("Created vector store: %s", vector_store.id)
            
            return vector_store
            
        except Exception as e:
            self._handle_error(e, f"Failed to create vector store: {name}")
            raise
    
    async def get_vector_store(self, vector_store_id: str) -> VectorStore:
        """Retrieve a vector store by ID.
        
        Args:
            vector_store_id: ID of the vector store
            
        Returns:
            VectorStore: The vector store object
            
        Raises:
            Exception: On API errors
        """
        try:
            api_response = await self.client.vector_stores.retrieve(vector_store_id)
            return VectorStore.parse_obj(api_response.model_dump())
        except Exception as e:
            self._handle_error(e, f"Failed to retrieve vector store: {vector_store_id}")
            raise
    
    async def list_vector_stores(self, 
                               limit: int = 20) -> List[VectorStore]:
        """List vector stores.
        
        Args:
            limit: Maximum number of vector stores to return
            
        Returns:
            List[VectorStore]: List of vector stores
            
        Raises:
            Exception: On API errors
        """
        try:
            api_response = await self.client.vector_stores.list(
                limit=limit
            )
            
            return [VectorStore.parse_obj(vs.model_dump()) for vs in api_response.data]
            
        except Exception as e:
            self._handle_error(e, "Failed to list vector stores")
            raise
    
    async def delete_vector_store(self, vector_store_id: str) -> VectorStoreDeleted:
        """Delete a vector store.
        
        Args:
            vector_store_id: ID of the vector store to delete
            
        Returns:
            VectorStoreDeleted: Deletion confirmation
            
        Raises:
            Exception: On API errors
        """
        try:
            api_response = await self.client.vector_stores.delete(vector_store_id)
            return VectorStoreDeleted.parse_obj(api_response.model_dump())
        except Exception as e:
            self._handle_error(e, f"Failed to delete vector store: {vector_store_id}")
            raise
    
    async def search_vector_store(self,
                                vector_store_id: str, 
                                query: str,
                                limit: int = 10) -> List[VectorStoreSearchResult]:
        """Search a vector store with a text query.
        
        Args:
            vector_store_id: ID of the vector store
            query: Search query text
            limit: Maximum number of results to return
            
        Returns:
            List[VectorStoreSearchResult]: Search results ordered by relevance
            
        Raises:
            Exception: On API errors
        """
        try:
            api_response = await self.client.vector_stores.search(
                vector_store_id=vector_store_id,
                query=query,
                limit=limit
            )
            
            # Convert to our schema format
            search_response = VectorStoreSearchResponse.parse_obj({
                "object": "vector_store.search_results",
                "data": [result.model_dump() for result in api_response.data]
            })
            
            return search_response.data
            
        except Exception as e:
            self._handle_error(e, f"Failed to search vector store: {vector_store_id}")
            raise
    
    async def upload_vector_store_file(self, 
                                     vector_store_id: str,
                                     file_path: str,
                                     purpose: str = "vector_store",
                                     metadata: Optional[Dict[str, Any]] = None,
                                     timeout: float = 300.0) -> VectorStoreFile:
        """Upload a file to a vector store.
        
        Args:
            vector_store_id: ID of the vector store
            file_path: Path to the file to upload
            purpose: Purpose of the file (default: "vector_store")
            metadata: Optional metadata dictionary
            timeout: Maximum time to wait for processing (seconds)
            
        Returns:
            VectorStoreFile: The uploaded file object
            
        Raises:
            TimeoutError: If file processing takes too long
            Exception: On API errors
        """
        try:
            with open(file_path, "rb") as f:
                # Upload and wait for processing to complete
                file = await self.client.vector_stores.files.upload_and_poll(
                    vector_store_id=vector_store_id,
                    file=f,
                    purpose=purpose,
                    metadata=metadata or {},
                    timeout=timeout
                )
            
            vector_store_file = VectorStoreFile.parse_obj(file.model_dump())
            self.logger.info("Uploaded file to vector store: %s", vector_store_file.id)
            
            return vector_store_file
            
        except Exception as e:
            self._handle_error(e, f"Failed to upload file to vector store: {vector_store_id}")
            raise
    
    async def delete_vector_store_file(self, 
                                     vector_store_id: str,
                                     file_id: str) -> Dict[str, Any]:
        """Delete a file from a vector store.
        
        Args:
            vector_store_id: ID of the vector store
            file_id: ID of the file to delete
            
        Returns:
            Dict[str, Any]: Deletion confirmation
            
        Raises:
            Exception: On API errors
        """
        try:
            api_response = await self.client.vector_stores.files.delete(
                vector_store_id=vector_store_id,
                file_id=file_id
            )
            
            return api_response.model_dump()
        except Exception as e:
            self._handle_error(e, f"Failed to delete file from vector store: {file_id}")
            raise