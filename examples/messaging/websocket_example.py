"""
Example demonstrating WebSocket client and server implementation.

This example sets up a simple WebSocket server and client that exchange messages.
The server echoes back any message sent by clients.

To run the server:
    python websocket_example.py server

To run a client:
    python websocket_example.py client "Your message here"
"""

import argparse
import asyncio
import logging
import signal
import sys
from typing import Dict, Optional, Set

from schemas.messaging.websockets import (
    MessageType, StandardMessage
)
from utils.messaging.websocket_server import WebSocketServer
from utils.messaging.websocket_client import WebSocketClient


# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EchoServer:
    """Simple echo server that broadcasts messages to all clients."""
    
    def __init__(self, host: str = "localhost", port: int = 8765):
        """Initialize the echo server.
        
        Args:
            host: Host address to listen on
            port: Port number to use
        """
        self.server = WebSocketServer(host=host, port=port)
        self.clients: Set[str] = set()
        
        # Set up custom handlers
        self.server.on_connect = self.on_connect
        self.server.on_disconnect = self.on_disconnect
        self.server.on_message = self.on_message
        
        # Setup signal handling
        self.setup_signal_handling()
    
    def setup_signal_handling(self):
        """Set up signal handlers for graceful shutdown."""
        loop = asyncio.get_event_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, lambda: asyncio.create_task(self.shutdown()))
    
    async def start(self):
        """Start the echo server."""
        await self.server.start()
        logger.info(f"Echo server running on ws://{self.server.host}:{self.server.port}")
        
        # Keep running until stopped
        stop_event = asyncio.Event()
        await stop_event.wait()
    
    async def shutdown(self):
        """Shutdown the echo server gracefully."""
        logger.info("Shutting down echo server...")
        await self.server.stop()
        # Signal to exit
        for task in asyncio.all_tasks():
            if task is not asyncio.current_task():
                task.cancel()
    
    async def on_connect(self, websocket, message):
        """Handle client connection."""
        client_id = message.client_id or "unknown"
        logger.info(f"Client connected: {client_id}")
        self.clients.add(client_id)
        # Add client to a "chat" room
        self.server.add_to_room(client_id, "chat")
        return True
    
    async def on_disconnect(self, websocket, message):
        """Handle client disconnection."""
        # Find client by websocket
        client_id = None
        for cid in list(self.clients):
            client = self.server.clients.get(cid)
            if client and client.websocket == websocket:
                client_id = cid
                break
        
        if client_id:
            logger.info(f"Client disconnected: {client_id}")
            self.clients.remove(client_id)
    
    async def on_message(self, websocket, message):
        """Handle incoming messages."""
        # Find client by websocket
        client_id = None
        for cid, client in self.server.clients.items():
            if client.websocket == websocket:
                client_id = cid
                break
        
        if not client_id:
            logger.warning("Message from unknown client")
            return
        
        if message.type == MessageType.MESSAGE:
            logger.info(f"Message from {client_id}: {message}")
            
            # Create echo response
            echo_message = StandardMessage(
                content=f"Echo: {message.content}" if hasattr(message, "content") else "Echo",
                topic="echo"
            )
            
            # Broadcast to all clients in the "chat" room
            await self.server.broadcast_to_room("chat", echo_message)
        else:
            logger.info(f"Received message of type {message.type} from {client_id}")


class ChatClient:
    """Simple chat client using WebSockets."""
    
    def __init__(self, uri: str = "ws://localhost:8765"):
        """Initialize the chat client.
        
        Args:
            uri: WebSocket server URI
        """
        self.client = WebSocketClient(uri)
        # Add message handler
        self.client.add_message_handler(self.handle_message)
        # Setup signal handling
        self.setup_signal_handling()
        # Set up stop event
        self.stop_event = asyncio.Event()
    
    def setup_signal_handling(self):
        """Set up signal handlers for graceful shutdown."""
        loop = asyncio.get_event_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, lambda: asyncio.create_task(self.shutdown()))
    
    def handle_message(self, message):
        """Handle incoming messages."""
        if message.type == MessageType.MESSAGE:
            if hasattr(message, "content"):
                logger.info(f"Received: {message.content}")
            else:
                logger.info(f"Received message: {message}")
        elif message.type == MessageType.ERROR:
            logger.error(f"Error: {message.message}")
        else:
            logger.info(f"Received message of type {message.type}")
    
    async def connect(self):
        """Connect to the WebSocket server."""
        await self.client.connect()
    
    async def send_message(self, content):
        """Send a message to the server.
        
        Args:
            content: Message content to send
        """
        await self.client.send_message(content)
    
    async def receive_loop(self):
        """Loop to receive messages until stopped."""
        try:
            while not self.stop_event.is_set():
                try:
                    # Short timeout to allow for clean cancellation
                    message = await asyncio.wait_for(self.client.receive(), timeout=0.5)
                    # Message is already handled by the handler
                except asyncio.TimeoutError:
                    # Just retry
                    continue
                except Exception as e:
                    logger.error(f"Error receiving message: {e}")
                    break
        except asyncio.CancelledError:
            # Task was cancelled
            pass
    
    async def shutdown(self):
        """Shutdown the client gracefully."""
        logger.info("Shutting down client...")
        self.stop_event.set()
        await self.client.disconnect()
        # Signal to exit
        for task in asyncio.all_tasks():
            if task is not asyncio.current_task():
                task.cancel()


async def run_server(host: str, port: int):
    """Run a WebSocket echo server.
    
    Args:
        host: Host address to listen on
        port: Port number to use
    """
    server = EchoServer(host=host, port=port)
    await server.start()


async def run_client(uri: str, message: Optional[str] = None):
    """Run a WebSocket chat client.
    
    Args:
        uri: WebSocket server URI
        message: Optional message to send immediately
    """
    client = ChatClient(uri)
    
    try:
        # Connect to the server
        await client.connect()
        logger.info(f"Connected to {uri}")
        
        # Start receive loop
        receive_task = asyncio.create_task(client.receive_loop())
        
        # Send initial message if provided
        if message:
            await client.send_message(message)
            logger.info(f"Sent: {message}")
        
        # Interactive mode
        while True:
            try:
                # Wait for user input with a small timeout to allow for clean cancellation
                line = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: input("Enter message (or 'exit' to quit): ")
                )
                
                if line.strip().lower() == "exit":
                    break
                
                await client.send_message(line)
                logger.info(f"Sent: {line}")
                
            except KeyboardInterrupt:
                break
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error: {e}")
                break
        
        # Clean up
        receive_task.cancel()
        await client.shutdown()
        
    except Exception as e:
        logger.error(f"Client error: {e}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="WebSocket Example")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Server command
    server_parser = subparsers.add_parser("server", help="Run WebSocket server")
    server_parser.add_argument("--host", type=str, default="localhost", help="Host to bind")
    server_parser.add_argument("--port", type=int, default=8765, help="Port to use")
    
    # Client command
    client_parser = subparsers.add_parser("client", help="Run WebSocket client")
    client_parser.add_argument("--uri", type=str, default="ws://localhost:8765", help="Server URI")
    client_parser.add_argument("message", type=str, nargs="?", help="Message to send")
    
    args = parser.parse_args()
    
    if args.command == "server":
        asyncio.run(run_server(args.host, args.port))
    elif args.command == "client":
        asyncio.run(run_client(args.uri, args.message))
    else:
        parser.print_help()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
