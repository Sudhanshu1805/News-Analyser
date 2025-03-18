# Company News Analyzer with Hindi TTS

This web application extracts news articles about a specified company, performs sentiment analysis, conducts a comparative analysis across multiple articles, and generates a Hindi text-to-speech summary. The application is built using FastAPI for the backend API and Streamlit for the frontend interface.

## Features

- **News Extraction:** Scrapes news articles related to a specified company using BeautifulSoup
- **Sentiment Analysis:** Analyzes sentiment (positive, negative, neutral) of each article
- **Topic Extraction:** Identifies key topics in each article
- **Comparative Analysis:** Compares sentiment and coverage across multiple articles
- **Hindi Text-to-Speech:** Generates a Hindi audio summary of the analysis
- **Web Interface:** User-friendly Streamlit interface with visualizations
- **API Backend:** FastAPI backend for processing and data retrieval

## Architecture

The application follows a client-server architecture:

1. **Frontend (Streamlit):**
   - User interface for input and result visualization
   - Communicates with the backend API

2. **Backend (FastAPI):**
   - RESTful API for processing requests
   - Background task processing for long-running operations
   - Article scraping and analysis
   - Text-to-speech generation

3. **Components:**
   - `app.py`: Streamlit web application
   - `api.py`: FastAPI backend API
   - `utils.py`: Core functionality (scraping, analysis, TTS)

## Setup and Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Installation Steps

1. Clone the repository:
   ```
   git clone https://github.com/your-username/company-news-analyzer.git
   cd company-news-analyzer
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Run the application:

   Start the backend API:
   ```
   uvicorn api:app --reload
   ```

   In a separate terminal, start the Streamlit frontend:
   ```
   streamlit run app.py
   ```

5. Access the application:
   - Frontend: http://localhost:8501
   - API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

## Usage

1. Enter a company name in the text input or select a previously analyzed company
2. Adjust the number of articles to analyze using the slider (5-15)
3. Click "Analyze News" to start the analysis
4. Wait for the analysis to complete (progress bar will show status)
5. View results in the different tabs:
   - **Summary:** Overall sentiment analysis and common topics
   - **Articles:** Detailed information for each article
   - **Comparative Analysis:** Sentiment distribution and coverage differences
   - **Hindi Summary:** Text and audio summary in Hindi

## API Endpoints

The application provides the following API endpoints:

- `POST /analyze`: Start analysis for a company
- `GET /results/{company_name}`: Get analysis results for a company
- `GET /audio/{company_name}`: Get Hindi TTS audio for a company
- `GET /companies`: Get list of companies that have been analyzed

## Models and Techniques

1. **News Extraction:**
   - BeautifulSoup for HTML parsing
   - Regex for content extraction

2. **Sentiment Analysis:**
   - Hugging Face Transformers (DistilBERT) for sentiment classification

3. **Topic Extraction:**
   - CountVectorizer for keyword extraction
   - Basic stopword removal

4. **Text-to-Speech:**
   - gTTS (Google Text-to-Speech) for Hindi audio generation

## Deployment

The application can be deployed to Hugging Face Spaces:

1. Create a new Space on Hugging Face
2. Set up the repository with the required files
3. Configure the `api.py` file to use the correct URL for the deployed application
4. Update the `API_URL` in `app.py` to point to the deployed API

## Limitations and Assumptions

- The application only scrapes non-JavaScript websites
- News sources may have rate limits or anti-scraping measures
- Sentiment analysis is performed using a pre-trained model and may not be perfectly accurate
- Topic extraction is basic and could be improved with more sophisticated NLP techniques
- The Hindi summary is generated using a template and could be improved with proper translation

## Future Improvements

- Add more sophisticated NLP models for better sentiment analysis
- Implement proper translation for Hindi summaries
- Add more visualization options for comparative analysis
- Implement caching for faster results retrieval
- Add user authentication for personalized analysis

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
