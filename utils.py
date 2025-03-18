import requests
from bs4 import BeautifulSoup
import pandas as pd
from transformers import pipeline
from sklearn.feature_extraction.text import CountVectorizer
from gtts import gTTS
import re
import time
import random
from typing import List, Dict, Any
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize sentiment analysis pipeline
sentiment_analyzer = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")

# Headers to mimic browser requests
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Cache-Control': 'max-age=0',
}

def search_news(company_name: str, num_articles: int = 15) -> List[str]:
    """
    Search for news articles about a company using Google News.
    Returns a list of URLs to scrape.
    
    Args:
        company_name: Name of the company to search for
        num_articles: Number of articles to try to find (will try to get more since some might fail)
    
    Returns:
        List of URLs to news articles
    """
    try:
        # Format company name for URL
        query = company_name.replace(' ', '+')
        # Google News search URL
        search_url = f"https://www.google.com/search?q={query}+news&tbm=nws"
        
        response = requests.get(search_url, headers=HEADERS)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all news article links
        article_links = []
        for g in soup.find_all('div', class_='SoaBEf'):
            links = g.find_all('a')
            if links:
                href = links[0].get('href')
                if href.startswith('/url?q='):
                    # Extract actual URL from Google's redirect URL
                    actual_url = href.replace('/url?q=', '').split('&sa=')[0]
                    article_links.append(actual_url)
                elif href.startswith('http'):
                    article_links.append(href)
        
        logger.info(f"Found {len(article_links)} potential news articles about {company_name}")
        return article_links[:num_articles]
    
    except Exception as e:
        logger.error(f"Error searching for news: {str(e)}")
        return []

def scrape_article(url: str) -> Dict[str, Any]:
    """
    Scrape a news article and extract relevant information.
    
    Args:
        url: URL of the article to scrape
        
    Returns:
        Dictionary containing article data or None if scraping failed
    """
    try:
        # Add random delay to avoid rate limiting
        time.sleep(random.uniform(1, 3))
        
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract title
        title = soup.find('title')
        title_text = title.text if title else "No title found"
        
        # Extract main content - this is a simplified approach and may need to be customized
        # based on the specific news sites you're targeting
        article_text = ""
        
        # Try to find article content with common class names
        article_tags = soup.find_all(['article', 'div'], class_=re.compile('(article|content|story|body)', re.I))
        if article_tags:
            for tag in article_tags:
                paragraphs = tag.find_all('p')
                if paragraphs:
                    for p in paragraphs:
                        article_text += p.text + " "
        
        # If no article content found, try to get all paragraphs
        if not article_text:
            paragraphs = soup.find_all('p')
            for p in paragraphs:
                article_text += p.text + " "
        
        # Clean up the text
        article_text = re.sub(r'\s+', ' ', article_text).strip()
        
        # Create summary (first 300 characters or first 3 sentences)
        sentences = re.split(r'[.!?]', article_text)
        summary = ' '.join(sentences[:3]).strip()
        if len(summary) > 300:
            summary = summary[:297] + '...'
        
        # Extract publication date (simplified)
        date = None
        date_tags = soup.find_all(['time', 'span', 'p', 'div'], class_=re.compile('(date|time|published)', re.I))
        if date_tags:
            date = date_tags[0].text.strip()
        
        # Return article data
        return {
            "url": url,
            "title": title_text,
            "content": article_text,
            "summary": summary,
            "date": date
        }
    
    except Exception as e:
        logger.error(f"Error scraping article {url}: {str(e)}")
        return None

def extract_news_articles(company_name: str, num_articles: int = 10) -> List[Dict[str, Any]]:
    """
    Extract news articles about a company.
    
    Args:
        company_name: Name of the company
        num_articles: Target number of articles to extract
        
    Returns:
        List of dictionaries containing article data
    """
    # Get more URLs than needed since some might fail to scrape
    article_urls = search_news(company_name, num_articles * 2)
    
    articles = []
    for url in article_urls:
        article_data = scrape_article(url)
        if article_data and len(article_data["content"]) > 100:  # Ensure meaningful content
            articles.append(article_data)
            logger.info(f"Successfully scraped article: {article_data['title']}")
        
        # Stop once we have enough articles
        if len(articles) >= num_articles:
            break
    
    logger.info(f"Successfully extracted {len(articles)} articles about {company_name}")
    return articles[:num_articles]  # Ensure we return at most num_articles

def analyze_sentiment(text: str) -> Dict[str, Any]:
    """
    Analyze the sentiment of a text.
    
    Args:
        text: Text to analyze
        
    Returns:
        Dictionary with sentiment data
    """
    try:
        # Truncate text to 512 tokens (model limit)
        truncated_text = text[:512]
        
        # Get sentiment from model
        result = sentiment_analyzer(truncated_text)[0]
        label = result['label']
        score = result['score']
        
        # Map to simple categories
        if label == "POSITIVE":
            sentiment = "Positive"
        elif label == "NEGATIVE":
            sentiment = "Negative"
        else:
            sentiment = "Neutral"
        
        return {
            "sentiment": sentiment,
            "confidence": score
        }
    
    except Exception as e:
        logger.error(f"Error analyzing sentiment: {str(e)}")
        return {"sentiment": "Neutral", "confidence": 0.5}  # Default fallback

def extract_topics(text: str, top_n: int = 3) -> List[str]:
    """
    Extract main topics from text using simple keyword extraction.
    
    Args:
        text: Text to analyze
        top_n: Number of topics to extract
        
    Returns:
        List of topic keywords
    """
    try:
        # Clean text
        clean_text = re.sub(r'[^\w\s]', '', text.lower())
        
        # Remove common stopwords (simplified)
        stopwords = ['the', 'and', 'a', 'to', 'in', 'of', 'is', 'it', 'that', 'for', 'on', 'with', 'as', 'was', 'by', 'at']
        word_tokens = clean_text.split()
        clean_tokens = [w for w in word_tokens if w not in stopwords and len(w) > 2]
        
        # Count word frequency
        vectorizer = CountVectorizer(max_features=top_n*2, ngram_range=(1, 2))
        X = vectorizer.fit_transform([' '.join(clean_tokens)])
        
        # Get top words/phrases
        top_words = vectorizer.get_feature_names_out()
        
        # Format for readability (capitalize first letter)
        topics = [' '.join(word.split('_')) for word in top_words[:top_n]]
        topics = [t.title() for t in topics]
        
        return topics
    
    except Exception as e:
        logger.error(f"Error extracting topics: {str(e)}")
        return ["General News"]  # Default fallback

def perform_comparative_analysis(articles: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Perform comparative analysis across multiple articles.
    
    Args:
        articles: List of article dictionaries with sentiment and topics
        
    Returns:
        Dictionary with comparative analysis results
    """
    try:
        # Count sentiment distribution
        sentiment_counts = {"Positive": 0, "Negative": 0, "Neutral": 0}
        for article in articles:
            # Use the Sentiment key instead of sentiment (case matters)
            sentiment_counts[article["Sentiment"]] += 1
        
        # Find all topics
        all_topics = []
        for article in articles:
            # Use the Topics key instead of topics (case matters)
            all_topics.extend(article["Topics"])
        
        # Count topic frequency
        topic_freq = pd.Series(all_topics).value_counts().to_dict()
        common_topics = [topic for topic, count in topic_freq.items() if count > 1]
        
        # Generate coverage differences
        coverage_differences = []
        
        # Compare sentiment variations
        if sentiment_counts["Positive"] > sentiment_counts["Negative"]:
            coverage_differences.append({
                "Comparison": f"{sentiment_counts['Positive']} articles have positive sentiment, while {sentiment_counts['Negative']} are negative.",
                "Impact": "The majority of coverage is positive, suggesting favorable public perception."
            })
        elif sentiment_counts["Negative"] > sentiment_counts["Positive"]:
            coverage_differences.append({
                "Comparison": f"{sentiment_counts['Negative']} articles have negative sentiment, while {sentiment_counts['Positive']} are positive.",
                "Impact": "The majority of coverage is negative, suggesting potential reputation issues."
            })
        else:
            coverage_differences.append({
                "Comparison": "Coverage is evenly split between positive and negative sentiment.",
                "Impact": "Mixed reception in the media with no clear sentiment trend."
            })
        
        # Compare topic focus
        if common_topics:
            coverage_differences.append({
                "Comparison": f"Common themes across articles include {', '.join(common_topics[:3])}.",
                "Impact": "These recurring themes represent the main public discussion points about the company."
            })
        
        # Determine overall sentiment
        dominant_sentiment = max(sentiment_counts, key=sentiment_counts.get)
        if dominant_sentiment == "Positive":
            final_sentiment = f"Coverage is predominantly positive ({sentiment_counts['Positive']}/{len(articles)} articles). Suggests favorable public perception."
        elif dominant_sentiment == "Negative":
            final_sentiment = f"Coverage is predominantly negative ({sentiment_counts['Negative']}/{len(articles)} articles). May indicate challenges or controversies."
        else:
            final_sentiment = f"Coverage is mostly neutral ({sentiment_counts['Neutral']}/{len(articles)} articles). Suggests factual reporting with limited emotional content."
        
        return {
            "Sentiment Distribution": sentiment_counts,
            "Coverage Differences": coverage_differences,
            "Common Topics": common_topics[:5] if common_topics else ["No common topics"],
            "Final Sentiment Analysis": final_sentiment
        }
    
    except Exception as e:
        logger.error(f"Error in comparative analysis: {str(e)}")
        return {
            "Sentiment Distribution": {"Positive": 0, "Negative": 0, "Neutral": 0},
            "Coverage Differences": [],
            "Common Topics": ["Analysis error"],
            "Final Sentiment Analysis": "Could not determine overall sentiment."
        }
    
def create_hindi_summary(company_name: str, analysis_results: Dict[str, Any]) -> str:
    """
    Create a Hindi summary of the analysis results.
    
    Args:
        company_name: Name of the company
        analysis_results: Results of the comparative analysis
        
    Returns:
        Hindi summary text
    """
    # This is a simple template for Hindi summary
    # For a production app, use a proper translation service or create better templates
    
    sentiment_dist = analysis_results["Sentiment Distribution"]
    final_sentiment = analysis_results["Final Sentiment Analysis"]
    
    # Basic Hindi summary template
    hindi_summary = f"""{company_name} के बारे में समाचार विश्लेषण।
हमने {sum(sentiment_dist.values())} समाचार लेख खोजे।
इनमें से, {sentiment_dist['Positive']} सकारात्मक, {sentiment_dist['Negative']} नकारात्मक, और {sentiment_dist['Neutral']} तटस्थ थे।
समग्र विश्लेषण: {final_sentiment}"""

    return hindi_summary

def text_to_hindi_speech(text: str) -> str:
    """
    Convert text to Hindi speech.
    
    Args:
        text: Text to convert to speech (in Hindi)
        
    Returns:
        Filename of the generated audio
    """
    try:
        # Generate a unique filename
        filename = f"hindi_speech_{int(time.time())}.mp3"
        
        # Create TTS output
        tts = gTTS(text=text, lang='hi', slow=False)
        tts.save(filename)
        
        logger.info(f"Generated Hindi TTS output: {filename}")
        return filename
    
    except Exception as e:
        logger.error(f"Error generating Hindi speech: {str(e)}")
        return ""

def process_company_news(company_name: str, num_articles: int = 10) -> Dict[str, Any]:
    """
    Process news for a company - main function that combines all steps.
    
    Args:
        company_name: Name of the company
        num_articles: Number of articles to process
        
    Returns:
        Dictionary with all analysis results
    """
    try:
        # Step 1: Extract news articles
        articles = extract_news_articles(company_name, num_articles)
        
        # Step 2: Process each article
        processed_articles = []
        for article in articles:
            # Analyze sentiment
            sentiment_result = analyze_sentiment(article["content"])
            
            # Extract topics
            topics = extract_topics(article["content"])
            
            # Create processed article
            processed_article = {
                "Title": article["title"],
                "Summary": article["summary"],
                "Sentiment": sentiment_result["sentiment"],
                "Topics": topics,
                "URL": article["url"]
            }
            processed_articles.append(processed_article)
        
        # Step 3: Perform comparative analysis
        comparative_analysis = perform_comparative_analysis(processed_articles)
        
        # Step 4: Create Hindi summary
        hindi_summary = create_hindi_summary(company_name, comparative_analysis)
        
        # Step 5: Generate Hindi TTS
        audio_file = text_to_hindi_speech(hindi_summary)
        
        # Combine all results
        result = {
            "Company": company_name,
            "Articles": processed_articles,
            "Comparative Sentiment Score": comparative_analysis,
            "Final Sentiment Analysis": comparative_analysis["Final Sentiment Analysis"],
            "Hindi Summary": hindi_summary,
            "Audio": audio_file
        }
        
        return result
    
    except Exception as e:
        logger.error(f"Error processing news for {company_name}: {str(e)}")
        return {
            "Company": company_name,
            "Articles": [],
            "Comparative Sentiment Score": {},
            "Final Sentiment Analysis": "Error processing news.",
            "Hindi Summary": "",
            "Audio": ""
        }
