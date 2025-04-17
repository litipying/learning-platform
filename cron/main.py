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
import http.client
import random

# Add Runninghub API configuration
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
            "X-Title": "Space English Learning App",
            "Content-Type": "application/json"
        }
    )
    
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

def get_random_voice():
    """Get a random voice ID and name from the predefined list."""
    voices = [
        {"id": "IKne3meq5aSn9XLyUdCD", "name": "Charlie"}, 
        {"id": "Xb7hH8MSUJpSbSDYk0k2", "name": "Alice"}, 
        {"id": "iP95p4xoKVk53GoZ742B", "name": "Chris"}, 
        {"id": "cjVigY5qzO86Huf0OWal", "name": "Eric"}, 
        {"id": "cgSgspJ2msm6clMCkdW9", "name": "Jessica"},
        {"id": "pFZP5JQG7iQjIQuC4Bku", "name": "Lily"},
    ]
    return random.choice(voices)

def generate_audio(text, today, sequence_num):
    """Generate audio file using ElevenLabs API."""
    try:
        # Initialize ElevenLabs client
        client = ElevenLabs(
            api_key=os.getenv('ELEVENLABS_API_KEY')
        )
        
        # Get random voice
        voice = get_random_voice()
        
        # Generate audio with a randomly selected child-friendly voice
        audio_generator = client.text_to_speech.convert(
            text=text,
            voice_id=voice["id"],
            model_id="eleven_multilingual_v2",  # Latest multilingual model
            output_format="mp3_44100_128"  # High-quality audio
        )
        
        # Save the audio file
        file_path = f"data/audio/{today}/alien_news_{today}_{sequence_num}.mp3"
        
        # Convert generator to bytes and write to file
        audio_bytes = b''.join(chunk for chunk in audio_generator)
        with open(file_path, 'wb') as f:
            f.write(audio_bytes)
        
        print(f"Successfully generated audio with settings:")
        print(f"- Voice: {voice['name']} (ID: {voice['id']})")
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

def create_runninghub_task(workflow_id, input_data=None, node_info_list=None):
    """
    Create a task in RunningHub API.
    
    Args:
        workflow_id (str): The ID of the workflow to execute
        input_data (dict, optional): Additional input data for the workflow
        node_info_list (list, optional): List of node information
    
    Returns:
        dict: Response from the API containing task details
        None: If the request fails
    """
    try:
        if not RUNNINGHUB_API_KEY:
            print("Error: RUNNINGHUB_API_KEY environment variable is not set")
            return None

        # Prepare the payload
        payload = {
            "apiKey": RUNNINGHUB_API_KEY,
            "workflowId": workflow_id,
        }

        # Add either nodeInfoList or input data with addMetadata
        if node_info_list is not None:
            payload["nodeInfoList"] = node_info_list
        else:
            payload["addMetadata"] = True
            if input_data:
                payload["input"] = input_data

        print(f"Payload: {payload}")

        # Create connection
        conn = http.client.HTTPSConnection("www.runninghub.ai")
        
        headers = {
            'Host': 'www.runninghub.ai',
            'Content-Type': 'application/json'
        }

        # Make the request
        conn.request(
            "POST",
            "/task/openapi/create",
            json.dumps(payload),
            headers
        )

        # Get response
        response = conn.getresponse()
        response_data = json.loads(response.read().decode("utf-8"))
        
        if response.status == 200 and response_data.get('code') == 0:
            print(f"Response data: {response_data}")
            task_data = response_data.get('data', {})
            task_id = task_data.get('taskId')
            task_status = task_data.get('taskStatus')
            
            if task_id:
                print(f"Successfully created RunningHub task:")
                print(f"- Task ID: {task_id}")
                print(f"- Initial Status: {task_status}")
                return task_data
            else:
                print("No task ID in response data")
                return None
        else:
            error_msg = response_data.get('msg', 'Unknown error')
            print(f"Error from RunningHub API: {response.status}")
            print(f"Error message: {error_msg}")
            print(f"Response: {response_data}")
            return None

    except Exception as e:
        print(f"Error creating RunningHub task: {str(e)}")
        print(f"Error details: {repr(e)}")
        return None

def check_runninghub_task_status(task_id):
    """
    Check the status of a RunningHub task.
    
    Args:
        task_id (str): The ID of the task to check
    
    Returns:
        dict: Response from the API containing code, msg, and data
        None: If the request fails
    """
    try:
        if not RUNNINGHUB_API_KEY:
            print("Error: RUNNINGHUB_API_KEY environment variable is not set")
            return None

        # Prepare the payload
        payload = {
            "apiKey": RUNNINGHUB_API_KEY,
            "taskId": task_id
        }

        # Create connection
        conn = http.client.HTTPSConnection("www.runninghub.ai")
        
        headers = {
            'Host': 'www.runninghub.ai',
            'Content-Type': 'application/json'
        }

        # Make the request
        conn.request(
            "POST",
            "/task/openapi/status",
            json.dumps(payload),
            headers
        )

        # Get response
        response = conn.getresponse()
        response_data = json.loads(response.read().decode("utf-8"))

        print(f"Status check response: {response_data}")
        
        if response.status == 200:
            return response_data
        else:
            print(f"Error from RunningHub API: {response.status}")
            print(f"Response: {response_data}")
            return None

    except Exception as e:
        print(f"Error checking RunningHub task status: {str(e)}")
        print(f"Error details: {repr(e)}")
        return None

def get_runninghub_task_outputs(task_id):
    """
    Get the outputs of a completed RunningHub task.
    
    Args:
        task_id (str): The ID of the task to get outputs for
    
    Returns:
        list: List of output files with their URLs and metadata
        None: If the request fails
    """
    try:
        if not RUNNINGHUB_API_KEY:
            print("Error: RUNNINGHUB_API_KEY environment variable is not set")
            return None

        # Prepare the payload
        payload = {
            "apiKey": RUNNINGHUB_API_KEY,
            "taskId": task_id
        }

        # Create connection
        conn = http.client.HTTPSConnection("www.runninghub.ai")
        
        headers = {
            'Host': 'www.runninghub.ai',
            'Content-Type': 'application/json'
        }

        # Make the request
        conn.request(
            "POST",
            "/task/openapi/outputs",
            json.dumps(payload),
            headers
        )

        # Get response
        response = conn.getresponse()
        response_data = json.loads(response.read().decode("utf-8"))
        
        if response.status == 200 and response_data.get('code') == 0:
            outputs = response_data.get('data', [])
            if outputs:
                print(f"Successfully retrieved {len(outputs)} output(s)")
                return outputs
            else:
                print("No outputs found in response")
                return None
        else:
            print(f"Error from RunningHub API: {response.status}")
            print(f"Response: {response_data}")
            return None

    except Exception as e:
        print(f"Error getting RunningHub task outputs: {str(e)}")
        print(f"Error details: {repr(e)}")
        return None

def wait_for_runninghub_task(task_id, max_attempts=100, delay_seconds=10):
    """
    Wait for a RunningHub task to complete and get its outputs.
    
    Args:
        task_id (str): The ID of the task to wait for
        max_attempts (int): Maximum number of status check attempts
        delay_seconds (int): Delay between status checks in seconds
    
    Returns:
        dict: Task outputs if successful
        None: If the task failed or timed out
    """
    print(f"Waiting for RunningHub task {task_id} to complete...")
    
    for attempt in range(max_attempts):
        response = check_runninghub_task_status(task_id)
        
        if not response:
            print(f"Failed to get task status (attempt {attempt + 1}/{max_attempts})")
            time.sleep(delay_seconds)
            continue
        
        # Print detailed status information
        print(f"Status check {attempt + 1}/{max_attempts}:")
        print(f"- Code: {response.get('code')}")
        print(f"- Message: {response.get('msg', '')}")
        print(f"- Data: {response.get('data', '')}")
        
        code = response.get('code')
        data = response.get('data', '')
        
        if code == 0 and data == 'SUCCESS':
            print("Task completed successfully!")
            # Get task outputs
            outputs = get_runninghub_task_outputs(task_id)
            if outputs:
                return outputs[0]  # Return the first output
            else:
                print("Task completed but no outputs found")
                return None
        elif code == 0 and data == 'FAILED':
            print("❌ Task failed with status FAILED")
            return None
        elif code == 0:
            # Code 0 but not SUCCESS or FAILED means still running
            print(f"Task still running (attempt {attempt + 1}/{max_attempts})...")
            time.sleep(delay_seconds)
            continue
        else:
            # Any other code indicates an error
            print(f"Task failed with code: {code}")
            print(f"Error message: {response.get('msg', 'No error message')}")
            return None
    
    print(f"Task timed out after {max_attempts} attempts")
    return None

def get_random_character_attributes():
    """Get random character attributes for the alien character."""
    skin_colors = [
        "iridescent blue", "shimmering green", "metallic purple", 
        "glowing pink", "crystalline turquoise", "pearlescent silver",
        "rainbow-shifting", "starry black", "nebula-patterned"
    ]
    
    skin_textures = [
        "smooth and glossy", "softly glowing", "crystal-like",
        "semi-translucent", "metallic shimmering", "star-speckled",
        "holographic", "bubble-like", "cloud-textured"
    ]
    
    hair_styles = [
        "floating cosmic energy strands", "glowing crystalline spikes",
        "flowing zero-gravity waves", "geometric holographic patterns",
        "constellation-like dots", "spiral nebula swirls",
        "meteor shower streaks", "aurora-like streams",
        "no hair but glowing markings"
    ]
    
    hair_colors = [
        "shifting galaxy colors", "pulsing neon", "shimmering rainbow",
        "star-sparkled silver", "flowing aurora lights", "cosmic gradient",
        "glowing constellation patterns", "nebula swirls", "meteor shower sparkles"
    ]
    
    # Updated to focus on formal business suits with cosmic elements
    suit_styles = [
        "classic navy business suit with subtle starlight pinstripes",
        "charcoal grey suit with constellation pattern lapels",
        "black formal suit with galaxy-shimmer finish",
        "traditional business suit with glowing energy trim",
        "formal three-piece suit with nebula-pattern vest",
        "professional suit with aurora-like collar accents",
        "elegant business suit with floating light details",
        "tailored suit with cosmic dust highlights",
        "formal attire with holographic pinstripes"
    ]
    
    suit_accessories = [
        "with a floating cosmic tie",
        "with a crystalline pocket square",
        "with glowing cufflinks",
        "with a shimmering lapel pin",
        "with an energy-field bowtie",
        "with a starlight-trimmed collar",
        "with nebula-pattern buttons",
        "with an aurora-effect tie clip",
        "with constellation-pattern trim"
    ]
    
    # Combine suit style with an accessory
    outfit = f"{random.choice(suit_styles)} {random.choice(suit_accessories)}"
    
    unique_features = [
        "crystal antennae that glow with emotions", "floating orbital accessories",
        "holographic patterns that shift with mood", "constellation freckles",
        "geometric energy markings", "floating light particles around them",
        "aurora-like aura", "star-like sparkles in their eyes",
        "nebula patterns that swirl on their skin"
    ]

    # Base newsroom template with variations
    newsroom_base = "space station newsroom with floating screens and a news desk"
    newsroom_backgrounds = [
        "swirling galaxy", "twinkling stars", "aurora lights",
        "nebula clouds", "meteor shower", "cosmic dust",
        "planetary rings", "shooting stars", "space phenomena"
    ]
    
    newsroom_desk_features = [
        "holographic displays", "floating data streams",
        "glowing control panels", "orbiting microphones",
        "energy field barriers", "crystal decorations",
        "anti-gravity props", "light beam accents",
        "star map projections"
    ]
    
    newsroom_lighting = [
        "soft cosmic glow", "pulsing star lights",
        "rainbow aurora effects", "crystal refraction patterns",
        "nebula-like illumination", "constellation spotlights",
        "meteor streak lighting", "plasma field ambiance",
        "quantum light particles"
    ]

    # Art styles specific to newsroom setting
    art_styles = [
        "clean and modern cartoon with soft gradients",
        "semi-realistic cartoon with glowing effects",
        "stylized animation with dynamic lighting",
        "cute chibi style with sparkle effects",
        "sleek vector art with cosmic highlights",
        "playful cartoon with ethereal elements",
        "polished 3D cartoon style with glow effects",
        "whimsical illustration with space themes",
        "geometric cartoon with light ray accents"
    ]
    
    # Combine elements for a consistent but varied newsroom setting
    setting = f"{newsroom_base} featuring a {random.choice(newsroom_backgrounds)} background, {random.choice(newsroom_desk_features)}, and {random.choice(newsroom_lighting)}"
    
    return {
        'skin_color': random.choice(skin_colors),
        'skin_texture': random.choice(skin_textures),
        'hair_style': random.choice(hair_styles),
        'hair_color': random.choice(hair_colors),
        'outfit': outfit,
        'unique_feature': random.choice(unique_features),
        'setting': setting,
        'art_style': random.choice(art_styles)
    }

def generate_character_image(character_name, emotion, today, sequence_num):
    """Generate a cartoon image of the alien character with the specified emotion using RunningHub API."""
    try:
        # Get random character attributes
        attrs = get_random_character_attributes()
        
        # Create a detailed prompt for the alien character
        prompt = f"""Create a cute cartoon alien character named {character_name} for children's education:
        - Art Style: {attrs['art_style']}
        - Big expressive eyes showing {emotion} emotion
        - A cute alien news reporter with unique features:
          * Skin: {attrs['skin_color']} with {attrs['skin_texture']} texture
          * Hair: {attrs['hair_style']} in {attrs['hair_color']}
          * Wearing: {attrs['outfit']}
          * Special Feature: {attrs['unique_feature']}
        - The character should be expressing {emotion} in a way that's clear and appealing to children
        - Setting: {attrs['setting']}
        
        Important requirements:
        1. Keep the character design simple and recognizable despite the special features
        2. Make sure the {emotion} emotion is clearly visible in the expression
        3. Ensure all elements are appropriate for children
        4. Maintain a bright, well-lit composition
        5. The character should be the main focus of the image, with the newsroom setting as a backdrop
        6. The newsroom setting should be visible but not overwhelming"""
        
        # Create RunningHub task
        create_response = create_runninghub_task(
            workflow_id="1912608474486796289",  # Your workflow ID for image generation
            node_info_list=[
                {
                    "nodeId": "50",
                    "fieldName": "text",
                    "fieldValue": prompt
                }
            ]
        )
        
        if not create_response:
            print("Failed to create RunningHub task")
            return None
            
        task_id = create_response.get('taskId')
        if not task_id:
            print("No task ID in RunningHub response")
            return None
            
        # Wait for task completion and get outputs
        output = wait_for_runninghub_task(task_id)
        if not output:
            print("Task failed or timed out")
            return None
            
        # Get image URL from output
        image_url = output.get('fileUrl')
        if not image_url:
            print("No file URL in task output")
            return None
            
        # Download the generated image
        image_response = requests.get(image_url)
        if image_response.status_code == 200:
            # Save the image
            image_path = f"data/images/{today}/alien_news_{today}_{sequence_num}.png"
            with open(image_path, 'wb') as f:
                f.write(image_response.content)
            
            print(f"Successfully generated image at: {image_path}")
            print(f"Character attributes used:")
            print(f"- Art Style: {attrs['art_style']}")
            print(f"- Skin: {attrs['skin_color']} with {attrs['skin_texture']} texture")
            print(f"- Hair: {attrs['hair_style']} in {attrs['hair_color']}")
            print(f"- Outfit: {attrs['outfit']}")
            print(f"- Special Feature: {attrs['unique_feature']}")
            print(f"- Setting: {attrs['setting']}")
            print(f"Task cost time: {output.get('taskCostTime', 'unknown')} seconds")
            return image_path
        else:
            print(f"Error downloading image: {image_response.status_code}")
            return None
            
    except Exception as e:
        print(f"Error generating image: {str(e)}")
        print(f"Error details: {repr(e)}")
        return None

def check_folders_exist(today):
    """
    Check if all required folders for today's date exist and have content.
    
    Args:
        today (str): Date string in YYYYMMDD format
        
    Returns:
        bool: True if all folders exist and have content, False otherwise
    """
    required_folders = {
        'text': f'data/text/{today}',
        'audio': f'data/audio/{today}',
        'images': f'data/images/{today}',
        'videos': f'data/videos/{today}'
    }
    
    try:
        # Check if all folders exist
        for folder_path in required_folders.values():
            if not os.path.exists(folder_path):
                print(f"Folder {folder_path} does not exist")
                return False
            
            # Check if folder has any files
            files = os.listdir(folder_path)
            if not files:
                print(f"Folder {folder_path} is empty")
                return False
            
            # Check if files match the expected pattern
            pattern = f"alien_news_{today}_"
            matching_files = [f for f in files if f.startswith(pattern)]
            if not matching_files:
                print(f"No matching files found in {folder_path}")
                return False
        
        print(f"All required folders for {today} exist and have content")
        return True
        
    except Exception as e:
        print(f"Error checking folders: {str(e)}")
        return False

def process_article(article, session, sequence_num):
    """Process a single news article with image, audio, and video generation."""
    try:
        # Create date-based folders
        folders, today = create_date_folders()
        
        alien_news = generate_alien_news(article['title'], article['description'])
        alien_data = clean_json_response(alien_news)
        
        print(f"Original Title: {article['title']}")
        print(f"Original Content: {article['description']}")
        print(f"Character Name: {alien_data['character_name']}")
        print(f"Emotion: {alien_data['emotion']}")
        print(f"Alien Title: {alien_data['alien_title']}")
        print(f"Alien Content: {alien_data['alien_content']}")
        
        # Save text content
        text_path = save_news_text(alien_data, today, sequence_num)
        
        # Use the generated emotion directly
        emotion = alien_data['emotion']
        
        # Generate character image using the generated character name and emotion
        image_path = generate_character_image(alien_data['character_name'], emotion, today, sequence_num)
        
        # Generate audio content
        audio_text = generate_audio_content(
            alien_data['alien_title'],
            alien_data['alien_content'],
            alien_data['vocab']
        )
        
        # Generate and save audio file
        audio_path = generate_audio(audio_text, today, sequence_num)
        
        if not audio_path or not image_path:
            print("Failed to generate audio or image")
            return None
            
        # Generate video from audio and image files
        print(f"audio_path : {audio_path}")
        print(f"image_path : {image_path}")
        video_path = None
        
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
        print(f"Generated files for article {sequence_num}:")
        print(f"- Text: {text_path}")
        print(f"- Audio: {audio_path}")
        print(f"- Image: {image_path}")
        print(f"- Video: {video_path}")
        print('--------------------------------')
        
        return news
        
    except Exception as e:
        print(f"Error processing article: {str(e)}")
        print(f"Error details: {repr(e)}")
        return None

def job():
    print(f"Starting news fetch at {datetime.now()}")
    
    # Get today's date in YYYYMMDD format
    today = datetime.now().strftime('%Y%m%d')
    
    # Check if today's folders already exist and have content
    if check_folders_exist(today):
        print(f"Content for {today} already exists. Skipping job.")
        return
    
    engine = setup_database()
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        articles = get_news()
        print(f"Found {len(articles)} articles to process")
        
        successful_articles = 0
        for i, article in enumerate(articles, 1):
            print(f"\nProcessing article {i} of {len(articles)}")
            if process_article(article, session, i):
                successful_articles += 1
        
        session.commit()
        print(f"\nSuccessfully processed {successful_articles} out of {len(articles)} articles")
        
    except Exception as e:
        print(f"Error occurred in job: {str(e)}")
        print(f"Error details: {repr(e)}")
        session.rollback()
    finally:
        session.close()

def create_date_folders():
    """Create date-based folders for organizing content."""
    today = datetime.now().strftime('%Y%m%d')
    
    folders = {
        'text': f'data/text/{today}',
        'audio': f'data/audio/{today}',
        'images': f'data/images/{today}',
        'videos': f'data/videos/{today}'
    }
    
    for folder_path in folders.values():
        os.makedirs(folder_path, exist_ok=True)
        print(f"Created folder: {folder_path}")
    
    return folders, today

def save_news_text(alien_data, today, sequence_num):
    """Save the alien news text content to a file."""
    text_content = {
        "character_name": alien_data['character_name'],
        "emotion": alien_data['emotion'],
        "alien_title": alien_data['alien_title'],
        "alien_content": alien_data['alien_content'],
        "vocab": alien_data['vocab']
    }
    
    file_path = f"data/text/{today}/alien_news_{today}_{sequence_num}.json"
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(text_content, f, ensure_ascii=False, indent=2)
    
    return file_path

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