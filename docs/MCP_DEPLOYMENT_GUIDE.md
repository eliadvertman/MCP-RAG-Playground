# MCP RAG Server Deployment Guide

This comprehensive guide walks you through deploying the MCP RAG server locally and integrating it with Claude Desktop for seamless AI-powered document search and retrieval.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Local Environment Setup](#local-environment-setup)
3. [MCP Server Deployment](#mcp-server-deployment)
4. [Claude Desktop Integration](#claude-desktop-integration)
5. [Testing the Integration](#testing-the-integration)
6. [Usage Examples](#usage-examples)
7. [Troubleshooting](#troubleshooting)
8. [Advanced Configuration](#advanced-configuration)

## Prerequisites

### System Requirements
- **Python**: 3.9 or higher
- **Operating System**: Windows, macOS, or Linux
- **Memory**: At least 4GB RAM (8GB recommended)
- **Storage**: 2GB free space for dependencies and vector database

### Required Software
- **Claude Desktop**: Latest version installed
- **uv** (recommended) or **pip**: Python package manager
- **Docker** (optional): For Milvus vector database
- **Git**: For cloning the repository

### Development Tools (Optional)
- **VS Code** or **PyCharm**: IDE for development
- **Postman**: For API testing

## Local Environment Setup

### 1. Clone the Repository

```bash
# Clone the repository
git clone https://github.com/your-username/mcp-rag-playground.git
cd mcp-rag-playground

# Verify you're in the correct directory
ls -la
# Should see: README.md, requirements.txt, mcp_rag_playground/, examples/, etc.
```

### 2. Set Up Python Environment

#### Option A: Using uv (Recommended)
```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create and activate virtual environment
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
uv pip install -r requirements.txt
```

#### Option B: Using pip and virtualenv
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

### 3. Install MCP Library

The MCP library is required for the server to function:

```bash
# Using uv
uv pip install "mcp[cli]>=1.2.0"

# Using pip
pip install "mcp[cli]>=1.2.0"
```

### 4. Set Up Vector Database (Optional but Recommended)

#### Quick Setup with Mock Services (Development)
For development and testing, you can use mock services without setting up a real vector database:

```bash
# Test with mock services
python examples/mcp_server_example.py
```

#### Production Setup with Milvus
For production use, set up Milvus vector database:

```bash
# Navigate to Milvus directory
cd vectordb/milvus

# Start Milvus with Docker Compose
docker-compose up -d

# Verify Milvus is running
docker-compose ps
# Should show milvus services as running

# Return to project root
cd ../..
```

## MCP Server Deployment

### 1. Verify Installation

First, test that the MCP server can be created:

```bash
# Test MCP server creation
python -c "
from mcp_rag_playground import create_mock_rag_mcp_server
server = create_mock_rag_mcp_server()
print('✅ MCP server created successfully!')
print(f'Server has {len(server.mcp._tools)} tools available')
"
```

Expected output:
```
✅ MCP server created successfully!
Server has 5 tools available
```

### 2. Test MCP Server Locally

Run the MCP server in development mode to test functionality:

```bash
# Run MCP server in development mode
uv run mcp dev examples/mcp_server_example.py
```

This will start the MCP server and show output like:
```
🚀 Starting RAG MCP Server...
✅ RAG MCP Server initialized with the following capabilities:
   🔧 Tools:
     - add_document_from_file: Add documents from file paths
     - add_document_from_content: Add documents from raw content
     - search_knowledge_base: Search for relevant documents
     - get_collection_info: Get knowledge base statistics
     - delete_collection: Remove all documents (⚠️  destructive)
   📄 Resources:
     - rag://collection/info: Collection information
     - rag://search/{query}: Search results
   📝 Prompts:
     - rag_search_prompt: Generate context-aware prompts for Q&A
🔗 Server ready for MCP connections!
```

### 3. Test with MCP Inspector (Optional)

The MCP inspector allows you to test server functionality interactively:

```bash
# Start MCP inspector (in a separate terminal)
mcp inspector

# Then connect to your server
# URL: stdio://uv run mcp dev examples/mcp_server_example.py
```

## Claude Desktop Integration

### 1. Locate Claude Desktop Configuration

Find your Claude Desktop configuration directory:

#### macOS
```bash
# Configuration directory
~/.config/claude-desktop/
```

#### Windows
```bash
# Configuration directory (adjust for your username)
C:\Users\[YourUsername]\AppData\Roaming\Claude\
```

#### Linux
```bash
# Configuration directory
~/.config/claude-desktop/
```

### 2. Create MCP Server Configuration

Create or edit the `mcp_servers.json` file in the configuration directory:

#### For Development (Mock Services)
```json
{
  "mcpServers": {
    "rag-knowledge-base": {
      "command": "uv",
      "args": [
        "run", 
        "mcp", 
        "dev", 
        "/absolute/path/to/mcp-rag-playground/examples/mcp_server_example.py"
      ],
      "env": {
        "PYTHONPATH": "/absolute/path/to/mcp-rag-playground"
      }
    }
  }
}
```

#### For Production (with Real Vector Database)
```json
{
  "mcpServers": {
    "rag-knowledge-base": {
      "command": "python",
      "args": [
        "/absolute/path/to/mcp-rag-playground/examples/mcp_server_production.py"
      ],
      "env": {
        "PYTHONPATH": "/absolute/path/to/mcp-rag-playground",
        "MCP_ENVIRONMENT": "prod"
      }
    }
  }
}
```

**Important**: Replace `/absolute/path/to/mcp-rag-playground` with the actual absolute path to your project directory.

### 3. Create Production Server Script

Create a production server script for better control:

```bash
# Create production server script
cat > examples/mcp_server_production.py << 'EOF'
#!/usr/bin/env python3
"""
Production MCP Server for RAG functionality.
"""
import os
import sys
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from mcp_rag_playground import create_rag_mcp_server

def main():
    """Create and return production MCP server."""
    environment = os.getenv("MCP_ENVIRONMENT", "prod")
    
    # Create MCP server for production
    rag_mcp_server = create_rag_mcp_server(
        environment=environment,
        collection_name="claude_desktop_rag_collection",
        server_name="Claude Desktop RAG Knowledge Base"
    )
    
    return rag_mcp_server.get_server()

if __name__ == "__main__":
    server = main()
EOF

# Make it executable
chmod +x examples/mcp_server_production.py
```

### 4. Restart Claude Desktop

After updating the configuration:

1. **Completely quit Claude Desktop**
   - macOS: Cmd+Q or right-click dock icon → Quit
   - Windows: File → Exit or close all windows
   - Linux: Application menu → Quit

2. **Restart Claude Desktop**
   - Launch Claude Desktop from your applications menu

3. **Verify MCP Server Connection**
   - Look for notification about MCP server connection
   - Check Claude Desktop logs if available

## Testing the Integration

### 1. Verify MCP Server is Connected

In a new Claude Desktop conversation, try asking:

```
Can you tell me what MCP tools are available?
```

You should see the RAG tools listed:
- `add_document_from_file`
- `add_document_from_content` 
- `search_knowledge_base`
- `get_collection_info`
- `delete_collection`

### 2. Test Document Addition

Add a document to test functionality:

```
Please add this content to the knowledge base: "Python is a high-level programming language known for its simplicity and readability. It was created by Guido van Rossum and first released in 1991."
```

### 3. Test Search Functionality

Search for the added content:

```
Search the knowledge base for information about Python programming.
```

### 4. Test File Upload

If you have a text file:

```
Please add the file "/path/to/your/document.txt" to the knowledge base.
```

## Usage Examples

### Example 1: Building a Personal Knowledge Base

```
1. "Add this content about machine learning to the knowledge base: 'Machine learning is a subset of artificial intelligence that enables computers to learn from data without being explicitly programmed.'"

2. "Please add the file '/Users/username/Documents/ml_notes.md' to the knowledge base."

3. "Search the knowledge base for information about machine learning algorithms."

4. "What does the knowledge base contain about neural networks?"
```

### Example 2: Document Research Assistant

```
1. "Add all the PDF files in my research folder to the knowledge base."

2. "Search for information about climate change impacts on agriculture."

3. "Generate a summary of what the knowledge base contains about renewable energy."

4. "Find documents that discuss both solar power and wind energy."
```

### Example 3: Code Documentation Helper

```
1. "Add the Python files from my project directory to the knowledge base."

2. "Search for functions that handle user authentication."

3. "What documentation exists about the database connection code?"

4. "Find examples of error handling patterns in the codebase."
```

### Example 4: Meeting Notes and Knowledge Management

```
1. "Add this meeting transcript to the knowledge base: [transcript content]"

2. "Search for previous discussions about product roadmap."

3. "What decisions were made in meetings about the marketing strategy?"

4. "Find action items assigned to specific team members."
```

## Troubleshooting

### Common Issues and Solutions

#### 1. "MCP server not found" Error

**Symptoms**: Claude Desktop shows MCP server connection failed

**Solutions**:
```bash
# Check file paths are absolute
pwd  # Note this absolute path
# Update mcp_servers.json with absolute paths

# Verify Python environment
which python
which uv

# Test server manually
uv run mcp dev examples/mcp_server_example.py
```

#### 2. "Module not found" Errors

**Symptoms**: ImportError when starting server

**Solutions**:
```bash
# Ensure virtual environment is activated
source .venv/bin/activate  # or venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
pip install "mcp[cli]>=1.2.0"

# Check PYTHONPATH in configuration
echo $PYTHONPATH
```

#### 3. Vector Database Connection Issues

**Symptoms**: Database connection timeouts or errors

**Solutions**:
```bash
# Check Milvus status
cd vectordb/milvus
docker-compose ps

# Restart Milvus if needed
docker-compose down
docker-compose up -d

# Use mock services for testing
# Edit server to use create_mock_rag_mcp_server()
```

#### 4. Permission Denied Errors

**Symptoms**: Cannot access files or directories

**Solutions**:
```bash
# Check file permissions
ls -la examples/mcp_server_example.py

# Make scripts executable
chmod +x examples/mcp_server_*.py

# Verify directory access
ls -la /path/to/your/project
```

#### 5. Claude Desktop Not Recognizing Tools

**Symptoms**: Tools don't appear in Claude Desktop

**Solutions**:
1. **Check Configuration Format**:
   ```json
   {
     "mcpServers": {
       "rag-knowledge-base": {
         "command": "uv",
         "args": ["run", "mcp", "dev", "examples/mcp_server_example.py"]
       }
     }
   }
   ```

2. **Verify Server Logs**:
   ```bash
   # Run server manually to see error messages
   uv run mcp dev examples/mcp_server_example.py
   ```

3. **Restart Claude Desktop Completely**

### Debug Mode

Enable debug logging for more detailed troubleshooting:

```bash
# Set debug environment variables
export MCP_DEBUG=1
export PYTHONPATH=/path/to/your/project

# Run server with debugging
uv run mcp dev examples/mcp_server_example.py
```

### Log Locations

Check these locations for helpful logs:

#### macOS
```bash
# Claude Desktop logs
~/Library/Logs/Claude/

# System logs
tail -f /var/log/system.log | grep Claude
```

#### Windows
```bash
# Claude Desktop logs
%APPDATA%\Claude\logs\

# Event viewer for system logs
```

#### Linux
```bash
# Application logs
~/.local/share/Claude/logs/

# System logs
journalctl -f | grep claude
```

## Advanced Configuration

### Environment-Specific Configurations

#### Development Configuration
```json
{
  "mcpServers": {
    "rag-dev": {
      "command": "uv",
      "args": ["run", "mcp", "dev", "examples/mcp_server_example.py"],
      "env": {
        "MCP_ENVIRONMENT": "dev",
        "MCP_DEBUG": "1"
      }
    }
  }
}
```

#### Production Configuration
```json
{
  "mcpServers": {
    "rag-prod": {
      "command": "python",
      "args": ["/opt/mcp-rag/examples/mcp_server_production.py"],
      "env": {
        "MCP_ENVIRONMENT": "prod",
        "MILVUS_HOST": "localhost",
        "MILVUS_PORT": "19530"
      }
    }
  }
}
```

### Custom Server Configuration

Create a custom server configuration:

```python
# examples/custom_mcp_server.py
import os
from mcp_rag_playground import create_rag_mcp_server

def main():
    # Custom configuration
    environment = os.getenv("MCP_ENVIRONMENT", "dev")
    collection_name = os.getenv("MCP_COLLECTION", "custom_collection")
    server_name = os.getenv("MCP_SERVER_NAME", "Custom RAG Server")
    
    server = create_rag_mcp_server(
        environment=environment,
        collection_name=collection_name,
        server_name=server_name
    )
    
    return server.get_server()

if __name__ == "__main__":
    main()
```

### Multiple Server Instances

Run multiple MCP servers for different use cases:

```json
{
  "mcpServers": {
    "rag-documents": {
      "command": "python",
      "args": ["examples/document_server.py"],
      "env": {"MCP_COLLECTION": "documents"}
    },
    "rag-code": {
      "command": "python", 
      "args": ["examples/code_server.py"],
      "env": {"MCP_COLLECTION": "codebase"}
    },
    "rag-meetings": {
      "command": "python",
      "args": ["examples/meetings_server.py"], 
      "env": {"MCP_COLLECTION": "meeting_notes"}
    }
  }
}
```

### Performance Optimization

#### For Large Document Collections
```python
# Configure for better performance
server = create_rag_mcp_server(
    environment="prod",
    collection_name="large_collection"
)

# Adjust search parameters for speed vs accuracy
# Use higher min_score for faster searches: min_score=0.8
# Use lower limit for faster results: limit=3
```

#### Memory Management
```bash
# Set memory limits
export PYTHONIOENCODING=utf-8
export OMP_NUM_THREADS=4

# Monitor memory usage
htop  # or Task Manager on Windows
```

### Security Considerations

#### File Access Control
- Ensure MCP server only has access to intended directories
- Use specific file paths rather than wildcards
- Implement file type validation

#### Network Security
- Run Milvus on localhost only for development
- Use proper authentication for production deployments
- Consider VPN access for remote deployments

### Backup and Recovery

#### Backup Knowledge Base
```bash
# Export collection data
python -c "
from mcp_rag_playground import create_rag_mcp_server
server = create_rag_mcp_server('prod')
info = server.rag_api.get_collection_info()
print(f'Collection has {info.get(\"document_count\", 0)} documents')
"
```

#### Recovery Procedures
1. Keep source documents backed up separately
2. Document your ingestion process
3. Test recovery procedures regularly

---

## Next Steps

1. **Start with Development**: Use mock services to test integration
2. **Add Your Documents**: Begin building your knowledge base
3. **Optimize Configuration**: Adjust settings based on your use case
4. **Monitor Performance**: Track response times and accuracy
5. **Scale Up**: Move to production when ready

For additional help, check the [main README](../README.md) or create an issue in the repository.

---

**Happy Knowledge Building! 🚀**