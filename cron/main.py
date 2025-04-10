import os
import time
import schedule
import pytz
import json
import requests
from datetime import datetime
from openai import OpenAI
from elevenlabs import ElevenLabs
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

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
    created_at = Column(DateTime, default=datetime.utcnow)

def setup_database():
    engine = create_engine('sqlite:///data/news.db')
    Base.metadata.create_all(engine)
    return engine

def get_news():
    try:
        url = "https://newsapi.org/v2/top-headlines"
        headers = {"X-Api-Key": os.getenv('NEWS_API_KEY')}
        params = {
            "language": "en",
            "country": "us",
            "category": "general"
        }
        
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        data = response.json()
        return data.get('articles', [])[:3]  # Get top 3 articles
        
    except Exception as e:
        print(f"Error fetching news: {str(e)}")
        return []

def clean_json_response(response_text):
    """Clean the response text to handle both pure JSON and markdown-wrapped JSON."""
    # Remove markdown code block if present
    if response_text.startswith('```json'):
        response_text = response_text.replace('```json', '', 1)
    elif response_text.startswith('```'):
        response_text = response_text.replace('```', '', 1)
    
    if response_text.endswith('```'):
        response_text = response_text[:-3]
    
    # Clean up any leading/trailing whitespace
    response_text = response_text.strip()
    
    try:
        # Parse the cleaned JSON string
        return json.loads(response_text)
    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {str(e)}")
        print(f"Response text: {response_text}")
        raise

def generate_alien_news(original_title, original_content):
    client = OpenAI(
        api_key=os.getenv('OPENAI_API_KEY'),
        base_url="https://openrouter.ai/api/v1",
        default_headers={
            "HTTP-Referer": "https://space-english-app.com",
            "X-Title": "Space English Learning App",
            "Content-Type": "application/json"
        }
    )
    
    prompt = f"""
    You are writing for children aged 6-10 years old who are learning English. 
    Based on this Earth news:
    Title: {original_title}
    Content: {original_content}
    
    Create a fun, simple, and child-friendly alien version of this news that happened on planet Zorg. 
    Follow these guidelines:
    1. Use simple, clear sentences with basic vocabulary
    2. Keep sentences short (10-15 words maximum)
    3. Make it fun and playful
    4. Include some silly alien words (but not too many)
    5. Avoid any scary, violent, or complex topics
    6. If the original news is too complex or inappropriate for children, create a simple, fun alien story about a similar but child-friendly topic
    
    Also select 3 English vocabulary words that are:
    1. Appropriate for children aged 6-10
    2. Common words they might encounter in daily life or school
    3. Words that help build their basic English vocabulary
    4. Not too easy (like 'the', 'is', 'and') but also not too difficult
    
    For each vocabulary word:
    1. Provide a simple, child-friendly explanation
    2. Write a fun, easy-to-understand example sentence
    3. The sentence should clearly show the word's meaning
    
    Format the response as JSON:
    {{
        "alien_title": "title (keep it short and fun)",
        "alien_content": "content (2-3 simple sentences)",
        "vocab": [
            {{"word": "word1", "explanation": "simple explanation1", "sentence": "fun example sentence1"}},
            {{"word": "word2", "explanation": "simple explanation2", "sentence": "fun example sentence2"}},
            {{"word": "word3", "explanation": "simple explanation3", "sentence": "fun example sentence3"}}
        ]
    }}
    """
    
    try:
        response = client.chat.completions.create(
            model="deepseek/deepseek-r1:free",
            messages=[
                {
                    "role": "system", 
                    "content": "You are a friendly alien teacher who explains Earth news to young children (ages 6-10) in a fun, simple way. You always use age-appropriate language and make learning English fun!"
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        
        if not response.choices or not response.choices[0].message:
            raise ValueError("No response received from OpenRouter")
            
        content = response.choices[0].message.content
        print(f"Raw response content: {content}")
        return content
        
    except Exception as e:
        print(f"Error in generate_alien_news: {str(e)}")
        print(f"Full error details: {repr(e)}")
        raise

def generate_audio(text, filename):
    """Generate audio file using ElevenLabs API."""
    try:
        # Initialize ElevenLabs client
        client = ElevenLabs(
            api_key=os.getenv('ELEVENLABS_API_KEY')
        )
        
        # Create audio directory if it doesn't exist
        os.makedirs('data/audio', exist_ok=True)
        
        # Generate audio with a child-friendly voice
        audio_generator = client.text_to_speech.convert(
            text=text,
            voice_id="JBFqnCBsd6RMkjVDRZzb",  # Josh voice ID
            model_id="eleven_multilingual_v2",  # Latest multilingual model
            output_format="mp3_44100_128"  # High-quality audio
        )
        
        # Save the audio file
        file_path = f"data/audio/{filename}.mp3"
        
        # Convert generator to bytes and write to file
        audio_bytes = b''.join(chunk for chunk in audio_generator)
        with open(file_path, 'wb') as f:
            f.write(audio_bytes)
        
        print(f"Successfully generated audio with settings:")
        print(f"- Voice ID: JBFqnCBsd6RMkjVDRZzb (Josh)")
        print(f"- Model: eleven_multilingual_v2")
        print(f"- Output format: mp3_44100_128")
        print(f"- File path: {file_path}")
        
        return file_path
    except Exception as e:
        print(f"Error generating audio: {str(e)}")
        print(f"Error details: {repr(e)}")
        return None

def generate_audio_content(alien_title, alien_content, vocab_words):
    """Generate the text content for TTS in a child-friendly format."""
    content = f"""
    <break time="500ms"/>Hello Earth friends! <break time="300ms"/>
    Welcome to today's alien news from Planet Zorg!
    <break time="800ms"/>
    
    {alien_title}
    <break time="500ms"/>
    
    {alien_content}
    <break time="800ms"/>
    
    And now, let's learn some fun Earth words!
    <break time="500ms"/>
    
    Word number one: <break time="200ms"/>{vocab_words[0]['word']}
    This word means: <break time="200ms"/>{vocab_words[0]['explanation']}
    Here's how to use it: <break time="200ms"/>{vocab_words[0]['sentence']}
    <break time="500ms"/>
    
    Word number two: <break time="200ms"/>{vocab_words[1]['word']}
    This word means: <break time="200ms"/>{vocab_words[1]['explanation']}
    Here's how to use it: <break time="200ms"/>{vocab_words[1]['sentence']}
    <break time="500ms"/>
    
    Word number three: <break time="200ms"/>{vocab_words[2]['word']}
    This word means: <break time="200ms"/>{vocab_words[2]['explanation']}
    Here's how to use it: <break time="200ms"/>{vocab_words[2]['sentence']}
    <break time="800ms"/>
    
    That's all for today's alien news! <break time="300ms"/>Keep learning and having fun!
    <break time="500ms"/>Goodbye, Earth friends!
    """
    return content

def job():
    print(f"Starting news fetch at {datetime.now()}")
    engine = setup_database()
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        articles = get_news()
        
        for article in articles:
            alien_news = generate_alien_news(article['title'], article['description'])
            try:
                alien_data = clean_json_response(alien_news)
                
                print(f"Original Title: {article['title']}")
                print(f"Original Content: {article['description']}")
                print(f"Alien Title: {alien_data['alien_title']}")
                print(f"Alien Content: {alien_data['alien_content']}")
                for i, vocab in enumerate(alien_data['vocab'], 1):
                    print(f"Vocab {i}:")
                    print(f"  Word: {vocab['word']}")
                    print(f"  Explanation: {vocab['explanation']}")
                    print(f"  Sentence: {vocab['sentence']}")
                print('--------------------------------')
                
                # Generate audio content
                audio_text = generate_audio_content(
                    alien_data['alien_title'],
                    alien_data['alien_content'],
                    alien_data['vocab']
                )
                
                # Generate unique filename using timestamp
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                audio_filename = f"alien_news_{timestamp}"
                
                # Generate and save audio file
                audio_path = generate_audio(audio_text, audio_filename)
                
                news = News(
                    original_title=article['title'],
                    original_content=article['description'],
                    alien_title=alien_data['alien_title'],
                    alien_content=alien_data['alien_content'],
                    vocab_word1=alien_data['vocab'][0]['word'],
                    vocab_explanation1=alien_data['vocab'][0]['explanation'],
                    vocab_sentence1=alien_data['vocab'][0]['sentence'],
                    vocab_word2=alien_data['vocab'][1]['word'],
                    vocab_explanation2=alien_data['vocab'][1]['explanation'],
                    vocab_sentence2=alien_data['vocab'][1]['sentence'],
                    vocab_word3=alien_data['vocab'][2]['word'],
                    vocab_explanation3=alien_data['vocab'][2]['explanation'],
                    vocab_sentence3=alien_data['vocab'][2]['sentence'],
                    audio_path=audio_path
                )
                
                session.add(news)
                print(f"Generated audio file: {audio_path}")
                
            except Exception as e:
                print(f"Error processing article: {str(e)}")
                print(f"Raw response: {alien_news}")
                continue
        
        session.commit()
        print(f"Successfully processed {len(articles)} articles")
        
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        print(f"Error details: {repr(e)}")
        session.rollback()
    finally:
        session.close()

def main():
    # Schedule job to run at midnight HKT
    hkt = pytz.timezone('Asia/Hong_Kong')
    schedule.every().day.at("00:00").do(job)
    
    # Run job immediately on startup
    job()
    
    # Keep the script running
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    main() 