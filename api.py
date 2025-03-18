from fastapi import FastAPI, Query, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os
import logging
from utils import process_company_news

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="News Analyzer API",
    description="API for company news analysis and sentiment reporting with Hindi TTS",
    version="1.0.0"
)

# Cache to store results (simple in-memory cache)
results_cache = {}

class CompanyRequest(BaseModel):
    company_name: str
    num_articles: Optional[int] = 10

class ArticleResponse(BaseModel):
    Title: str
    Summary: str
    Sentiment: str
    Topics: List[str]
    URL: str

class CompanyAnalysisResponse(BaseModel):
    Company: str
    Articles: List[ArticleResponse]
    Comparative_Sentiment_Score: Dict[str, Any]
    Final_Sentiment_Analysis: str
    Audio: str

@app.get("/")
async def root():
    """Root endpoint to check if API is running"""
    return {"message": "News Analyzer API is running"}

@app.post("/analyze", response_model=Dict[str, Any])
async def analyze_company(request: CompanyRequest, background_tasks: BackgroundTasks):
    """
    Analyze news for a specific company.
    Returns basic response immediately and processes full analysis in background.
    """
    company_name = request.company_name
    num_articles = request.num_articles
    
    # Check cache
    cache_key = f"{company_name}_{num_articles}"
    if cache_key in results_cache:
        logger.info(f"Returning cached results for {company_name}")
        return results_cache[cache_key]
    
    # Return immediate response and process in background
    response = {
        "status": "processing",
        "message": f"Analysis for {company_name} started. Check /results/{company_name} for results.",
        "company": company_name
    }
    
    # Add task to background
    background_tasks.add_task(process_and_cache_results, company_name, num_articles)
    
    return response

@app.get("/results/{company_name}")
async def get_results(company_name: str):
    """
    Get the analysis results for a specific company.
    """
    # Check if results exist for any cache key with this company name
    for key in results_cache:
        if key.startswith(company_name + "_"):
            return results_cache[key]
    
    # If no results found
    raise HTTPException(status_code=404, detail=f"No results found for {company_name}. Analysis may still be processing.")

@app.get("/audio/{company_name}")
async def get_audio(company_name: str):
    """
    Get the Hindi TTS audio file for a company analysis.
    """
    # Find the cache key for this company
    audio_file = None
    for key in results_cache:
        if key.startswith(company_name + "_"):
            if "Audio" in results_cache[key] and results_cache[key]["Audio"]:
                audio_file = results_cache[key]["Audio"]
                break
    
    if not audio_file or not os.path.exists(audio_file):
        raise HTTPException(status_code=404, detail=f"No audio file found for {company_name}")
    
    return FileResponse(
        path=audio_file, 
        media_type="audio/mpeg", 
        filename=f"{company_name}_analysis.mp3"
    )

@app.get("/companies")
async def get_companies():
    """
    Get list of companies that have been analyzed.
    """
    companies = set()
    for key in results_cache:
        company_name = key.split("_")[0]
        companies.add(company_name)
    
    return {"companies": list(companies)}

def process_and_cache_results(company_name: str, num_articles: int):
    """
    Process company news and cache results.
    """
    try:
        logger.info(f"Starting background processing for {company_name}")
        
        # Process company news
        result = process_company_news(company_name, num_articles)
        
        # Cache results
        cache_key = f"{company_name}_{num_articles}"
        results_cache[cache_key] = result
        
        logger.info(f"Completed processing for {company_name}")
    
    except Exception as e:
        logger.error(f"Error in background processing for {company_name}: {str(e)}")
        # Cache error result
        results_cache[f"{company_name}_{num_articles}"] = {
            "status": "error",
            "message": f"Error processing analysis for {company_name}: {str(e)}",
            "company": company_name
        }
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)