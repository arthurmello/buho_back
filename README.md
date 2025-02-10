# Buho Backend
Backend for investment banking assistant.

## Features

### Document Processing
- Supports multiple file formats including PDF, DOCX, TXT, XLSX, XLS, PPTX, and PPT
- Automatic document summarization and analysis
- Vector database storage for efficient document retrieval
- Cost-effective embedding processing with token usage tracking

### AI-Powered Analysis
- Intelligent question-answering system based on uploaded documents
- Context-aware responses using OpenAI's GPT models
- Hybrid search capabilities for accurate information retrieval
- Automated financial data extraction and analysis

### Document Generation
- Automated generation of investment banking documents:
  - Information Memorandums
  - Marketing Strips (PowerPoint presentations)
  - Discounted Cash Flow Analysis (Excel)
- Customizable templates and parameters
- Multi-format output support (DOCX, PPTX, XLSX)

### Deal Management
- Multi-user support with deal-specific workspaces
- File organization and management system
- Chat history tracking per deal
- Dashboard with key deal metrics and insights

## Getting Started
To set up the project, follow these steps:

1. Create a virtual environment using Poetry:

    ```shell
    poetry env use python3.9
    ```

2. Install the project dependencies:

    ```shell
    poetry install
    ```

3. Set your OpenAI secret key in the `.env` file. Make sure to replace `YOUR_SECRET_KEY` with your actual secret key:

    ```shell
    echo 'OPENAI_SECRET_KEY=YOUR_SECRET_KEY' >> .env
    ```

4. Activate the environment and run the main script:

    ```shell
    poetry run python -m buho_back.main
    ```

## API Endpoints

The service exposes several REST endpoints:

- `/input_files`: File upload and management
- `/output_files`: Document generation
- `/chat`: Q&A interface with uploaded documents
- `/deals`: Deal management
- `/dashboard_data`: Deal metrics and analytics
- `/qa_tracker`: Question and answer tracking

## Deployment

The application is containerized using Docker and can be deployed to Google Cloud Run. The deployment configuration includes:

- 4GB memory allocation
- 8 CPU cores
- 600-second timeout
- Automatic secret management for API keys

## Requirements

- Python 3.12.5
- Poetry for dependency management
- OpenAI API key
- LibreOffice for document processing