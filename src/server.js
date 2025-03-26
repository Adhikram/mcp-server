#!/usr/bin/env node

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListResourcesRequestSchema,
  ListToolsRequestSchema,
  ReadResourceRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import pg from "pg";

const server = new Server(
  {
    name: "database-schema-server",
    version: "0.1.0",
  },
  {
    capabilities: {
      resources: {},
      tools: {},
    },
  }
);

const args = process.argv.slice(2);
if (args.length === 0) {
  console.error("Please provide a database URL as a command-line argument");
  process.exit(1);
}

const databaseUrl = args[0];

const resourceBaseUrl = new URL(databaseUrl);
resourceBaseUrl.protocol = "postgres:";
resourceBaseUrl.password = "";

const pool = new pg.Pool({
  connectionString: databaseUrl,
});

const SCHEMA_PATH = "schema";

// List all tables in the database
server.setRequestHandler(ListResourcesRequestSchema, async () => {
  const client = await pool.connect();
  try {
    const result = await client.query(
      "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
    );
    return {
      resources: result.rows.map((row) => ({
        uri: new URL(`${row.table_name}/${SCHEMA_PATH}`, resourceBaseUrl).href,
        mimeType: "application/json",
        name: `"${row.table_name}" database schema`,
      })),
    };
  } finally {
    client.release();
  }
});

// Get detailed schema information for a specific table
server.setRequestHandler(ReadResourceRequestSchema, async (request) => {
  const resourceUrl = new URL(request.params.uri);

  const pathComponents = resourceUrl.pathname.split("/");
  const schema = pathComponents.pop();
  const tableName = pathComponents.pop();

  if (schema !== SCHEMA_PATH) {
    throw new Error("Invalid resource URI");
  }

  const client = await pool.connect();
  try {
    // Get column information
    const columnsResult = await client.query(
      `SELECT 
        column_name,
        data_type,
        is_nullable,
        column_default
      FROM information_schema.columns 
      WHERE table_name = $1`,
      [tableName]
    );

    // Get primary keys
    const pkResult = await client.query(
      `SELECT c.column_name
      FROM information_schema.table_constraints tc
      JOIN information_schema.constraint_column_usage AS ccu USING (constraint_schema, constraint_name)
      JOIN information_schema.columns AS c ON c.table_schema = tc.constraint_schema
        AND tc.table_name = c.table_name AND ccu.column_name = c.column_name
      WHERE constraint_type = 'PRIMARY KEY' AND tc.table_name = $1`,
      [tableName]
    );

    // Get foreign keys
    const fkResult = await client.query(
      `SELECT
        tc.constraint_name,
        kcu.column_name,
        ccu.table_name AS foreign_table_name,
        ccu.column_name AS foreign_column_name
      FROM information_schema.table_constraints AS tc
      JOIN information_schema.key_column_usage AS kcu
        ON tc.constraint_name = kcu.constraint_name
        AND tc.table_schema = kcu.table_schema
      JOIN information_schema.constraint_column_usage AS ccu
        ON ccu.constraint_name = tc.constraint_name
        AND ccu.table_schema = tc.table_schema
      WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_name = $1`,
      [tableName]
    );

    const schemaInfo = {
      name: tableName,
      columns: columnsResult.rows.map(col => ({
        name: col.column_name,
        type: col.data_type,
        nullable: col.is_nullable === 'YES',
        default: col.column_default
      })),
      primary_keys: pkResult.rows.map(row => row.column_name),
      foreign_keys: fkResult.rows.map(row => ({
        name: row.constraint_name,
        constrained_columns: [row.column_name],
        referred_table: row.foreign_table_name,
        referred_columns: [row.foreign_column_name]
      }))
    };

    return {
      contents: [
        {
          uri: request.params.uri,
          mimeType: "application/json",
          text: JSON.stringify(schemaInfo, null, 2),
        },
      ],
    };
  } finally {
    client.release();
  }
});

// List available tools
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: "connect_database",
        description: "Test database connection",
        inputSchema: {
          type: "object",
          properties: {},
        },
      },
      {
        name: "list_tables",
        description: "List all tables in the database",
        inputSchema: {
          type: "object",
          properties: {},
        },
      },
      {
        name: "get_database_schema",
        description: "Get complete database schema information",
        inputSchema: {
          type: "object",
          properties: {},
        },
      },
      {
        name: "query",
        description: "Run a read-only SQL query",
        inputSchema: {
          type: "object",
          properties: {
            sql: { type: "string" },
          },
        },
      },
    ],
  };
});

// Handle tool calls
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const client = await pool.connect();
  try {
    switch (request.params.name) {
      case "connect_database":
        await client.query("SELECT 1");
        return {
          content: [{ type: "text", text: "Successfully connected to database" }],
          isError: false,
        };

      case "list_tables":
        const tablesResult = await client.query(
          "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
        );
        return {
          content: [{ type: "text", text: JSON.stringify(tablesResult.rows.map(r => r.table_name), null, 2) }],
          isError: false,
        };

      case "get_database_schema":
        const tables = await client.query(
          "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
        );
        
        const schemaInfo = {
          tables: {},
          views: [],
          indexes: {}
        };

        for (const table of tables.rows) {
          const tableSchema = await client.query(
            `SELECT 
              column_name,
              data_type,
              is_nullable,
              column_default
            FROM information_schema.columns 
            WHERE table_name = $1`,
            [table.table_name]
          );

          schemaInfo.tables[table.table_name] = {
            name: table.table_name,
            columns: tableSchema.rows.map(col => ({
              name: col.column_name,
              type: col.data_type,
              nullable: col.is_nullable === 'YES',
              default: col.column_default
            })),
            primary_keys: [],
            foreign_keys: []
          };
        }

        return {
          content: [{ type: "text", text: JSON.stringify(schemaInfo, null, 2) }],
          isError: false,
        };

      case "query":
        await client.query("BEGIN TRANSACTION READ ONLY");
        const result = await client.query(request.params.arguments?.sql);
        await client.query("ROLLBACK");
        return {
          content: [{ type: "text", text: JSON.stringify(result.rows, null, 2) }],
          isError: false,
        };

      default:
        throw new Error(`Unknown tool: ${request.params.name}`);
    }
  } catch (error) {
    return {
      content: [{ type: "text", text: `Error: ${error.message}` }],
      isError: true,
    };
  } finally {
    client.release();
  }
});

async function runServer() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
}

runServer().catch(console.error); 