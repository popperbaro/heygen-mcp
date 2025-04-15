# Heygen MCP Server

A MCP (Model Control Protocol) server providing tools to interact with the Heygen API (V1 & V2), compatible with Claude Desktop and usable as a Python library.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Features

- Provides MCP tools for Heygen API actions:
  - Get Remaining Credits
  - List Voices
  - List Avatar Groups
  - List Avatars in a Group
  - Generate Avatar Video
  - Check Video Status
- Configurable Heygen API key via command-line or environment variable (`HEYGEN_API_KEY`).
- Asynchronous API client using `httpx` and `pydantic`.
- Command-line interface powered by `click`.
- Designed for use with Claude Desktop extensions.
- Can be imported and used as a Python library.

## Installation

### Prerequisites

- Python 3.12 or higher
- A Heygen API key (get one from [Heygen](https://www.heygen.com/))

### From GitHub (Currently Not on PyPI)

```bash
# Install directly from GitHub
pip install git+https://github.com/your-username/heygen-mcp.git

# Alternatively, clone and install
git clone https://github.com/your-username/heygen-mcp.git
cd heygen-mcp
pip install .
```

### For Development

1.  Clone this repository:

    ```bash
    git clone https://github.com/your-username/heygen-mcp.git
    cd heygen-mcp
    ```

2.  Install in editable mode:
    ```bash
    # Installs the package and dev dependencies
    pip install -e ".[dev]"
    ```

## Usage

### Command-Line Interface (CLI)

The package installs a command-line script `heygen-mcp`.

```bash
# Start the server (requires API key)

# Option 1: Pass key via argument
heygen-mcp --api-key YOUR_API_KEY

# Option 2: Use environment variable (recommended)
export HEYGEN_API_KEY=YOUR_API_KEY
heygen-mcp
```

The server will start on `http://localhost:8000` by default.

### Setting up with Claude Desktop

1.  Start the `heygen-mcp` server using one of the methods above.
2.  Open Claude Desktop.
3.  Go to `Settings > Extensions`.
4.  Click `Add MCP Server`.
5.  Enter a **Name** (e.g., "Heygen Video Tools").
6.  Enter the **URL** (typically `http://127.0.0.1:8000` or `http://localhost:8000`).
7.  Save and enable the extension.

Claude should now connect, and the Heygen tools will be available.

### Available MCP Tools

The server provides the following tools to Claude:

- **get_remaining_credits**: Retrieves the remaining credits in your Heygen account.
- **get_voices**: Retrieves a list of available voices from the Heygen API (limited to first 100 voices).
- **get_avatar_groups**: Retrieves a list of Heygen avatar groups.
- **get_avatars_in_avatar_group**: Retrieves a list of avatars in a specific Heygen avatar group.
- **generate_avatar_video**: Generates a new avatar video with the specified avatar, text, and voice.
- **get_avatar_video_status**: Retrieves the status of a video generated via the Heygen API.

### Programmatic Usage (Python Library)

You can also import the API client or even the MCP application instance:

```python
import asyncio
from heygen_mcp import HeygenAPIClient, mcp # Import client and MCP app

async def example_usage():
    api_key = "YOUR_API_KEY" # Load securely!
    client = HeygenAPIClient(api_key)

    try:
        # Get remaining credits
        credits = await client.get_remaining_credits()
        print(f"Remaining credits: {credits.remaining_credits}")

        # Get available voices
        voices = await client.get_voices()
        if voices.voices:
            print(f"First voice: {voices.voices[0].name}")

        # List avatar groups
        groups = await client.list_avatar_groups()
        if groups.avatar_groups:
            group_id = groups.avatar_groups[0].id
            print(f"First group: {groups.avatar_groups[0].name}")

            # Get avatars in the group
            avatars = await client.get_avatars_in_group(group_id)
            if avatars.avatars:
                print(f"First avatar: {avatars.avatars[0].avatar_name}")

    finally:
        await client.close()

# Run the example
# asyncio.run(example_usage())
```

## Development

- **Adding Tools:** Modify `server.py` to add or change MCP tools/resources.
- **API Client:** Update the `HeyGenApiClient` class for new API endpoints or model changes.
- **Dependencies:** Use `pip install -e ".[dev]"` to install for development.
- **Testing:** Run tests using `pytest`.
- **Linting/Formatting:** Use `ruff check .` and `ruff format .`.
