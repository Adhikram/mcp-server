"""
Test client for the Database Schema MCP Server
"""

import asyncio
import os
from typing import Any, Dict, List

from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client
from pydantic import BaseModel

class DatabaseConfig(BaseModel):
    """Configuration for database connection"""
    type: str = "postgresql"
    host: str = "localhost"
    port: int = 5432
    database: str = "test_db"
    username: str = "postgres"
    password: str = "postgres"
    options: Dict[str, Any] = {}

async def handle_sampling_message(
    message: types.CreateMessageRequestParams,
) -> types.CreateMessageResult:
    """Handle sampling messages from the server"""
    return types.CreateMessageResult(
        role="assistant",
        content=types.TextContent(
            type="text",
            text="Processing database schema request...",
        ),
        model="gpt-3.5-turbo",
        stopReason="endTurn",
    )

async def test_database_schema_server():
    """Test the database schema server functionality"""
    
    # Get database configuration from environment variables or use defaults
    db_config = DatabaseConfig(
        type=os.getenv("DB_TYPE", "postgresql"),
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5432")),
        database=os.getenv("DB_NAME", "test_db"),
        username=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "postgres"),
    )

    # Create server parameters for stdio connection
    server_params = StdioServerParameters(
        command="python",
        args=["/Users/mac/office/swarm-apps/mcp-server/src/server.py"],
        env={
            "DB_TYPE": db_config.type,
            "DB_HOST": db_config.host,
            "DB_PORT": str(db_config.port),
            "DB_NAME": db_config.database,
            "DB_USER": db_config.username,
            "DB_PASSWORD": db_config.password,
        },
    )

    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(
                read, write, sampling_callback=handle_sampling_message
            ) as session:
                # Initialize the connection
                await session.initialize()
                print("Connected to database schema server")

                # List available tools
                tools = await session.list_tools()
                print("\nAvailable tools:")
                for tool in tools:
                    print(f"- {tool.name}: {tool.description}")

                # Test database connection
                print("\nTesting database connection...")
                result = await session.call_tool("connect_database")
                print(f"Connection result: {result}")

                # List all tables
                print("\nListing all tables...")
                tables = await session.call_tool("list_tables")
                print(f"Found tables: {tables}")

                if tables:
                    # Get schema for the first table
                    first_table = tables[0]
                    print(f"\nGetting schema for table: {first_table}")
                    table_schema = await session.call_tool("get_table_schema", {"table_name": first_table})
                    print(f"Table schema: {table_schema}")

                    # Get complete database schema
                    print("\nGetting complete database schema...")
                    schema = await session.call_tool("get_database_schema")
                    print(f"Database schema: {schema}")
                else:
                    print("No tables found in the database")

    except Exception as e:
        print(f"Error during database schema testing: {str(e)}")
        raise

async def main():
    """Main entry point"""
    try:
        await test_database_schema_server()
    except Exception as e:
        print(f"Fatal error: {str(e)}")
        return 1
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code) 