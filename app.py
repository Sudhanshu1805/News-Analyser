import streamlit as st
import requests
import pandas as pd
import time
import json
import os
import base64
from typing import Dict, Any, List
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# API URL (change this when deploying)
API_URL = "http://localhost:8000"  # Local development
# API_URL = "https://your-app-name.hf.space" # Hugging Face Spaces

def get_companies() -> List[str]:
    """Get list of analyzed companies from API"""
    try:
        response = requests.get(f"{API_URL}/companies")
        if response.status_code == 200:
            return response.json().get("companies", [])
        return []
    except Exception as e:
        logger.error(f"Error fetching companies: {str(e)}")
        return []

def submit_analysis_request(company_name: str, num_articles: int) -> Dict[str, Any]:
    """Submit analysis request to API"""
    try:
        response = requests.post(
            f"{API_URL}/analyze",
            json={"company_name": company_name, "num_articles": num_articles}
        )
        return response.json()
    except Exception as e:
        logger.error(f"Error submitting analysis: {str(e)}")
        return {"status": "error", "message": f"API error: {str(e)}"}

def get_analysis_results(company_name: str) -> Dict[str, Any]:
    """Get analysis results from API"""
    try:
        response = requests.get(f"{API_URL}/results/{company_name}")
        if response.status_code == 200:
            return response.json()
        return {"status": "error", "message": f"Error: {response.status_code}"}
    except Exception as e:
        logger.error(f"Error fetching results: {str(e)}")
        return {"status": "error", "message": f"API error: {str(e)}"}

def get_audio_url(company_name: str) -> str:
    """Get URL for audio file"""
    return f"{API_URL}/audio/{company_name}"

def autoplay_audio(file_url: str) -> str:
    """Generate HTML for audio autoplay"""
    audio_html = f"""
        <audio controls autoplay>
            <source src="{file_url}" type="audio/mpeg">
            Your browser does not support the audio element.
        </audio>
    """
    return audio_html

def create_sentiment_chart(sentiment_dist: Dict[str, int]) -> None:
    """Create sentiment distribution chart"""
    df = pd.DataFrame({
        'Sentiment': list(sentiment_dist.keys()),
        'Count': list(sentiment_dist.values())
    })
    
    st.bar_chart(df.set_index('Sentiment'))

def main():
    st.set_page_config(
        page_title="Company News Analyzer",
        page_icon="📊",
        layout="wide"
    )
    
    st.title("📰 Company News Analyzer with Sentiment Analysis")
    st.write("Enter a company name to analyze recent news articles and get sentiment analysis with Hindi TTS summary.")
    
    # Sidebar for options
    st.sidebar.title("⚙️ Options")
    
    # Get list of analyzed companies
    analyzed_companies = get_companies()
    
    # Company input - allow selection from analyzed companies or input new
    company_input_method = st.sidebar.radio(
        "Company Selection Method",
        ["Enter new company", "Select previously analyzed company"],
        index=1 if analyzed_companies else 0
    )
    
    if company_input_method == "Select previously analyzed company" and analyzed_companies:
        company_name = st.sidebar.selectbox("Select Company", analyzed_companies)
        st.sidebar.write(f"Selected: {company_name}")
        show_results = st.sidebar.button("Show Analysis")
        
        if show_results:
            with st.spinner(f"Loading analysis for {company_name}..."):
                results = get_analysis_results(company_name)
                display_results(company_name, results)
    
    else:
        company_name = st.text_input("Enter Company Name", "Tesla")
        num_articles = st.sidebar.slider("Number of Articles", 5, 15, 10)
        
        col1, col2 = st.columns([1, 3])
        with col1:
            analyze_button = st.button("Analyze News")
        
        if analyze_button and company_name:
            with st.spinner(f"Starting analysis for {company_name}..."):
                # Submit analysis request
                response = submit_analysis_request(company_name, num_articles)
                
                if response.get("status") == "processing":
                    st.success(f"Analysis for {company_name} started! Results will appear shortly...")
                    
                    # Set up progress bar
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    # Poll for results
                    for i in range(1, 101):
                        # Update progress bar
                        progress_bar.progress(i)
                        
                        # Check if results are ready
                        if i % 10 == 0:  # Check every 10%
                            status_text.text(f"Processing... ({i}%)")
                            results = get_analysis_results(company_name)
                            
                            if "Articles" in results and results["Articles"]:
                                progress_bar.progress(100)
                                status_text.text("Analysis complete!")
                                display_results(company_name, results)
                                break
                        
                        # Wait before next update
                        time.sleep(0.5)
                    
                    # Final check if loop completed
                    if i >= 100:
                        results = get_analysis_results(company_name)
                        if "Articles" in results and results["Articles"]:
                            display_results(company_name, results)
                        else:
                            st.warning("Analysis is taking longer than expected. Please check back later or try again.")
                
                else:
                    st.error(f"Error: {response.get('message', 'Unknown error')}")
    
    # Footer
    st.sidebar.markdown("---")
    st.sidebar.info(
        "This application extracts news articles, performs sentiment analysis, "
        "and generates a Hindi text-to-speech summary for company news analysis."
    )

def display_results(company_name: str, results: Dict[str, Any]) -> None:
    """Display analysis results"""
    if "status" in results and results["status"] == "error":
        st.error(f"Error: {results.get('message', 'Unknown error')}")
        return
    
    if "Articles" not in results or not results["Articles"]:
        st.warning(f"No articles found for {company_name} or analysis still processing.")
        return
    
    # Display company header
    st.header(f"📊 Analysis Results for {company_name}")
    
    # Create tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs(["Summary", "Articles", "Comparative Analysis", "Hindi Summary"])
    
    with tab1:
        st.subheader("Overall Sentiment Analysis")
        
        # Show final sentiment analysis
        if "Final Sentiment Analysis" in results:
            st.info(results["Final Sentiment Analysis"])
        
        # Show sentiment distribution chart
        if "Comparative Sentiment Score" in results and "Sentiment Distribution" in results["Comparative Sentiment Score"]:
            sentiment_dist = results["Comparative Sentiment Score"]["Sentiment Distribution"]
            create_sentiment_chart(sentiment_dist)
        
        # Show common topics
        if "Comparative Sentiment Score" in results and "Common Topics" in results["Comparative Sentiment Score"]:
            common_topics = results["Comparative Sentiment Score"]["Common Topics"]
            st.subheader("Common Topics")
            for topic in common_topics:
                st.markdown(f"- {topic}")
    
    with tab2:
        st.subheader("Articles Analyzed")
        
        # Display each article
        for i, article in enumerate(results["Articles"]):
            with st.expander(f"{i+1}. {article['Title']}"):
                # Color-code sentiment
                sentiment_color = {
                    "Positive": "green",
                    "Negative": "red",
                    "Neutral": "gray"
                }.get(article["Sentiment"], "black")
                
                st.markdown(f"**Sentiment:** <span style='color:{sentiment_color}'>{article['Sentiment']}</span>", unsafe_allow_html=True)
                st.markdown(f"**Summary:** {article['Summary']}")
                
                # Display topics as tags
                st.markdown("**Topics:**")
                topic_html = " ".join([f"<span style='background-color:#f0f2f6;padding:2px 8px;margin:0 4px;border-radius:10px;font-size:0.8em'>{topic}</span>" for topic in article["Topics"]])
                st.markdown(topic_html, unsafe_allow_html=True)
                
                if "URL" in article:
                    st.markdown(f"[Read full article]({article['URL']})")
    
    with tab3:
        st.subheader("Comparative Analysis")
        
        if "Comparative Sentiment Score" in results:
            comp_analysis = results["Comparative Sentiment Score"]
            
            # Display coverage differences
            if "Coverage Differences" in comp_analysis:
                st.markdown("### Key Differences in Coverage")
                for i, diff in enumerate(comp_analysis["Coverage Differences"]):
                    with st.expander(f"Insight {i+1}: {diff.get('Comparison', '')[:50]}..."):
                        st.markdown(f"**Comparison:** {diff.get('Comparison', '')}")
                        st.markdown(f"**Impact:** {diff.get('Impact', '')}")
            
            # Display sentiment distribution
            if "Sentiment Distribution" in comp_analysis:
                st.markdown("### Sentiment Distribution")
                sentiment_dist = comp_analysis["Sentiment Distribution"]
                
                # Show as chart
                create_sentiment_chart(sentiment_dist)
                
                # Show as text
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Positive", sentiment_dist.get("Positive", 0))
                with col2:
                    st.metric("Neutral", sentiment_dist.get("Neutral", 0))
                with col3:
                    st.metric("Negative", sentiment_dist.get("Negative", 0))
            
            # Display common topics
            if "Common Topics" in comp_analysis:
                st.markdown("### Common Topics Across Articles")
                common_topics = comp_analysis["Common Topics"]
                
                # Display as tags
                topic_html = " ".join([f"<span style='background-color:#f0f2f6;padding:4px 10px;margin:0 6px;border-radius:10px'>{topic}</span>" for topic in common_topics])
                st.markdown(topic_html, unsafe_allow_html=True)
    
    with tab4:
        st.subheader("Hindi Summary and Audio")
        
        # Display Hindi summary
        if "Hindi Summary" in results:
            st.markdown("### Hindi Text Summary")
            st.text(results["Hindi Summary"])
        
        # Display audio player
        if "Audio" in results and results["Audio"]:
            st.markdown("### Hindi Audio Summary")
            audio_url = get_audio_url(company_name)
            st.markdown(autoplay_audio(audio_url), unsafe_allow_html=True)
            st.markdown(f"[Download Audio]({audio_url})")

if __name__ == "__main__":
    main()
