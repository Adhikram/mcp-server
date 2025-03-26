# Database Schema MCP Server

A powerful MCP server that provides tools to read and expose database schemas from various database types (PostgreSQL, MySQL, SQLite, etc.).

## 🌟 Features

- Connect to different types of databases
- List all tables in a database
- Get detailed schema information for specific tables
- Get complete database schema including tables, views, and indexes
- Support for multiple database types (PostgreSQL, MySQL, SQLite)

## 🚀 Installation

### Prerequisites

1. Python 3.x
2. Virtual environment (recommended)

### Basic Installation

1. Create and activate a virtual environment:
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Unix/macOS:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

### Windows MCP Installation

1. Install Node.js:
   - Download and install from [Node.js official website](https://nodejs.org/en/download)
   - Verify installation by running `node --version` in PowerShell

2. Update System Path:
```powershell
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
```

3. If Node.js is not recognized, manually add to Path:
   - Press `Windows + R`
   - Type `sysdm.cpl` and press Enter
   - Go to "Advanced" tab
   - Click "Environment Variables"
   - Under "System variables", find and select "Path"
   - Click "Edit"
   - Add `C:\Program Files\nodejs\` if not present
   - Click "OK" on all windows
   - Restart your computer

4. Install MCP:
   - Download the `mcp-install.ps1` script
   - Unblock the file (right-click → Properties → Unblock)
   - Open PowerShell as Administrator and run:
     ```powershell
     Set-ExecutionPolicy unrestricted
     ```
   - Navigate to script location and run:
     ```powershell
     .\mcp-install.ps1 @modelcontextprotocol/server-postgres
     ```
   - Exit Claude Desktop completely (check system tray)
   - Configure server in `C:\Users\YOUR_USERNAME\AppData\Roaming\Claude\claude_desktop_config.json`
   - Copy MCP server config to `mcp.json` in Cursor
   - Restart Cursor

### MCP Configuration Example

Create a `.cursor/mcp.json` file in your project root with the following structure:

```json
{
    "mcpServers": {
        "local-db": {
            "args": [
                "C:\\Users\\YOUR_USERNAME\\AppData\\Roaming\\npm\\node_modules\\@modelcontextprotocol\\server-postgres\\dist\\index.js",
                "database-url"
            ],
            "command": "node"
        },
        "staging-db": {
            "args": [
                "C:\\Users\\YOUR_USERNAME\\AppData\\Roaming\\npm\\node_modules\\@modelcontextprotocol\\server-postgres\\dist\\index.js",
                "database-url"
            ],
            "command": "node"
        },
        "production-db": {
            "args": [
                "C:\\Users\\YOUR_USERNAME\\AppData\\Roaming\\npm\\node_modules\\@modelcontextprotocol\\server-postgres\\dist\\index.js",
                "database-url"
            ],
            "command": "node"
        }
    }
}
```

Replace `YOUR_USERNAME` with your Windows username and ensure the paths match your Node.js module installation location.

## 💻 Usage

### Starting the Server

```bash
python src/server.py
```

### Available Tools

#### 1. Connect to Database
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

#### 2. List Tables
```python
tables = await list_tables("postgresql://user:password@localhost:5432/mydb")
```

#### 3. Get Table Schema
```python
schema = await get_table_schema("postgresql://user:password@localhost:5432/mydb", "users")
```

#### 4. Get Database Schema
```python
schema = await get_database_schema("postgresql://user:password@localhost:5432/mydb")
```

## 📚 Example Usage with Claude

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

## 🔒 Security Best Practices

1. Never expose sensitive database credentials in client-side code
2. Use environment variables or secure configuration management for credentials
3. Implement proper access controls and authentication
4. Use SSL/TLS for database connections when possible 