"""
Database Schema MCP Server - A server that can read and expose database schemas
"""

import os
import asyncio
from typing import Any, Dict, List, Optional, AsyncIterator
from dataclasses import dataclass
from contextlib import asynccontextmanager
import sys

from mcp.server.fastmcp import FastMCP, Context
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.engine.url import URL

# Define server context
@dataclass
class ServerContext:
    engine: Any = None
    inspector: Any = None

@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[ServerContext]:
    """Initialize database connection on startup"""
    context = ServerContext()
    try:
        yield context
    finally:
        if context.engine:
            context.engine.dispose()

# Configure FastMCP with dependencies
mcp = FastMCP(
    "Database Schema Server",
    dependencies=[
        "sqlalchemy",
        "psycopg2-binary",
        "pymysql",
    ],
    lifespan=app_lifespan
)

# Store the connection string globally so it's accessible to tools
connection_string = None

@mcp.tool()
async def connect_database(
    ctx: Context = None
) -> Dict[str, Any]:
    """
    Connect to a SQL database using SQLAlchemy.
    Uses the connection string provided via command line.
    """
    global connection_string
    
    try:
        if ctx:
            ctx.info(f"Attempting to connect to database")
            
        engine = create_engine(connection_string)
        # Test connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        
        inspector = inspect(engine)
        
        # Store in context
        ctx.request_context.lifespan_context.engine = engine
        ctx.request_context.lifespan_context.inspector = inspector
        
        # Get all tables
        tables = inspector.get_table_names()
        
        return {
            "success": True,
            "tables": tables
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Database connection error: {str(e)}"
        }

@mcp.tool()
async def list_tables(ctx: Context = None) -> Dict[str, Any]:
    """List all tables in the database"""
    if not ctx.request_context.lifespan_context.inspector:
        return {
            "success": False,
            "error": "Not connected to database. Please connect first."
        }
    
    try:
        tables = ctx.request_context.lifespan_context.inspector.get_table_names()
        return {
            "success": True,
            "tables": tables
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Error listing tables: {str(e)}"
        }

@mcp.tool()
async def get_database_schema(ctx: Context = None) -> Dict[str, Any]:
    """Get complete database schema information"""
    if not ctx.request_context.lifespan_context.inspector:
        return {
            "success": False,
            "error": "Not connected to database. Please connect first."
        }
    
    try:
        inspector = ctx.request_context.lifespan_context.inspector
        schema_info = {
            "tables": {},
            "views": [],
            "indexes": {}
        }
        
        for table in inspector.get_table_names():
            columns = []
            for col in inspector.get_columns(table):
                columns.append({
                    "name": col["name"],
                    "type": str(col["type"]),
                    "nullable": col.get("nullable", True),
                    "default": str(col.get("default", ""))
                })
            
            schema_info["tables"][table] = {
                "name": table,
                "columns": columns,
                "primary_keys": inspector.get_pk_constraint(table).get("constrained_columns", []),
                "foreign_keys": inspector.get_foreign_keys(table)
            }
        
        return {
            "success": True,
            "schema": schema_info
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Error getting schema: {str(e)}"
        }

@mcp.tool()
async def query(sql: str, ctx: Context = None) -> Dict[str, Any]:
    """Run a read-only SQL query"""
    if not ctx.request_context.lifespan_context.engine:
        return {
            "success": False,
            "error": "Not connected to database. Please connect first."
        }
    
    try:
        with ctx.request_context.lifespan_context.engine.connect() as conn:
            conn.execute(text("BEGIN TRANSACTION READ ONLY"))
            try:
                result = conn.execute(text(sql))
                rows = [dict(row) for row in result]
                conn.execute(text("ROLLBACK"))
                return {
                    "success": True,
                    "rows": rows
                }
            except Exception as e:
                conn.execute(text("ROLLBACK"))
                raise e
    except Exception as e:
        return {
            "success": False,
            "error": f"Query error: {str(e)}"
        }

@mcp.resource("postgres://{user}@{host}:{port}/{table}/schema")
def table_schema_resource(user: str, host: str, port: str, table: str) -> str:
    """Get the schema for a specific table as a formatted resource"""
    if not mcp.lifespan_context.inspector:
        return "# Error\n\nNot connected to database. Please connect first."
    
    try:
        inspector = mcp.lifespan_context.inspector
        
        # Check if table exists
        if table not in inspector.get_table_names():
            return f"# Error\n\nTable '{table}' not found in database."
        
        # Get table schema
        columns = []
        for col in inspector.get_columns(table):
            columns.append({
                "name": col["name"],
                "type": str(col["type"]),
                "nullable": col.get("nullable", True),
                "default": str(col.get("default", ""))
            })
        
        schema_info = {
            "name": table,
            "columns": columns,
            "primary_keys": inspector.get_pk_constraint(table).get("constrained_columns", []),
            "foreign_keys": inspector.get_foreign_keys(table)
        }
        
        # Format as JSON (since mimeType is application/json)
        return {
            "table": schema_info["name"],
            "columns": [
                {
                    "name": col["name"],
                    "type": col["type"],
                    "nullable": col["nullable"],
                    "default": col["default"]
                }
                for col in schema_info["columns"]
            ],
            "primary_keys": schema_info["primary_keys"],
            "foreign_keys": schema_info["foreign_keys"]
        }
        
    except Exception as e:
        return {
            "error": f"Failed to get schema: {str(e)}"
        }

@mcp.prompt()
def explore_database() -> str:
    """Prompt for exploring the database schema"""
    return """I can help you explore the database schema. Here's what I can do:

1. List all tables in the database
2. Show detailed schema information for specific tables
3. Run read-only SQL queries to explore the data

What would you like to know about the database?"""

@mcp.prompt()
def query_database() -> str:
    """Prompt for querying the database"""
    return """I can help you query the database. Please provide your SQL query and I'll execute it.

Note: Only read-only queries are allowed for security reasons.

Example queries:
- SELECT * FROM table_name LIMIT 10
- SELECT column1, column2 FROM table_name WHERE condition
- SELECT COUNT(*) FROM table_name"""

if __name__ == "__main__":
    
    # Store the connection string globally
    # connection_string = "postgresql://postgres:postgres@localhost:5432/test_db"
    # connection_string = "postgresql://new_user:password@localhost:5432/sellers-db"
    connection_string = "mysql+pymysql://test_user:test_pass@localhost:3306/test_db"
    print(f"Connection string: {connection_string}", file=sys.stderr)
    
    # Run the server
    mcp.run() 