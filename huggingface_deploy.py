import os
import subprocess
import json
import argparse
import shutil
import sys

def deploy_to_huggingface(hf_token, space_name):
    """
    Deploy the application to Hugging Face Spaces.
    
    Args:
        hf_token (str): Hugging Face API token
        space_name (str): Name of the Hugging Face Space
    """
    # Check if git is installed
    try:
        subprocess.check_call(["git", "--version"], stdout=subprocess.DEVNULL)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Error: Git is not installed or not in PATH. Please install Git first.")
        return False
    
    # Check if huggingface_hub is installed
    try:
        import huggingface_hub
    except ImportError:
        print("Installing huggingface_hub...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "huggingface_hub"])
    
    # Create Hugging Face Space configuration
    space_config = {
        "title": "Company News Analyzer",
        "colorFrom": "blue",
        "colorTo": "green",
        "sdk": "streamlit",
        "sdk_version": "1.26.0",
        "app_file": "app.py",
        "pinned": False
    }
    
    # Create README.md for Hugging Face Space
    hf_readme = """# Company News Analyzer with Hindi TTS

This application extracts news articles about a specified company, performs sentiment analysis, conducts a comparative analysis, and generates a Hindi text-to-speech summary.

## Features
- News extraction from multiple sources
- Sentiment analysis
- Topic extraction
- Comparative analysis
- Hindi text-to-speech output

## Usage
1. Enter a company name
2. Adjust the number of articles to analyze
3. Click "Analyze News"
4. View results in the tabs

## API
The application provides a REST API for programmatic access. API documentation is available at `/docs`.

## Technology Stack
- FastAPI
- Streamlit
- Hugging Face Transformers
- gTTS (Google Text-to-Speech)
- BeautifulSoup
"""
    
    # Create directory for Hugging Face Space
    os.makedirs("hf_space", exist_ok=True)
    
    # Copy files to Hugging Face Space directory
    files_to_copy = [
        "api.py",
        "app.py",
        "utils.py",
        "requirements.txt",
        "Dockerfile"
    ]
    
    for file in files_to_copy:
        if os.path.exists(file):
            shutil.copy(file, "hf_space/")
    
    # Write README.md
    with open("hf_space/README.md", "w") as f:
        f.write(hf_readme)
    
    # Write .gitattributes
    with open("hf_space/.gitattributes", "w") as f:
        f.write("* filter=lfs diff=lfs merge=lfs -text\n")
    
    # Write space.json config
    with open("hf_space/space.json", "w") as f:
        json.dump(space_config, f, indent=2)
    
    # Modify app.py API URL for Hugging Face
    with open("hf_space/app.py", "r") as f:
        app_content = f.read()
    
    app_content = app_content.replace(
        "API_URL = \"http://localhost:8000\"  # Local development",
        f"API_URL = \"https://{space_name}.hf.space\"  # Hugging Face Spaces"
    )
    
    with open("hf_space/app.py", "w") as f:
        f.write(app_content)
    
    # Initialize git repo
    os.chdir("hf_space")
    subprocess.check_call(["git", "init"])
    subprocess.check_call(["git", "add", "."])
    subprocess.check_call(["git", "commit", "-m", "Initial commit"])
    
    # Create Hugging Face Space
    subprocess.check_call([
        "huggingface-cli", "repo", "create", 
        space_name, "--type", "space", "--token", hf_token
    ])
    
    # Push to Hugging Face
    subprocess.check_call([
        "git", "remote", "add", "origin",
        f"https://huggingface.co/spaces/{space_name}"
    ])
    subprocess.check_call(["git", "push", "-u", "origin", "main"])
    
    print(f"✅ Successfully deployed to Hugging Face Spaces: https://huggingface.co/spaces/{space_name}")
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Deploy to Hugging Face Spaces")
    parser.add_argument("--token", required=True, help="Hugging Face API token")
    parser.add_argument("--space", required=True, help="Name of the Hugging Face Space (format: username/space-name)")
    
    args = parser.parse_args()
    deploy_to_huggingface(args.token, args.space)
