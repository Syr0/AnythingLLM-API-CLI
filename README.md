# AnythingLLM File Management CLI

A command-line tool for managing workspaces and documents with the AnythingLLM API. This tool enables uploading, embedding, and listing documents.

## Prerequisites

- **Python**: Version 3.7+
- **Dependencies**: Install packages listed in `requirements.txt`:
  ```bash
  pip install -r requirements.txt
  ```

## Usage

### Commands

- **List Workspaces:**
  ```bash
  python main.py -l
  ```

- **Upload Files:**
  ```bash
  python main.py -u "<path/to/directory>"
  ```

- **Embed Files into a Workspace (using regex pattern):**
  ```bash
  python main.py -e <regex> -w <workspace-name>
  ```

- **Upload and Embed (combined command):**
  ```bash
  python main.py -u "<path/to/directory>" -e <regex> -w <workspace-name>
  ```

### Configuration

Update the API key and base URL at the beginning of `main.py`:

```python
ANYTHING_LLM_API_KEY = 'Your_API_Key'
ANYTHING_LLM_BASE_URL = 'http://your-api-url'
```

Replace `'Your_API_Key'` with your actual API key and `'http://your-api-url'` with the base URL of your AnythingLLM instance.
