# Web Browsing Agent

This project is a multi-agent browser automation tool using CrewAI and Stagehand.

## Installation

1. **Clone the repository**  
   ```bash
   git clone https://github.com/tamaghna-OGGOD/web_browsing_agent.git
   cd web_browsing_agent/browser-automation
   ```

2. **Create a virtual environment (recommended)**  
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies**  
   If you are using [uv](https://github.com/astral-sh/uv):
   ```bash
   uv pip install -e .
   ```
   Or, with pip:
   ```bash
   pip install -e .
   ```

## Running the Application

To run the application, start the Streamlit app with the following command:
`streamlit run .\src\agent.py`