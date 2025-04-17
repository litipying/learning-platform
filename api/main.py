from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Text, DateTime

app = FastAPI(
    title="Space English API",
    description="API for the Space English learning app",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount the data directory for static file serving
app.mount("/data", StaticFiles(directory="/app/data"), name="data")

# Function to convert file path to URL
def get_file_url(file_path: Optional[str]) -> Optional[str]:
    if not file_path:
        return None
    # Replace the local path with the API endpoint path
    return f"http://localhost:8003/data/{'/'.join(file_path.split('/')[1:])}"

# Database models
Base = declarative_base()

class News(Base):
    __tablename__ = 'news'
    
    id = Column(Integer, primary_key=True)
    original_title = Column(String(500))
    original_content = Column(Text)
    alien_title = Column(String(500))
    alien_content = Column(Text)
    vocab_word1 = Column(String(100))
    vocab_explanation1 = Column(Text)
    vocab_sentence1 = Column(Text)
    vocab_word2 = Column(String(100))
    vocab_explanation2 = Column(Text)
    vocab_sentence2 = Column(Text)
    vocab_word3 = Column(String(100))
    vocab_explanation3 = Column(Text)
    vocab_sentence3 = Column(Text)
    audio_path = Column(String(500))  # Path to the audio file
    image_path = Column(String(500))  # Path to the image file
    video_path = Column(String(500))  # Path to the video file
    created_at = Column(DateTime, default=datetime.utcnow)

# Pydantic models for API
class VocabWord(BaseModel):
    word: str
    explanation: str
    sentence: Optional[str] = None  # Made optional with default None

class NewsResponse(BaseModel):
    id: int
    original_title: str
    original_content: str
    alien_title: str
    alien_content: str
    vocab_words: List[VocabWord]
    audio_path: Optional[str]
    image_path: Optional[str]
    video_path: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

# Database connection
engine = create_engine('sqlite:///data/news.db')
SessionLocal = sessionmaker(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/news/", response_model=List[NewsResponse], tags=["news"])
async def get_news(limit: Optional[int] = 20):
    """
    Get the latest alien news articles with vocabulary words, audio, images, and videos.
    
    - **limit**: Number of news articles to return (default: 20, max: 20)
    """
    # Ensure limit doesn't exceed 20
    limit = min(limit, 20) if limit else 20
    
    db = SessionLocal()
    try:
        news_items = db.query(News).order_by(desc(News.created_at)).limit(limit).all()
        
        return [
            NewsResponse(
                id=item.id,
                original_title=item.original_title,
                original_content=item.original_content,
                alien_title=item.alien_title,
                alien_content=item.alien_content,
                vocab_words=[
                    VocabWord(
                        word=item.vocab_word1,
                        explanation=item.vocab_explanation1
                    ),
                    VocabWord(
                        word=item.vocab_word2,
                        explanation=item.vocab_explanation2
                    ),
                    VocabWord(
                        word=item.vocab_word3,
                        explanation=item.vocab_explanation3
                    )
                ],
                audio_path=get_file_url(item.audio_path),
                image_path=get_file_url(item.image_path),
                video_path=get_file_url(item.video_path),
                created_at=item.created_at
            )
            for item in news_items
        ]
    finally:
        db.close()

@app.delete("/news/{news_id}", tags=["news"])
async def delete_news(news_id: int):
    """
    Delete a specific news article by its ID.
    
    - **news_id**: The ID of the news article to delete
    """
    db = SessionLocal()
    try:
        news_item = db.query(News).filter(News.id == news_id).first()
        if not news_item:
            raise HTTPException(status_code=404, detail="News article not found")
        
        db.delete(news_item)
        db.commit()
        return {"message": f"News article {news_id} deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting news article: {str(e)}")
    finally:
        db.close()

@app.get("/news/{news_id}", response_model=NewsResponse, tags=["news"])
async def get_news_by_id(news_id: int):
    """
    Get a specific news article by its ID.
    
    - **news_id**: The ID of the news article to retrieve
    """
    db = SessionLocal()
    try:
        news_item = db.query(News).filter(News.id == news_id).first()
        if not news_item:
            raise HTTPException(status_code=404, detail="News article not found")
            
        return NewsResponse(
            id=news_item.id,
            original_title=news_item.original_title,
            original_content=news_item.original_content,
            alien_title=news_item.alien_title,
            alien_content=news_item.alien_content,
            vocab_words=[
                VocabWord(
                    word=news_item.vocab_word1,
                    explanation=news_item.vocab_explanation1,
                    sentence=news_item.vocab_sentence1
                ),
                VocabWord(
                    word=news_item.vocab_word2,
                    explanation=news_item.vocab_explanation2,
                    sentence=news_item.vocab_sentence2
                ),
                VocabWord(
                    word=news_item.vocab_word3,
                    explanation=news_item.vocab_explanation3,
                    sentence=news_item.vocab_sentence3
                )
            ],
            audio_path=get_file_url(news_item.audio_path),
            image_path=get_file_url(news_item.image_path),
            video_path=get_file_url(news_item.video_path),
            created_at=news_item.created_at
        )
    finally:
        db.close() 