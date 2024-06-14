# Buho Backend
Backend for investment banking assistant.

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
    poetry run python app/main.py
    ```

Now you can run the project using Poetry and your OpenAI secret key.