# Database Schema MCP Server

This MCP server provides tools to read and expose database schemas from various database types (PostgreSQL, MySQL, SQLite, etc.).

## Features

- Connect to different types of databases
- List all tables in a database
- Get detailed schema information for specific tables
- Get complete database schema including tables, views, and indexes
- Support for multiple database types (PostgreSQL, MySQL, SQLite)

## Installation

1. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Start the server:
```bash
python src/server.py
```

2. The server provides the following tools:

### connect_database
Connect to a database using configuration parameters:
```python
config = {
    "type": "postgresql",  # or "mysql", "sqlite"
    "host": "localhost",
    "port": 5432,
    "database": "mydb",
    "username": "user",
    "password": "password"
}
result = await connect_database(config)
```

### list_tables
List all tables in a database:
```python
tables = await list_tables("postgresql://user:password@localhost:5432/mydb")
```

### get_table_schema
Get detailed schema information for a specific table:
```python
schema = await get_table_schema("postgresql://user:password@localhost:5432/mydb", "users")
```

### get_database_schema
Get complete database schema information:
```python
schema = await get_database_schema("postgresql://user:password@localhost:5432/mydb")
```

## Example Usage with Claude

You can use this server with Claude to analyze database schemas. For example:

```python
# Connect to a database
config = {
    "type": "postgresql",
    "host": "localhost",
    "port": 5432,
    "database": "mydb",
    "username": "user",
    "password": "password"
}
await connect_database(config)

# Get the complete schema
schema = await get_database_schema("postgresql://user:password@localhost:5432/mydb")

# Analyze the schema
print(f"Database has {len(schema['tables'])} tables")
for table_name, table_info in schema['tables'].items():
    print(f"\nTable: {table_name}")
    print(f"Columns: {len(table_info['columns'])}")
    print(f"Primary Keys: {table_info['primary_keys']}")
    print(f"Foreign Keys: {len(table_info['foreign_keys'])}")
```

## Security Note

When using this server, make sure to:
1. Never expose sensitive database credentials in client-side code
2. Use environment variables or secure configuration management for credentials
3. Implement proper access controls and authentication
4. Use SSL/TLS for database connections when possible 