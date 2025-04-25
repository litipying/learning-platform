import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

# Ensure data directory exists
data_dir = "/app/data"
os.makedirs(data_dir, exist_ok=True)

# Mount the data directory for static file serving
app.mount("/data", StaticFiles(directory=data_dir), name="data")

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

class Story(Base):
    __tablename__ = 'stories'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(500))
    story_text = Column(Text)
    character_name = Column(String(100))
    character_image_path = Column(String(500))
    story_path = Column(String(500))
    voice_id = Column(String(100), nullable=True)
    moral = Column(Text, nullable=True)
    timestamp = Column(String(50))
    date = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship with scenes
    scenes = relationship("Scene", back_populates="story", cascade="all, delete-orphan")

class Scene(Base):
    __tablename__ = 'scenes'
    
    id = Column(Integer, primary_key=True)
    story_id = Column(Integer, ForeignKey('stories.id'))
    scene_number = Column(Integer)
    description = Column(Text)
    scene_story = Column(Text, nullable=True)
    image_path = Column(String(500))
    audio_path = Column(String(500), nullable=True)
    
    # Relationship with story
    story = relationship("Story", back_populates="scenes")

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

class SceneResponse(BaseModel):
    id: int
    scene_number: int
    description: str
    scene_story: Optional[str]
    image_path: Optional[str]
    audio_path: Optional[str]
    
    class Config:
        from_attributes = True

class StoryCharacter(BaseModel):
    id: int
    title: str
    story_text: str
    character_name: str
    character_image_path: str
    moral: Optional[str]
    voice_id: Optional[str]
    
    class Config:
        from_attributes = True

class StoryDateResponse(BaseModel):
    date: str
    stories: List[StoryCharacter]
    scenes: List[SceneResponse]
    
    class Config:
        from_attributes = True

# Function to ensure database directories exist
def ensure_db_path(db_path):
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        logger.info(f"Creating database directory: {db_dir}")
        # os.makedirs(db_dir, exist_ok=True)
    return db_path

# Database connection for News
news_db_path = ensure_db_path("/app/data/news.db")
news_engine = create_engine(f'sqlite:///{news_db_path}')
Base.metadata.create_all(news_engine)  # Create news tables if they don't exist
NewsSessionLocal = sessionmaker(bind=news_engine)

# Separate database connection for Story/Scene
story_db_path = ensure_db_path("/app/data/story.db")
logger.info(f"Story database path: {story_db_path}")
story_engine = create_engine(f'sqlite:///{story_db_path}')
Base.metadata.create_all(story_engine)  # Create story tables if they don't exist
StorySessionLocal = sessionmaker(bind=story_engine)

def get_db():
    db = NewsSessionLocal()
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
    
    db = NewsSessionLocal()
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
    db = NewsSessionLocal()
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
    db = NewsSessionLocal()
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

@app.get("/story/dates", response_model=List[str], tags=["story"])
async def get_story_dates():
    """
    Get all available dates for stories.
    """
    try:
        db = StorySessionLocal()
        try:
            dates = db.query(Story.date).distinct().order_by(desc(Story.date)).all()
            return [date[0] for date in dates]
        except Exception as e:
            logger.error(f"Error retrieving story dates: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error retrieving story dates: {str(e)}")
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database connection error: {str(e)}")

@app.get("/story/scenes/date/{date}", response_model=StoryDateResponse, tags=["story"])
async def get_scenes_by_date(date: str, latest_only: bool = False):
    """
    Get all scenes from stories for a specific date.
    
    - **date**: The date in format YYYYMMDD
    - **latest_only**: If true, only return the latest story for the date
    """
    try:
        db = StorySessionLocal()
        try:
            # Query to find stories for the given date
            query = db.query(Story).filter(Story.date == date).order_by(desc(Story.timestamp))
            
            if latest_only:
                stories = query.limit(1).all()
            else:
                stories = query.all()
                
            if not stories:
                logger.warning(f"No stories found for date {date}")
                raise HTTPException(status_code=404, detail=f"No stories found for date {date}")
            
            # Get all story IDs
            story_ids = [story.id for story in stories]
            
            # Query to find all scenes for these stories
            scenes = db.query(Scene).filter(Scene.story_id.in_(story_ids)).all()
            
            # Create response
            story_characters = [
                StoryCharacter(
                    id=story.id,
                    title=story.title,
                    story_text=story.story_text,
                    character_name=story.character_name,
                    character_image_path=get_file_url(story.character_image_path),
                    moral=story.moral,
                    voice_id=story.voice_id
                ) for story in stories
            ]
            
            scene_responses = [
                SceneResponse(
                    id=scene.id,
                    scene_number=scene.scene_number,
                    description=scene.description,
                    scene_story=scene.scene_story,
                    image_path=get_file_url(scene.image_path),
                    audio_path=get_file_url(scene.audio_path)
                ) for scene in scenes
            ]
            
            return StoryDateResponse(
                date=date,
                stories=story_characters,
                scenes=scene_responses
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error retrieving scenes: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error retrieving scenes: {str(e)}")
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database connection error: {str(e)}") 