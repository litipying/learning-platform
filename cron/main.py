# Standard library imports
import os
import time
import json
import random
import http.client
import base64
import glob
try:
    import yaml
except ImportError:
    import pyyaml as yaml
from codecs import encode
from datetime import datetime
from typing import Optional, Dict, List, Any
from io import BytesIO

# Third-party imports
import pytz
import schedule
import requests
from openai import OpenAI
from elevenlabs import ElevenLabs
import PIL.Image
from google import genai
from google.genai import types

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Local imports
from did_service import DIDService
from runninghub_service import RunningHubService

# API configurations
HEDRA_API_URL = "https://app.v1.hedra.com/api/v1"
HEDRA_API_KEY = os.getenv('HEDRA_API_KEY')

RUNNINGHUB_API_URL = "https://www.runninghub.ai"
RUNNINGHUB_API_KEY = os.getenv('RUNNINGHUB_API_KEY')

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

def setup_database():
    engine = create_engine('sqlite:///data/news.db')
    Base.metadata.create_all(engine)
    return engine

def get_news(num_articles=3):
    """
    Fetch news articles from the News API.
    
    Args:
        num_articles (int): Number of articles to return (default: 3)
        
    Returns:
        list: List of news articles, each containing title and description
    """
    try:
        url = "https://newsapi.org/v2/top-headlines"
        headers = {"X-Api-Key": os.getenv('NEWS_API_KEY')}
        params = {
            "language": "en",
            "country": "us",
            "category": "general",
            "pageSize": min(num_articles, 100)  # News API limits to 100 articles max
        }

        print(f"Fetching news with params: {params}")
        
        response = requests.get(url, headers=headers, params=params)
        print(f"Fetching news response: {response.json()}")
        response.raise_for_status()  # Raise an exception for bad status codes
        
        data = response.json()
        articles = data.get('articles', [])
        return articles[:num_articles]  # Return only the requested number of articles
        
    except Exception as e:
        print(f"Error fetching news: {str(e)}")
        return []

def clean_json_response(response_text):
    print(f"Response text 1: {response_text}")
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
        print(f"Response text 2: {response_text}")
        raise

def generate_alien_news(original_title, original_content):
    
    prompt = f"""
    You are writing a 30-SECOND audio script for children aged 6-10 years old who are learning English. 
    Based on this Earth news:
    Title: {original_title}
    Content: {original_content}
    
    First, create a unique alien character name that's fun and easy for children to pronounce.
    Then determine the emotional tone of the story (choose one: happy, excited, surprised, curious, proud, thoughtful).
    Finally, create an extremely concise, child-friendly alien version that happened on planet Zorg.
    IMPORTANT: The entire script must be spoken in 30 seconds or less!
    
    Follow these strict guidelines:
    1. Character name: Create a fun, simple alien name (2-3 syllables maximum)
    2. Emotion: Choose one emotion that best matches the story's tone
    3. Alien title: Maximum 8 words
    4. Alien content: Maximum 2 short sentences (about 20-25 words total)
    5. Use simple words that children know
    6. Make it fun but keep it brief
    7. Avoid any scary or complex topics
    8. If the original news is inappropriate for children, create a very short, fun alien story instead
    
    For vocabulary, select 3 simple English words that are:
    1. From your alien story
    2. Appropriate for ages 6-10
    3. Useful for daily life or school
    
    For each vocabulary word:
    1. Give a one-line, super simple explanation (5-7 words maximum)
    2. NO example sentences needed
    
    Format the response as JSON:
    {{
        "character_name": "fun alien name (2-3 syllables)",
        "emotion": "one of: happy, excited, surprised, curious, proud, thoughtful",
        "alien_title": "very short title (max 8 words)",
        "alien_content": "two short, simple sentences maximum",
        "vocab": [
            {{"word": "word1", "explanation": "very brief explanation (5-7 words)"}},
            {{"word": "word2", "explanation": "very brief explanation (5-7 words)"}},
            {{"word": "word3", "explanation": "very brief explanation (5-7 words)"}}
        ]
    }}
    
    Remember: All content MUST fit in a 30-second audio clip!
    """
    
    try:
        # client = OpenAI(
        #     api_key=os.getenv('OPENAI_API_KEY'),
        #     base_url="https://openrouter.ai/api/v1",
        #     default_headers={
        #         "X-Title": "Space English Learning App",
        #         "Content-Type": "application/json"
        #     }
        # )

        client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))
        
        # response = client.chat.completions.create(
        #     model="deepseek/deepseek-r1:free",
        #     messages=[
        #         {
        #             "role": "system", 
        #             "content": "You are a friendly alien teacher who explains Earth news to young children (ages 6-10) in a fun, simple way. You always use age-appropriate language and make learning English fun!"
        #         },
        #         {"role": "user", "content": prompt}
        #     ],
        #     temperature=0.7,
        #     max_tokens=1000
        # )
        
        # if not response.choices or not response.choices[0].message:
        #     raise ValueError("No response received from OpenRouter")
            
        # content = response.choices[0].message.content

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[prompt]
        )

        content = response.text
        print(f"Raw response content: {content}")
        return content
        
    except Exception as e:
        print(f"Error in generate_alien_news: {str(e)}")
        print(f"Full error details: {repr(e)}")
        raise

def get_random_voice(gender="male"):
    """
    Get a random voice ID and name from the predefined list.
    
    Args:
        gender (str): Preferred gender of the voice ("male", "female", or None for any)
                     Default is "male"
    
    Returns:
        dict: Voice information with id, name, and gender
    """
    voices = [
        {"id": "IKne3meq5aSn9XLyUdCD", "name": "Charlie", "gender": "male"}, 
        {"id": "Xb7hH8MSUJpSbSDYk0k2", "name": "Alice", "gender": "female"}, 
        {"id": "iP95p4xoKVk53GoZ742B", "name": "Chris", "gender": "male"}, 
        {"id": "cjVigY5qzO86Huf0OWal", "name": "Eric", "gender": "male"}, 
        {"id": "cgSgspJ2msm6clMCkdW9", "name": "Jessica", "gender": "female"},
        {"id": "pFZP5JQG7iQjIQuC4Bku", "name": "Lily", "gender": "female"},
    ]
    
    # Filter voices by gender if specified
    if gender:
        filtered_voices = [voice for voice in voices if voice["gender"] == gender.lower()]
        # If no voices match the gender, fall back to all voices
        if filtered_voices:
            return random.choice(filtered_voices)
    
    # Return random voice from all voices if gender is None or no matching voices found
    return random.choice(voices)

def generate_audio(
    text: str,
    timestamp: Optional[str] = None,
    gender: str = "male",
    base_path: str = "data",
    filename: Optional[str] = None,
    voice: Optional[str] = None
) -> Optional[str]:
    """
    Generate an audio file using the ElevenLabs API

    Args:
        text: Text to convert to speech
        timestamp: Timestamp to use in the filename
        gender: Gender of the voice to use (male/female)
        base_path: Base directory to save the file to
        filename: Optional filename to use
        voice: Optional specific voice dictionary to use

    Returns:
        Path to the generated audio file
    """
    try:
        # Use timestamp if provided, otherwise generate a new one
        if not timestamp:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Use filename if provided, otherwise generate one
        audio_filename = filename if filename else f"alien_news_{timestamp}.mp3"
        
        # Make sure the audio folder exists
        os.makedirs(f"{base_path}/audio", exist_ok=True)
        
        audio_path = f"{base_path}/audio/{audio_filename}"
        
        # Use provided voice if available, otherwise get a random voice based on gender
        if not voice:
            voice = get_random_voice(gender)
            print(f"Using random {gender} voice: {voice.get('name')} ({voice.get('id')})")
        else:
            print(f"Using specified voice: {voice.get('name')} ({voice.get('id')})")
        
        client = ElevenLabs(
            api_key=os.getenv('ELEVENLABS_API_KEY')
        )

        # Call the ElevenLabs API to generate audio
        audio_response = client.text_to_speech.convert(
            text=text,
            voice_id=voice["id"],
            model_id="eleven_multilingual_v2",  # Latest multilingual model
            output_format="mp3_44100_128",
        )
        
        # Handle the response, which could be bytes or a generator
        if hasattr(audio_response, 'read'):
            # If it's a file-like object with read method (BytesIO, etc.)
            audio_data = audio_response.read()
        elif hasattr(audio_response, '__iter__') and not isinstance(audio_response, (bytes, str)):
            # If it's an iterable/generator but not already bytes or string
            # Convert generator to bytes by reading chunks
            audio_chunks = bytearray()
            for chunk in audio_response:
                audio_chunks.extend(chunk)
            audio_data = bytes(audio_chunks)
        else:
            # Assume it's already bytes
            audio_data = audio_response
        
        # Save the audio file
        with open(audio_path, "wb") as audio_file:
            audio_file.write(audio_data)
        
        print(f"Audio saved to {audio_path}")
        return audio_path
    except Exception as e:
        print(f"Error generating audio: {e}")
        import traceback
        traceback.print_exc()
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
    <break time="500ms"/>
    
    Word number two: <break time="200ms"/>{vocab_words[1]['word']}
    This word means: <break time="200ms"/>{vocab_words[1]['explanation']}
    <break time="500ms"/>
    
    Word number three: <break time="200ms"/>{vocab_words[2]['word']}
    This word means: <break time="200ms"/>{vocab_words[2]['explanation']}
    <break time="800ms"/>
    
    That's all for today's alien news! <break time="300ms"/>Keep learning and having fun!
    <break time="500ms"/>Goodbye, Earth friends!
    """
    return content

def get_random_character_attributes(gender=None):
    """
    Get random character attributes for the alien character.
    
    Args:
        gender (str, optional): Preferred gender of the character ("male", "female", or None for neutral)
                               Default is None (neutral appearance)
    
    Returns:
        dict: Dictionary of character attributes
    """
    skin_colors = [
        "light blue", "mint green", "pale lavender"
    ]
    
    # Gender-specific or neutral hairstyles
    male_hair_styles = [
        "short cropped hair", "subtle quiff", "neat side part"
    ]
    
    female_hair_styles = [
        "neat bun", "short pixie cut", "shoulder-length waves"
    ]
    
    neutral_hair_styles = [
        "short tidy style", "medium-length style", "sleek look"
    ]
    
    hair_colors = [
        "red", "silver", "pale pink"
    ]
    
    # Updated to focus on professional attire with gender variations
    male_suit_styles = [
        "professional male news anchor suit in navy blue", 
        "professional male news anchor suit in charcoal gray",
        "professional male news anchor suit in dark green"
    ]
    
    female_suit_styles = [
        "professional female news anchor blazer in light gray",
        "professional female news anchor outfit in beige",
        "professional female news anchor blouse and blazer in navy"
    ]
    
    neutral_suit_styles = [
        "professional news anchor outfit in neutral tones",
        "clean, professional news anchor attire",
        "modern news presenter outfit"
    ]
    
    # Features that can be gender-influenced
    male_features = [
        "defined jawline with slight freckles",
        "human-like face structure with neat appearance",
        "expressive eyes with defined features"
    ]
    
    female_features = [
        "soft features with slight freckles",
        "human-like face structure with gentle curves",
        "large expressive eyes with softer features"
    ]
    
    neutral_features = [
        "balanced facial features with slight freckles",
        "human-like face structure for facial detection",
        "expressive eyes with clear nose and lips"
    ]

    # Base newsroom template with variations
    newsroom_base = "modern news studio with digital screens and a news desk"
    
    # Select attributes based on gender preference
    if gender and gender.lower() == "male":
        hair_style = random.choice(male_hair_styles)
        outfit = random.choice(male_suit_styles)
        unique_feature = random.choice(male_features)
    elif gender and gender.lower() == "female":
        hair_style = random.choice(female_hair_styles)
        outfit = random.choice(female_suit_styles)
        unique_feature = random.choice(female_features)
    else:
        hair_style = random.choice(neutral_hair_styles)
        outfit = random.choice(neutral_suit_styles)
        unique_feature = random.choice(neutral_features)
    
    return {
        'skin_color': random.choice(skin_colors),
        'hair_style': hair_style,
        'hair_color': random.choice(hair_colors),
        'outfit': outfit,
        'unique_feature': unique_feature,
        'setting': newsroom_base,
        'gender': gender.lower() if gender else "neutral"
    }

def get_random_character_file(resource_dir="resource/characters"):
    """
    Randomly select a character file from the resource/characters directory and parse its YAML content.
    
    Args:
        resource_dir (str): Path to the directory containing character YAML files
        
    Returns:
        dict: The parsed YAML data from the selected file, or None if no files found or error occurs
    """
    try:
        # Ensure the directory exists
        if not os.path.isdir(resource_dir):
            print(f"Character resource directory not found: {resource_dir}")
            return None
            
        # Get all YAML files in the directory
        yaml_files = glob.glob(os.path.join(resource_dir, "*.yaml"))
        yaml_files.extend(glob.glob(os.path.join(resource_dir, "*.yml")))
        
        if not yaml_files:
            print(f"No YAML files found in {resource_dir}")
            return None
            
        # Randomly select a file
        selected_file = random.choice(yaml_files)
        print(f"Selected character file: {selected_file}")
        
        # Parse the YAML file
        with open(selected_file, 'r', encoding='utf-8') as file:
            character_data = yaml.safe_load(file)
            
        return character_data
        
    except Exception as e:
        print(f"Error selecting character file: {str(e)}")
        print(f"Error details: {repr(e)}")
        return None

def generate_character_image(character_name, emotion, timestamp, gender=None, base_path="data", use_character_file=False, service="runninghub"):
    """
    Generate a hyper-realistic portrait of the alien character with the specified emotion.
    
    Args:
        character_name: Name of the alien character
        emotion: Emotional state of the character
        timestamp: Timestamp string in YYYYMMDDhhmmss format
        gender: Preferred gender presentation of the character ("male", "female", or None for neutral)
        base_path: Base path for saving files
        use_character_file: Whether to use predefined character data from YAML files
        service: Service to use for image generation ("runninghub" or "gemini")
        
    Returns:
        tuple: (image_path, prompt) if successful, (None, None) if failed
            - image_path (str): Path to the generated image
            - prompt (str): The prompt used to generate the image
    """
    try:
        # Determine character attributes source
        character_file_data = None
        if use_character_file:
            character_file_data = get_random_character_file()
            if character_file_data:
                print(f"Using character data from file: {character_file_data}")
        
        prompt = ""
        character_gender = gender
        
        # If using character file and it contains appearance data
        if character_file_data and 'appearance' in character_file_data:
            # Determine gender from appearance/personality or fall back to parameter
            appearance = character_file_data.get('appearance', '')
            personality = character_file_data.get('personality', '')
            appearance_lower = appearance.lower()
            
            if "male" in appearance_lower or "he" in personality.lower().split():
                character_gender = "male"
            elif "female" in appearance_lower or "she" in personality.lower().split():
                character_gender = "female"
            
            gender_descriptor = ""
            if character_gender == "male":
                gender_descriptor = "male-presenting"
            elif character_gender == "female":
                gender_descriptor = "female-presenting"
            
            # Create a detailed prompt using the full appearance description
            prompt = f"""A captivating and hyper-realistic portrait of a cute and friendly {gender_descriptor if character_gender else ""} humanoid alien journalist, clearly the central focus of the image, sitting confidently in a bright and modern news studio setting.

The alien has the following appearance: {appearance}

The alien displays a warm and inviting smile, with an overall {emotion} expression that is appealing to children. The background showcases a bright and tidy news studio, visible but intentionally out of focus to keep the alien as the primary subject. The scene includes subtle elements like digital news screens displaying graphics (not readable text), soft studio lights casting a clean white illumination, and a portion of a news desk in the foreground or background. The overall composition feels like a professional headshot with a clean and inviting backdrop.

The lighting is soft and even, ensuring a bright and well-lit composition. The entire scene communicates a sense of professionalism and approachability. Emphasis on a distinct humanoid alien character as the clear subject in a news studio environment."""

            # Add personality traits if available from character file
            if 'personality' in character_file_data:
                personality_traits = character_file_data['personality']
                prompt += f"\n\nThis character named {character_file_data.get('name', character_name)} should portray {personality_traits} through their demeanor and expression."
                
            # Add age information if available
            if 'age' in character_file_data:
                prompt += f"\n\nThe character is {character_file_data['age']} years old."
                
        else:
            # Fall back to randomly generated attributes if no character file or missing appearance
            attrs = get_random_character_attributes(gender)
            character_gender = attrs.get('gender')
            
            # Gender-specific pronouns and descriptors
            gender_descriptor = ""
            if character_gender == "male":
                gender_descriptor = "male-presenting"
            elif character_gender == "female":
                gender_descriptor = "female-presenting"
            
            # Create a detailed prompt for the alien character using generated attributes
            prompt = f"""A captivating and hyper-realistic portrait of a cute and friendly {gender_descriptor if character_gender != 'neutral' else ""} humanoid alien journalist, clearly the central focus of the image, sitting confidently in a bright and modern news studio setting. 

The alien has a distinctly human-like face with {attrs['unique_feature']}. Its skin possesses a unique {attrs['skin_color']} tone. The alien's hair is styled in a {attrs['hair_style']} of {attrs['hair_color']} color. The alien is dressed in a professional {attrs['outfit']}.

The background showcases a bright and tidy news studio, visible but intentionally out of focus to keep the alien as the primary subject. The scene includes subtle elements like digital news screens displaying graphics (not readable text), soft studio lights casting a clean white illumination, and a portion of a news desk in the foreground or background. The overall composition feels like a professional headshot with a clean and inviting backdrop.

The alien displays a warm and inviting smile, with an overall {emotion} expression that is appealing to children. The lighting is soft and even, ensuring a bright and well-lit composition. The entire scene communicates a sense of professionalism and approachability. Emphasis on a distinct humanoid alien character as the clear subject in a news studio environment."""

        print(f"generate_character_image : Prompt: {prompt}")
        
        # Extract date for folder structure (first 8 characters of timestamp)
        date = timestamp[:8]
        
        # Create output path
        os.makedirs(f"{base_path}/images/{date}", exist_ok=True)
        image_path = f"{base_path}/images/{date}/alien_news_{timestamp}.png"
        
        # Generate image based on selected service
        if service.lower() == "gemini":
            return generate_image_with_gemini(prompt, image_path, character_gender)
        else:
            return generate_image_with_runninghub(prompt, image_path, character_gender)
            
    except Exception as e:
        print(f"Error generating image: {str(e)}")
        print(f"Error details: {repr(e)}")
        return None, None

def generate_image_with_runninghub(prompt, image_path, character_gender):
    """
    Generate an image using RunningHub API.
    
    Args:
        prompt: The text prompt for image generation
        image_path: Path to save the generated image
        character_gender: Gender of the character (for logging)
        
    Returns:
        tuple: (image_path, prompt) if successful, (None, None) if failed
    """
    try:
        # Initialize RunningHub service
        runninghub_service = RunningHubService()

        # Create RunningHub task
        node_info_list = [
            {
                "nodeId": "50",
                "fieldName": "text",
                "fieldValue": prompt
            }
        ]

        print(f"RunningHub task data: {node_info_list}")

        # Create task and get task ID
        task_data = runninghub_service.create_task(
            workflow_id="1912608474486796289",  # Workflow ID for image generation
            node_info_list=node_info_list
        )
        
        if not task_data:
            print("Failed to create RunningHub task")
            return None, None
            
        task_id = task_data.get('taskId')
        if not task_id:
            print("No task ID in RunningHub response")
            return None, None
            
        # Wait for task completion and get outputs
        output = runninghub_service.wait_for_task(task_id)
        if not output:
            print("Task failed or timed out")
            return None, None
            
        # Get image URL from output
        image_url = output.get('fileUrl')
        if not image_url:
            print("No file URL in task output")
            return None, None
            
        # Download the generated image
        image_response = requests.get(image_url)
        if image_response.status_code == 200:
            # Save the image
            with open(image_path, 'wb') as f:
                f.write(image_response.content)
            
            print(f"Successfully generated {character_gender} alien image with RunningHub at: {image_path}")
            return image_path
        else:
            print(f"Error downloading image: {image_response.status_code}")
            return None, None
    
    except Exception as e:
        print(f"Error in RunningHub image generation: {str(e)}")
        return None, None

def generate_image_with_gemini(prompt, image_path, character_gender):
    """
    Generate an image using Google Gemini model.
    
    Args:
        prompt: The text prompt for image generation
        image_path: Path to save the generated image
        character_gender: Gender of the character (for logging)
        
    Returns:
        tuple: (image_path, prompt) if successful, (None, None) if failed
    """
    try:    
        # Initialize Google Gemini client
        client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))
        reference_image = PIL.Image.open('resource/reference_image/image.png')
        print(f"Reference image")
        
        # Prepare text input
        text_input = "Reference image to be used as a style guide, generate an image based on the style guide: " + prompt
        
        print(f"Sending prompt to Gemini for image generation...")
        
        # Generate image with Gemini
        response = client.models.generate_content(
            model="gemini-2.0-flash-exp-image-generation",
            contents=[text_input, reference_image],
            config=types.GenerateContentConfig(
                response_modalities=['TEXT', 'IMAGE']
            )
        )
        
        # Process the response
        image_data = None
        for part in response.candidates[0].content.parts:
            if part.inline_data is not None:
                image_data = part.inline_data.data
                break
        
        if not image_data:
            print("No image data in Gemini response")
            return None, None
            
        # Save the image
        image = PIL.Image.open(BytesIO(image_data))
        image.save(image_path)
        
        print(f"Successfully generated {character_gender} alien image with Gemini at: {image_path}")
        return image_path
        
    except Exception as e:
        print(f"Error in Gemini image generation: {str(e)}")
        print(f"Error details: {repr(e)}")
        # which line is the error?
        print(f"Error line: {e.__traceback__.tb_lineno}")
        return None, None

def generate_video(
    image_path: str,
    audio_path: Optional[str] = None,
    text: Optional[str] = None,
    voice_id: Optional[str] = None,
    output_path: str = "data/video/output.mp4",
    service: str = "runninghub"
) -> Optional[str]:
    """
    Generate a video using either RunningHub or D-ID service.
    
    Args:
        image_path: Path to the source image
        audio_path: Path to the audio file (optional)
        text: Text to be spoken (optional)
        voice_id: Voice ID for text-to-speech (optional)
        output_path: Path where the output video will be saved
        service: Service to use for video generation ("runninghub" or "did")
        
    Returns:
        str: Path to the generated video if successful, None otherwise
        
    Note:
        For D-ID service, either audio_path OR (text AND voice_id) must be provided
    """
    try:
        print(f"\nStarting video generation using {service}...")
        
        # Create directory for output if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        if service == "runninghub":
            if not audio_path:
                print("Error: RunningHub service requires audio_path")
                return None
                
            runninghub_service = RunningHubService()
            return runninghub_service.generate_video(image_path, audio_path, output_path)
            
        elif service == "did":
            if not audio_path and not (text and voice_id):
                print("Error: D-ID service requires either audio_path or both text and voice_id")
                return None
                
            did_service = DIDService()
            # Use the did_service's generate_video method which now supports both audio and text
            return did_service.generate_video(
                image_path=image_path,
                audio_path=audio_path,
                text=text,
                voice_id=voice_id,
                output_path=output_path
            )
                
        else:
            print(f"Unsupported service: {service}")
            return None
        
    except Exception as e:
        print(f"Error generating video: {str(e)}")
        print(f"Error details: {repr(e)}")
        return None

def check_folders_exist(date, base_path="data"):
    """
    Check if all required folders for today's date exist and have content.
    
    Args:
        date (str): Date string in YYYYMMDD format
        base_path (str): Base path for data storage (default: "data")
        
    Returns:
        bool: True if all folders exist and have content, False otherwise
    """
    required_folders = {
        'text': f'{base_path}/text/{date}',
        'audio': f'{base_path}/audio/{date}',
        'images': f'{base_path}/images/{date}',
        'videos': f'{base_path}/videos/{date}'
    }
    
    try:
        # Create folders if they don't exist
        for folder_path in required_folders.values():
            os.makedirs(folder_path, exist_ok=True)
            print(f"Created/checked folder: {folder_path}")
        
        return True
        
    except Exception as e:
        print(f"Error checking/creating folders: {str(e)}")
        return False

def process_article(article, session, base_path="data", service="runninghub", use_character_file=False, image_service="runninghub"):
    """
    Process a single news article with image, audio, and video generation.
    
    Args:
        article: News article data (title, description)
        session: Database session
        base_path: Base path for saving files
        service: Video service to use ('runninghub' or 'did')
        use_character_file: Whether to use predefined character data from YAML files
        image_service: Service to use for image generation ('runninghub' or 'gemini')
    
    Returns:
        News: Database entry if successful, None otherwise
    """
    try:
        # Generate timestamp in YYYYMMDDhhmmss format
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        date = timestamp[:8]  # Extract date part for folder structure
        
        if not check_folders_exist(date, base_path=base_path):
            print("Failed to create required folders")
            return None
        
        # Randomly select gender for this article (male or female)
        gender = random.choice(["male", "female"])
        print(f"Randomly selected gender for character: {gender}")
        
        alien_news = generate_alien_news(article['title'], article['description'])
        alien_data = clean_json_response(alien_news)
        
        print(f"Original Title: {article['title']}")
        print(f"Original Content: {article['description']}")
        print(f"Character Name: {alien_data['character_name']}")
        print(f"Emotion: {alien_data['emotion']}")
        print(f"Alien Title: {alien_data['alien_title']}")
        print(f"Alien Content: {alien_data['alien_content']}")
        
        # Save text content with gender information
        text_path = save_news_text(alien_data, timestamp, base_path=base_path, gender=gender)
        
        # Use the generated emotion directly
        emotion = alien_data['emotion']
        character_name = alien_data['character_name']

        
        # Generate character image using the generated character name, emotion, and gender
        image_path = generate_character_image(
            character_name, 
            emotion, 
            timestamp, 
            gender=gender, 
            base_path=base_path,
            use_character_file=use_character_file,
            service=image_service
        )

        print(f"process_article : Image path: {image_path}")
        
        if not image_path:
            print("Failed to generate image")
            return None
            
        # Generate audio content
        audio_text = generate_audio_content(
            alien_data['alien_title'],
            alien_data['alien_content'],
            alien_data['vocab']
        )
        
        # Create output path for video
        os.makedirs(f"{base_path}/videos/{date}", exist_ok=True)
        video_output_path = f"{base_path}/videos/{date}/alien_news_{timestamp}.mp4"
        
        # For RunningHub, we need to generate audio file
        # For D-ID, we can use either audio file or text directly
        audio_path = None
        if service == "runninghub" or (service == "did" and not os.getenv('USE_DID_TEXT_TO_SPEECH')):
            # Generate and save audio file with the randomly selected gender
            audio_path = generate_audio(
                text=audio_text, 
                timestamp=timestamp, 
                gender=gender, 
                base_path=base_path
            )
            
            if not audio_path:
                print("Failed to generate audio")
                return None
                
            # Generate video from audio and image files
            print(f"audio_path: {audio_path}")
            print(f"image_path: {image_path}")
            
            video_path = generate_video(
                image_path=image_path,
                audio_path=audio_path,
                output_path=video_output_path,
                service=service
            )
        else:
            # Use D-ID with text-to-speech
            print(f"Using D-ID with text-to-speech")
            print(f"image_path: {image_path}")

            # Get voice with the randomly selected gender
            voice = get_random_voice(gender)
            voice_id = voice["id"]
            
            video_path = generate_video(
                image_path=image_path,
                text=audio_text,
                voice_id=voice_id,
                output_path=video_output_path,
                service=service
            )
        
        if not video_path:
            print("Failed to generate video")
            return None
        
        # Create news entry
        news = News(
            original_title=article['title'],
            original_content=article['description'],
            alien_title=alien_data['alien_title'],
            alien_content=alien_data['alien_content'],
            vocab_word1=alien_data['vocab'][0]['word'],
            vocab_explanation1=alien_data['vocab'][0]['explanation'],
            vocab_word2=alien_data['vocab'][1]['word'],
            vocab_explanation2=alien_data['vocab'][1]['explanation'],
            vocab_word3=alien_data['vocab'][2]['word'],
            vocab_explanation3=alien_data['vocab'][2]['explanation'],
            audio_path=audio_path,
            image_path=image_path,
            video_path=video_path
        )
        
        session.add(news)
        print(f"Generated files for article {timestamp}:")
        print(f"- Text: {text_path}")
        if audio_path:
            print(f"- Audio: {audio_path}")
        print(f"- Image: {image_path}")
        print(f"- Video: {video_path}")
        print('--------------------------------')
        
        return news
        
    except Exception as e:
        print(f"Error processing article: {str(e)}")
        print(f"Error details: {repr(e)}")
        print(f"Error line: {e.__traceback__.tb_lineno}")
        return None

def job(base_path="data", service="runninghub", use_character_file=False, image_service="runninghub"):
    """
    Main job function to fetch news and process articles.
    
    Args:
        base_path: Base path for data storage (default: "data")
        service: Video service to use (default: "runninghub")
        use_character_file: Whether to use predefined character data from YAML files
        image_service: Service to use for image generation ('runninghub' or 'gemini')
    """
    print(f"Starting news fetch at {datetime.now()}")
    print(f"Using video service: {service}")
    print(f"Using image service: {image_service}")
    print(f"Base path: {base_path}")
    print(f"Using character files: {use_character_file}")
    
    # Get today's date in YYYYMMDD format for folder structure
    date = datetime.now().strftime('%Y%m%d')
    
    # Check if today's folders already exist and have content
    if check_folders_exist(date, base_path=base_path):
        print(f"Folders for {date} created successfully.")
    
    engine = setup_database()
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        articles = get_news()
        print(f"Found {len(articles)} articles to process")
        
        successful_articles = 0
        for article in articles:
            if process_article(
                article, 
                session, 
                base_path=base_path, 
                service=service, 
                use_character_file=use_character_file,
                image_service=image_service
            ):
                successful_articles += 1
        
        session.commit()
        print(f"\nSuccessfully processed {successful_articles} out of {len(articles)} articles")
        
    except Exception as e:
        print(f"Error occurred in job: {str(e)}")
        print(f"Error details: {repr(e)}")
        session.rollback()
    finally:
        session.close()

def save_news_text(alien_data, timestamp, base_path="data", gender=None):
    """Save the alien news text content to a file.
    
    Args:
        alien_data: Dictionary with alien news content
        timestamp: Timestamp string in YYYYMMDDhhmmss format
        base_path: Base path for saving files
        gender: Gender of the character (optional)
    
    Returns:
        str: Path to the saved text file
    """
    text_content = {
        "character_name": alien_data['character_name'],
        "emotion": alien_data['emotion'],
        "alien_title": alien_data['alien_title'],
        "alien_content": alien_data['alien_content'],
        "vocab": alien_data['vocab']
    }
    
    # Add gender if provided
    if gender:
        text_content["gender"] = gender
    
    # Extract date for folder structure (first 8 characters of timestamp)
    date = timestamp[:8]
    
    # Create directory if it doesn't exist
    os.makedirs(f"{base_path}/text/{date}", exist_ok=True)
    
    file_path = f"{base_path}/text/{date}/alien_news_{timestamp}.json"
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(text_content, f, ensure_ascii=False, indent=2)
    
    return file_path

def main():
    """Main function to run the scheduled job or process command line arguments."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Alien News Generator')
    parser.add_argument('--run-now', action='store_true', help='Run the job immediately')
    parser.add_argument('--service', choices=['runninghub', 'did'], default='runninghub',
                        help='Video service to use (default: runninghub)')
    parser.add_argument('--image-service', choices=['runninghub', 'gemini'], default='runninghub',
                        help='Image generation service to use (default: runninghub)')
    parser.add_argument('--base-path', default='data',
                        help='Base path for data storage (default: data)')
    parser.add_argument('--use-text-to-speech', action='store_true',
                        help='Use text-to-speech instead of audio files (only for D-ID)')
    parser.add_argument('--use-character-file', action='store_true',
                        help='Use predefined character data from YAML files')
    
    args = parser.parse_args()
    
    # If using text-to-speech, set the environment variable
    if args.use_text_to_speech and args.service == 'did':
        os.environ['USE_DID_TEXT_TO_SPEECH'] = 'true'
    
    if args.run_now:
        job(
            base_path=args.base_path, 
            service=args.service, 
            use_character_file=args.use_character_file,
            image_service=args.image_service
        )
    else:
        # Schedule job to run at midnight HKT
        hkt = pytz.timezone('Asia/Hong_Kong')
        schedule.every().day.at("00:00").do(
            job, 
            base_path=args.base_path, 
            service=args.service, 
            use_character_file=args.use_character_file,
            image_service=args.image_service
        )
        
        print(f"Job scheduled to run daily at midnight HKT. Press Ctrl+C to exit.")
        print(f"Using video service: {args.service}")
        print(f"Using image service: {args.image_service}")
        print(f"Base path: {args.base_path}")
        print(f"Text-to-speech: {'Enabled' if args.use_text_to_speech and args.service == 'did' else 'Disabled'}")
        print(f"Using character files: {args.use_character_file}")
        
        # Keep the script running
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)
        except KeyboardInterrupt:
            print("Exiting...")

if __name__ == "__main__":
    main() 