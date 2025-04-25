#!/usr/bin/env python3
"""
Adventure Story Generator for Alien News

This script generates adventure stories for alien characters, including:
1. Loading character data from YAML files
2. Generating an alien character image using Google Gemini
3. Creating an adventure story for the character using Google Gemini
4. Generating adventure scene images based on the story
5. Creating voice narrations for each scene using ElevenLabs
6. Storing story data in a SQLite database
"""

import os
import time
import json
import yaml
import argparse
import sqlite3
import random
from io import BytesIO
from datetime import datetime
import logging
import traceback

import PIL.Image
from google import genai
from google.genai import types

# Import shared functions from main.py
from main import (
    get_random_character_file,
    clean_json_response,
    generate_audio,
    get_random_voice
)

def setup_gemini_client():
    """
    Set up and configure the Google Gemini client.
    
    Returns:
        genai.Client: Configured Gemini client, or None if setup fails
    """
    # Check for API key
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("GEMINI_API_KEY environment variable not set")
        return None
        
    # Configure Gemini
    try:
        client = genai.Client(api_key=api_key)
        return client
    except Exception as e:
        print(f"Error setting up Gemini client: {str(e)}")
        return None

def generate_character_image(character_data, output_path):
    """
    Generate a character image using Google Gemini based on character data.
    
    Args:
        character_data (dict): Character data containing name, appearance, etc.
        output_path (str): Path to save the generated image
        
    Returns:
        str: Path to the generated image if successful, None otherwise
    """
    client = setup_gemini_client()
    if not client:
        return None
        
    try:
        # Create folder if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Create prompt for character image
        name = character_data.get('name', 'Alien Character')
        appearance = character_data.get('appearance', 'A humanoid alien with unique features')
        personality = character_data.get('personality', 'Friendly and curious')
        
        prompt = f"""Reference image to be used as a style guide, create a detailed, high-quality portrait image of an alien character named {name} from another planet.

Physical appearance: {appearance}

Personality: {personality}

The alien should be shown against a space-themed or alien world background that highlights their otherworldly features.
Make the image colorful, child-friendly, and expressive. The image should be detailed enough to see the character's unique alien features and convey their personality.
Include subtle elements that suggest their alien origin such as unusual skin textures, non-human anatomical features, or cosmic elements.
"""

        print(f"Generating alien character image with prompt:\n{prompt}")

        reference_image = PIL.Image.open('resource/reference_image/image.png')
        
        # Generate image with Gemini
        response = client.models.generate_content(
            model="gemini-2.0-flash-exp-image-generation",
            contents=[prompt, reference_image],
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
            return None
            
        # Save the image
        image = PIL.Image.open(BytesIO(image_data))
        image.save(output_path)
        
        print(f"Alien character image successfully generated at: {output_path}")
        return output_path
        
    except Exception as e:
        print(f"Error generating character image: {str(e)}")
        return None

def generate_adventure_story(character_data, output_path):
    """
    Generate an adventure story for the character using Google Gemini.
    
    Args:
        character_data (dict): Character data containing name, personality, backstory, etc.
        output_path (str): Path to save the generated story
        
    Returns:
        dict: Story data if successful, None otherwise
    """
    client = setup_gemini_client()
    if not client:
        return None
        
    try:
        # Create folder if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Extract character info
        name = character_data.get('name', 'Alien Character')
        personality = character_data.get('personality', 'Friendly and curious')
        backstory = character_data.get('backstory', '')
        age = character_data.get('age', 'unknown')
        
        # Create prompt for story generation
        prompt = f"""Create a cosmic adventure story for children about an alien character named {name}.

Character details:
- Name: {name}
- Age: {age}
- Personality: {personality}
- Backstory: {backstory}

The story should:
1. Be child-friendly and include educational elements about space or alien cultures
2. Be around 500 words
3. Have a clear beginning, middle, and end
4. Include 4 distinct scenes or locations in space, alien planets, or otherworldly settings that would make good illustrations
5. Feature space travel, alien technology, or interaction with different alien species
6. Have a positive message or moral that relates to universal values like friendship, curiosity, or helping others
7. Be imaginative and fun, highlighting the unique perspective of an alien character

Please structure your response as a JSON object with the following fields:
- title: The title of the alien adventure story
- story: The full story text
- scene1: Description of the first scene (alien location, what's happening, characters present)
- scene1_story: A brief narration for the first scene (exactly 2-3 sentences, written as a string)
- scene2: Description of the second scene
- scene2_story: A brief narration for the second scene (exactly 2-3 sentences, written as a string)
- scene3: Description of the third scene
- scene3_story: A brief narration for the third scene (exactly 2-3 sentences, written as a string)
- scene4: Description of the fourth scene
- scene4_story: A brief narration for the fourth scene (exactly 2-3 sentences, written as a string)
- moral: The moral or lesson of the story

IMPORTANT:
1. Each scene description should be DETAILED (at least 4-6 sentences) and include:
   - The specific setting and environment in rich detail
   - What the main character and any other characters are doing
   - The mood or atmosphere of the scene
   - Any important objects, technology, or elements in the scene
   - How the scene connects to the overall story
   - Visual details that would translate well to an illustration

2. Each scene_story field should be a plain text string of 2-3 sentences that will be read aloud as narration for that scene.
   DO NOT include any nested objects, just a simple string for each scene_story field.

The scene descriptions are used to generate illustrations, while scene_story fields are used for voice narration.
"""

        print(f"Generating alien adventure story for character {name}")
        
        # Generate story with Gemini
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[prompt]
        )
        
        # Process the response
        story_text = response.candidates[0].content.parts[0].text
        
        # Parse the JSON from the response
        try:
            story_data = clean_json_response(story_text)

            print(f"Generated story: {story_data}")
            
            # Save the story to the output path
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(story_data, f, ensure_ascii=False, indent=2)
                
            print(f"Alien adventure story successfully generated and saved to: {output_path}")
            return story_data
            
        except json.JSONDecodeError:
            print("Failed to parse story as JSON. Saving raw text.")
            # Save the raw text if JSON parsing fails
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(story_text)
            
            # Create a simple structure for the raw text
            return {
                "title": "Alien Adventure Story",
                "story": story_text,
                "scene1": "Scene 1: Alien world",
                "scene2": "Scene 2: Space travel", 
                "scene3": "Scene 3: Encounter with other aliens",
                "scene4": "Scene 4: Return to home planet",
                "moral": "The story moral"
            }
            
    except Exception as e:
        print(f"Error generating adventure story: {str(e)}")
        # which line
        print(f"Error line: {e.__traceback__.tb_lineno}")
        return None

def generate_scene_image(character_image_path, scene_description, output_path):
    """
    Generate a scene image based on the character image and scene description.
    
    Args:
        character_image_path (str): Path to the character image
        scene_description (str): Description of the scene to generate
        output_path (str): Path to save the generated image
        
    Returns:
        str: Path to the generated image if successful, None otherwise
    """
    client = setup_gemini_client()
    if not client:
        return None
        
    try:
        # Create folder if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Load the character image
        character_image = PIL.Image.open(character_image_path)
        
        # Create prompt for scene generation
        prompt = f"""Create a detailed, colorful illustration of the following alien/space scene for a children's story:

{scene_description}

Make sure the alien character from the reference image is prominently featured in this scene.
The scene should be vibrant, child-friendly, and match the description while emphasizing its alien or cosmic nature.
Include interesting alien environments, unusual cosmic phenomena, or extraterrestrial elements that would appeal to children.
The illustration should clearly take place in an alien world, spaceship, or cosmic setting - not on Earth unless specifically mentioned in the description.
"""

        print(f"Generating alien scene image for: {scene_description}")
        
        # Generate image with Gemini
        response = client.models.generate_content(
            model="gemini-2.0-flash-exp-image-generation",
            contents=[prompt, character_image],
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
            return None
            
        # Save the image
        image = PIL.Image.open(BytesIO(image_data))
        image.save(output_path)
        
        print(f"Alien scene image successfully generated at: {output_path}")
        return output_path
        
    except Exception as e:
        print(f"Error generating scene image: {str(e)}")
        return None

def setup_database(db_path="story.db"):
    """
    Set up the SQLite database for storing story data.
    
    Args:
        db_path (str): Path to the SQLite database file
        
    Returns:
        sqlite3.Connection: Database connection object
    """
    try:
        # If only filename provided, save in data folder
        if '/' not in db_path and '\\' not in db_path:
            db_path = os.path.join("data", db_path)
            
        # Print the absolute path for debugging
        abs_path = os.path.abspath(db_path)
        print(f"Setting up database at absolute path: {abs_path}")
        
        # Ensure the directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Check directory permissions
        dir_path = os.path.dirname(db_path)
        print(f"Directory path: {dir_path}")
        print(f"Directory exists: {os.path.exists(dir_path)}")
        print(f"Directory writable: {os.access(dir_path, os.W_OK)}")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create story table if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS stories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            story_text TEXT NOT NULL,
            character_name TEXT NOT NULL,
            character_image_path TEXT NOT NULL,
            story_path TEXT NOT NULL,
            voice_id TEXT,
            moral TEXT,
            timestamp TEXT NOT NULL,
            date TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Check if scenes table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='scenes'")
        scenes_table_exists = cursor.fetchone() is not None
        
        if not scenes_table_exists:
            # Create scenes table if it doesn't exist
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS scenes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                story_id INTEGER NOT NULL,
                scene_number INTEGER NOT NULL,
                description TEXT NOT NULL,
                scene_story TEXT,
                image_path TEXT NOT NULL,
                audio_path TEXT,
                FOREIGN KEY (story_id) REFERENCES stories (id)
            )
            ''')
        else:
            # Check if scene_story column exists in the scenes table
            cursor.execute("PRAGMA table_info(scenes)")
            columns = cursor.fetchall()
            column_names = [column[1] for column in columns]
            
            # Add scene_story column if it doesn't exist
            if 'scene_story' not in column_names:
                cursor.execute('ALTER TABLE scenes ADD COLUMN scene_story TEXT')
                print("Added scene_story column to scenes table")
        
        conn.commit()
        print(f"Database setup complete at {db_path}")
        
        # Test query to verify connection is working
        cursor.execute("SELECT sqlite_version();")
        version = cursor.fetchone()
        print(f"SQLite version: {version[0]}")
        
        return conn
    except sqlite3.Error as e:
        print(f"SQLite error in setup_database: {str(e)}")
        raise
    except Exception as e:
        print(f"Unexpected error in setup_database: {str(e)}")
        raise

def save_story_to_db(conn, story_data, character_data, character_image_path, story_path, scene_images, audio_paths, timestamp, date):
    """
    Save story data to the database.
    
    Args:
        conn (sqlite3.Connection): Database connection
        story_data (dict): Story data including title, story text, etc.
        character_data (dict): Character data
        character_image_path (str): Path to character image
        story_path (str): Path to story JSON file
        scene_images (list): List of paths to scene images
        audio_paths (list): List of paths to audio files
        timestamp (str): Timestamp
        date (str): Date
        
    Returns:
        int: ID of the inserted story record
    """
    try:
        cursor = conn.cursor()
        
        # Get voice ID from the voice data if available
        voice_id = None
        if 'voice_id' in character_data:
            voice_id = character_data['voice_id']
        
        # Debug information
        print(f"Saving story to database: '{story_data.get('title', 'Untitled')}'")
        print(f"Character name: {character_data.get('name', 'Unknown')}")
        print(f"Character image path: {character_image_path}")
        print(f"Story path: {story_path}")
        print(f"Number of scene images: {len(scene_images)}")
        print(f"Number of audio paths: {len(audio_paths)}")
        
        # Insert story record
        cursor.execute('''
        INSERT INTO stories (title, story_text, character_name, character_image_path, story_path, voice_id, moral, timestamp, date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            story_data.get('title', 'Untitled'),
            story_data.get('story', ''),
            character_data.get('name', 'Unknown'),
            character_image_path,
            story_path,
            voice_id,
            story_data.get('moral', ''),
            timestamp,
            date
        ))
        
        # Get the ID of the inserted story
        story_id = cursor.lastrowid
        print(f"Inserted story record with ID: {story_id}")
        
        # Insert scene records
        for i in range(1, 5):
            scene_key = f'scene{i}'
            scene_story_key = f'scene{i}_story'
            if scene_key in story_data and i <= len(scene_images):
                audio_path = audio_paths[i-1] if i <= len(audio_paths) else None
                scene_story = story_data.get(scene_story_key, '')
                
                print(f"Inserting scene {i} for story {story_id}")
                print(f"Scene image path: {scene_images[i-1]}")
                print(f"Scene audio path: {audio_path}")
                
                cursor.execute('''
                INSERT INTO scenes (story_id, scene_number, description, scene_story, image_path, audio_path)
                VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    story_id,
                    i,
                    story_data.get(scene_key, ''),
                    scene_story,
                    scene_images[i-1],
                    audio_path
                ))
                print(f"Inserted scene {i}")
        
        # Commit the transaction
        conn.commit()
        print(f"Database transaction committed successfully")
        
        # Verify the data was saved
        cursor.execute("SELECT id, title FROM stories WHERE id = ?", (story_id,))
        verification = cursor.fetchone()
        if verification:
            print(f"Verified story record: ID={verification[0]}, Title={verification[1]}")
        else:
            print("Warning: Could not verify story record after insertion")
            
        return story_id
    except sqlite3.Error as e:
        print(f"SQLite error in save_story_to_db: {str(e)}")
        if conn:
            conn.rollback()
            print("Transaction rolled back due to error")
        raise
    except Exception as e:
        print(f"Unexpected error in save_story_to_db: {str(e)}")
        if conn:
            conn.rollback()
            print("Transaction rolled back due to error")
        raise

def setup_story_environment(base_path, timestamp):
    """
    Set up the directory structure for story generation.
    
    Args:
        base_path (str): Base path for saving files
        timestamp (str): Timestamp string for unique filenames
        
    Returns:
        tuple: (story_dir, character_dir, scene_dir, voice_dir, date) if successful
    """
    try:
        date = timestamp[:8]  # Extract date for folder structure
        
        # Create story directory structure
        story_dir = f"{base_path}/story/{date}"
        character_dir = f"{story_dir}/character"
        scene_dir = f"{story_dir}/scene"
        voice_dir = f"{story_dir}/voice"
        
        # Create all necessary directories
        os.makedirs(story_dir, exist_ok=True)
        os.makedirs(character_dir, exist_ok=True)
        os.makedirs(scene_dir, exist_ok=True)
        os.makedirs(voice_dir, exist_ok=True)
        
        return story_dir, character_dir, scene_dir, voice_dir, date
    except Exception as e:
        print(f"Error setting up story environment: {str(e)}")
        return None

def prepare_character(character_file=None):
    """
    Load and prepare character data from a file or random selection.
    
    Args:
        character_file (str, optional): Path to a specific character file
        
    Returns:
        tuple: (character_data, gender, voice) if successful, None otherwise
    """
    try:
        # Load character data
        if character_file:
            # Load specific character file
            with open(character_file, 'r', encoding='utf-8') as f:
                character_data = yaml.safe_load(f)
                character_data_path = character_file
        else:
            # Get random character
            character_data = get_random_character_file()
            character_data_path = None
            
        if not character_data:
            print("Failed to load character data")
            return None
            
        name = character_data.get('name', 'Alien Character')
        print(f"Generating adventure for character: {name}")
        
        # Determine gender from character data (for voice selection)
        gender = None
        appearance = character_data.get('appearance', '').lower()
        personality = character_data.get('personality', '').lower()
        
        if "male" in appearance or "he" in personality.split():
            gender = "male"
        elif "female" in appearance or "she" in personality.split():
            gender = "female"
        else:
            # Randomly select gender for voice if not specified
            gender = random.choice(["male", "female"])
            
        print(f"Using {gender} voice for narration")
        voice = get_random_voice(gender)
        
        # Store the voice_id in the character data for database storage
        if voice:
            character_data['voice_id'] = voice.get('id')
        else:
            print("Warning: No voice_id available in the voice object")
            
        return character_data, gender, voice, character_data_path
    except Exception as e:
        print(f"Error preparing character: {str(e)}")
        return None

def create_character_image(character_data, character_dir, timestamp):
    """
    Generate an image for the character.
    
    Args:
        character_data (dict): Character data dictionary
        character_dir (str): Directory to save the character image
        timestamp (str): Timestamp string for unique filenames
        
    Returns:
        str: Path to the generated character image if successful, None otherwise
    """
    try:
        character_image_path = f"{character_dir}/character_{timestamp}.png"
        character_image = generate_character_image(character_data, character_image_path)
        
        if not character_image:
            print("Failed to generate character image")
            return None
            
        return character_image
    except Exception as e:
        print(f"Error creating character image: {str(e)}")
        return None

def create_adventure_story(character_data, story_dir, timestamp):
    """
    Generate an adventure story for the character.
    
    Args:
        character_data (dict): Character data dictionary
        story_dir (str): Directory to save the story
        timestamp (str): Timestamp string for unique filenames
        
    Returns:
        tuple: (story_data, story_path) if successful, None otherwise
    """
    try:
        story_path = f"{story_dir}/story_{timestamp}.json"
        story_data = generate_adventure_story(character_data, story_path)
        
        if not story_data:
            print("Failed to generate adventure story")
            return None
            
        return story_data, story_path
    except Exception as e:
        print(f"Error creating adventure story: {str(e)}")
        return None

def generate_scene_images_and_audio(story_data, character_image_path, scene_dir, voice_dir, timestamp, voice, base_path, date):
    """
    Generate images and audio for each scene in the story.
    
    Args:
        story_data (dict): Story data containing scene descriptions
        character_image_path (str): Path to the character image
        scene_dir (str): Directory to save the scene images
        voice_dir (str): Directory to save the audio files
        timestamp (str): Timestamp string for unique filenames
        voice (dict): Voice data for audio generation
        base_path (str): Base path for saving files
        date (str): Date string for folder structure
        
    Returns:
        tuple: (scene_images, audio_paths) lists of paths to generated content
    """
    try:
        scene_images = []
        audio_paths = []
        
        # Generate scene images and audio for each scene
        for i in range(1, 5):
            scene_key = f"scene{i}"
            scene_story_key = f"scene{i}_story"
            scene_description = story_data.get(scene_key, f"Scene {i} of the adventure")
            scene_story = story_data.get(scene_story_key, scene_description)
            scene_path = f"{scene_dir}/scene{i}_{timestamp}.png"
            
            # Generate the scene image
            scene_image = generate_scene_image(character_image_path, scene_description, scene_path)
            if scene_image:
                scene_images.append(scene_image)
                
                # Generate audio for this scene using scene_story instead of scene_description
                scene_audio_filename = f"scene{i}_{timestamp}.mp3"
                
                # Ensure scene_story is a string, not a dictionary
                if isinstance(scene_story, dict):
                    print(f"Warning: scene{i}_story is a dictionary, extracting text value")
                    # Try to extract the text from the dictionary
                    scene_text = scene_story.get('scene_story', '') or scene_story.get('text', '') or str(scene_story)
                else:
                    scene_text = str(scene_story)
                    
                print(f"Generating audio for scene {i} with text: {scene_text[:50]}...")

                scene_audio = generate_audio(
                    text=scene_text, 
                    timestamp=timestamp,
                    base_path=f"{base_path}/story/{date}/voice",
                    filename=scene_audio_filename,
                    voice=voice
                )

                if scene_audio:
                    audio_paths.append(scene_audio)
                    print(f"Scene {i} audio generated at: {scene_audio}")
            else:
                print(f"Failed to generate image for {scene_key}")
                
        return scene_images, audio_paths
    except Exception as e:
        print(f"Error generating scene images and audio: {str(e)}")
        return [], []

def save_story_results(story_dir, character_data, character_image_path, story_data, story_path, 
                      scene_images, audio_paths, timestamp, date, db_path):
    """
    Save story results to a JSON file and database.
    
    Args:
        story_dir (str): Directory to save the results
        character_data (dict): Character data
        character_image_path (str): Path to the character image
        story_data (dict): Story data
        story_path (str): Path to the story file
        scene_images (list): List of paths to scene images
        audio_paths (list): List of paths to audio files
        timestamp (str): Timestamp string
        date (str): Date string
        db_path (str): Path to the database file
        
    Returns:
        tuple: (result, story_id) if successful
    """
    try:
        # Create result data
        result = {
            "character": character_data,
            "character_image": character_image_path,
            "story": story_data,
            "story_path": story_path,
            "scene_images": scene_images,
            "audio_paths": audio_paths,
            "character_data_path": getattr(character_data, '__file__', None),
            "timestamp": timestamp,
            "date": date
        }
        
        # Save the result data
        result_path = f"{story_dir}/adventure_{timestamp}.json"
        with open(result_path, 'w', encoding='utf-8') as f:
            # Convert result to a serializable format
            serializable_result = {
                "character": character_data,
                "character_image": character_image_path,
                "story": story_data,
                "story_path": story_path,
                "scene_images": scene_images,
                "audio_paths": audio_paths,
                "timestamp": timestamp,
                "date": date
            }
            json.dump(serializable_result, f, ensure_ascii=False, indent=2)
        
        # Setup database connection
        conn = setup_database(db_path)
        
        # Save to database
        story_id = save_story_to_db(
            conn,
            story_data,
            character_data,
            character_image_path,
            story_path,
            scene_images,
            audio_paths,
            timestamp,
            date
        )
        
        print(f"Adventure story with images successfully generated at: {story_dir}")
        print(f"Story saved to database with ID: {story_id}")
        
        # Close database connection
        conn.close()
        
        return result, story_id
    except Exception as e:
        print(f"Error saving story results: {str(e)}")
        return None, None

def generate_adventure_story_with_images(base_path="./output", timestamp=None, db_path=None, character_file=None):
    """
    Generate an adventure story with images for a character.

    Args:
        base_path (str): Path to save the adventure story files
        timestamp (str): Timestamp to use for file naming
        db_path (str): Path to the database file, if None will use default
        character_file (str): Path to a specific character file to use (optional)

    Returns:
        tuple: (character_data, character_image_path, story_data, story_path, scene_images, audio_paths)
    """
    # Set up the timestamp for this run if not provided
    if not timestamp:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

    # Create directory structure
    env_result = setup_story_environment(base_path, timestamp)
    if not env_result:
        logging.error("Failed to set up story environment")
        return None
    
    story_dir, character_dir, scene_dir, voice_dir, date = env_result

    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(f"{base_path}/adventure_generation_{timestamp}.log"),
        ],
    )

    try:
        logging.info("Setting up Gemini client...")
        client = setup_gemini_client()
        if not client:
            logging.error("Failed to set up Gemini client.")
            return None

        logging.info("Preparing character data...")
        char_result = prepare_character(character_file)
        if not char_result:
            logging.error("Failed to prepare character data.")
            return None
            
        # Unpack the tuple correctly
        character_data, gender, voice, character_data_path = char_result
        logging.info(f"Character data prepared: {character_data.get('name', 'Unknown')}")

        # Generate character image
        logging.info(f"Creating character image...")
        character_image_path = create_character_image(character_data, character_dir, timestamp)
        if not character_image_path or not os.path.exists(character_image_path):
            logging.warning(f"Character image could not be created")
            return None
        else:
            logging.info(f"Character image created successfully at {character_image_path}")

        # Generate adventure story
        logging.info("Generating adventure story...")
        story_data, story_path = create_adventure_story(character_data, story_dir, timestamp)
        if not story_data or not story_path:
            logging.error("Failed to generate adventure story.")
            return None

        logging.info(f"Adventure story saved to {story_path}")

        # Get voice for audio generation
        voice = get_random_voice()

        # Generate scene images and audio
        logging.info("Generating scene images and audio...")
        scene_images, audio_paths = generate_scene_images_and_audio(
            story_data, character_image_path, scene_dir, voice_dir, timestamp, voice, base_path, date
        )

        if not scene_images or not audio_paths:
            logging.error("Failed to generate scene images or audio.")
            return None

        # Save story results to database
        try:
            logging.info(f"Saving story results to database: {db_path}")
            result, story_id = save_story_results(
                story_dir, 
                character_data, 
                character_image_path, 
                story_data, 
                story_path, 
                scene_images, 
                audio_paths, 
                timestamp, 
                date, 
                db_path
            )
            if not result:
                logging.warning("Failed to save story results to database")
            else:
                logging.info(f"Story saved to database with ID: {story_id}")
                
        except Exception as db_error:
            logging.error(f"Database error: {str(db_error)}")
            logging.error("Story was not saved to the database, but files were created")

        logging.info("Adventure story generation complete!")
        logging.info(f"Character image: {character_image_path}")
        logging.info(f"Adventure data: {story_path}")
        logging.info(f"Scene images: {', '.join(scene_images)}")
        logging.info(f"Audio files: {', '.join(audio_paths)}")

        # Return result data
        return {
            'character_data': character_data,
            'character_image': character_image_path,
            'story_data': story_data,
            'story_path': story_path,
            'scene_images': scene_images,
            'audio_paths': audio_paths,
            'timestamp': timestamp,
            'date': date
        }

    except Exception as e:
        logging.error(f"Error in generate_adventure_story_with_images: {str(e)}")
        logging.error(traceback.format_exc())
        return None

def main():
    """Command-line interface for the adventure story generator."""
    parser = argparse.ArgumentParser(description='Adventure Story Generator for Alien Characters')
    parser.add_argument('--base-path', default='data',
                      help='Base path for data storage (default: data)')
    parser.add_argument('--character-file', 
                      help='Path to a specific character file to use (optional)')
    parser.add_argument('--db-path', default='story.db',
                      help='Database filename (default: story.db, saved in data folder)')
    
    args = parser.parse_args()
    
    if not os.getenv('GEMINI_API_KEY'):
        print("Error: GEMINI_API_KEY environment variable is not set.")
        print("Please set the environment variable with your Google API key.")
        return
        
    if not os.getenv('ELEVENLABS_API_KEY'):
        print("Warning: ELEVENLABS_API_KEY environment variable is not set.")
        print("Audio generation will be skipped.")
    
    # Determine the full DB path
    db_path = args.db_path
    if '/' not in db_path and '\\' not in db_path:
        db_path = os.path.join(args.base_path, db_path)
    
    result = generate_adventure_story_with_images(
        base_path=args.base_path,
        character_file=args.character_file,
        db_path=db_path
    )
    
    if result:
        date_folder = result.get('date', datetime.now().strftime('%Y%m%d'))
        print("\nAdventure story generation completed successfully!")
        print(f"Content saved to: {args.base_path}/story/{date_folder}")
        print("\nDirectory Structure:")
        print(f"└── {args.base_path}/")
        print(f"    └── story/")
        print(f"        └── {date_folder}/")
        print(f"            ├── character/    (Character images)")
        print(f"            ├── scene/        (Scene images)")
        print(f"            ├── voice/        (Audio files)")
        print(f"            └── adventure_{result['timestamp']}.json     (Adventure data)")
        
        print(f"\nGenerated Content:")
        print(f"Character Image: {result['character_image']}")
        print(f"Story File: {result['story_path']}")
        print("\nScene Images:")
        for scene in result['scene_images']:
            print(f"- {scene}")
        if 'audio_paths' in result and result['audio_paths']:
            print("\nAudio Files:")
            for audio in result['audio_paths']:
                print(f"- {audio}")
        print(f"\nStory data saved to database: {db_path}")
    else:
        print("Failed to generate adventure story.")

if __name__ == "__main__":
    main() 