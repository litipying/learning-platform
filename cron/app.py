import streamlit as st
import streamlit.components.v1 as components
import base64
import os
import sys
import glob
import random
from io import BytesIO
from PIL import Image
from datetime import datetime
import pytz
import uuid
import re

from main import (
    get_news,
    generate_alien_news,
    generate_audio_content,
    generate_audio,
    generate_character_image,
    generate_video,
    clean_json_response,
    check_folders_exist,
    save_news_text,
    get_random_character_attributes,
    get_random_voice,
    get_random_character_file,
    setup_database
)

# Import story generator functions
from story import (
    generate_adventure_story_with_images,
    setup_story_environment,
    prepare_character,
    create_character_image,
    create_adventure_story,
    generate_scene_images_and_audio,
    save_story_results
)

# Set base path for demo
base_path = "data/demo"

# Helper functions
def sanitize_filename(text):
    """
    Sanitize a string to be used as a filename
    Removes special characters and limits length
    """
    # Replace special characters with underscores
    text = re.sub(r'[^\w\s-]', '_', text)
    # Replace multiple spaces with a single underscore
    text = re.sub(r'\s+', '_', text)
    # Limit length to avoid filesystem issues
    return text[:50]

# Main app layout with tabs
st.title("🚀 Alien Story Generator Demo")

# Create tabs
tab1, tab2 = st.tabs(["Alien News Generator", "Alien Story Generator"])

with tab1:
    st.markdown("### Alien News Demo Process Visualization")
    
    # Add description
    st.markdown("""
    This demo shows how the Alien News Generator processes Earth news into child-friendly alien content.
    Each step is visualized, from fetching news to generating the final video content.
    All demo files are saved in a separate demo directory and results are inserted into the database.
    """)
    
    # Add number input for article count
    num_articles = st.number_input(
        "Number of news articles to process",
        min_value=1,
        max_value=3,
        value=1,
        help="Select how many news articles you want to process (1-3)"
    )
    
    # Add video service selector
    video_service = st.selectbox(
        "Select video generation service",
        options=["did", "runninghub"],
        help="Choose which service to use for video generation"
    )
    
    # Add quality selector for RunningHub
    video_quality = "medium"
    if video_service == "runninghub":
        video_quality = st.selectbox(
            "Select video quality",
            options=["low", "medium", "high"],
            index=1,  # Default to medium
            help="Choose the quality level for RunningHub video generation. Higher quality takes longer."
        )
    
    # Add image service selector
    image_service = st.selectbox(
        "Select image generation service",
        options=["gemini", "runninghub"],
        help="Choose which service to use for image generation"
    )
    
    if image_service == "gemini" and not os.getenv('GEMINI_API_KEY'):
        st.warning("Gemini image service requires GEMINI_API_KEY environment variable to be set. Falling back to RunningHub.")
        image_service = "runninghub"
    
    # Always use predefined character files (removed the checkbox)
    use_character_file = True
    
    # Add text-to-speech option for D-ID
    use_text_to_speech = False
    voice_id = None
    if video_service == "did":
        use_text_to_speech = st.checkbox(
            "Use text-to-speech instead of generated audio",
            value=True,
            help="When enabled, D-ID will generate speech from text instead of using the pre-generated audio"
        )
    
    # Button to generate demo content
    if st.button("🎬 Generate Demo News"):
        st.write("Starting demo news generation...")
        
        # Create a placeholder for the progress bar
        progress_bar = st.progress(0)
        
        # Get today's date string
        hk_tz = pytz.timezone('Asia/Hong_Kong')
        today = datetime.now(hk_tz).strftime('%Y%m%d')
        
        try:
            # Setup database connection for storing results
            engine = setup_database()
            from sqlalchemy.orm import sessionmaker
            Session = sessionmaker(bind=engine)
            db_session = Session()
            
            # Step 1: Create folders
            if not check_folders_exist(today, base_path=base_path):
                st.error("❌ Failed to create demo folders")
                st.stop()
            st.success("✅ Created demo folders")
            progress_bar.progress(10)
    
            # Step 2: Fetch news articles
            articles = get_news(num_articles=num_articles)
            print(f"Fetched {len(articles)} articles")
            print(f"Articles: {articles}")
            if not articles:
                st.error("❌ No news articles found")
                st.stop()
            
            st.success(f"✅ Fetched {len(articles)} news articles")
            progress_bar.progress(20)
            
            # Display fetched articles
            with st.expander("View Original News Articles"):
                for idx, article in enumerate(articles, 1):
                    st.write(f"Article {idx}:")
                    st.write(f"Title: {article['title']}")
                    st.write(f"Description: {article['description']}")
                    st.write("---")
    
            # Process each article
            for i, article in enumerate(articles, 1):
                st.markdown(f"### Processing Demo Article {i}")
                
                # Generate timestamp in YYYYMMDDhhmmss format
                timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                # Add a random suffix to avoid collisions
                timestamp = f"{timestamp}_{uuid.uuid4().hex[:6]}"
                date = timestamp[:8]  # Extract date part for folder structure
                
                # Use random gender for internal use
                gender = random.choice(["male", "female"])
                
                # Generate alien news
                with st.spinner(f"Creating alien version of article {i}..."):
                    alien_news_response = generate_alien_news(article['title'], article['description'])
                    alien_data = clean_json_response(alien_news_response)
                    save_news_text(alien_data, timestamp, base_path=base_path, gender=gender)
                    
                    st.success("✅ Created alien version")
                    with st.expander("View Alien News Details"):
                        st.json(alien_data)
                
                # Generate audio content text
                with st.spinner("Generating speech script..."):
                    audio_text = generate_audio_content(
                        alien_data['alien_title'],
                        alien_data['alien_content'],
                        alien_data['vocab']
                    )
                    st.success("✅ Generated speech script")
    
                    with st.expander("View speech script"):
                        st.write(audio_text)
                
                # Generate audio file only if not using text-to-speech
                audio_path = None
                if not (video_service == "did" and use_text_to_speech):
                    with st.spinner("Generating alien voice..."):
                        audio_path = generate_audio(
                            text=audio_text, 
                            timestamp=timestamp, 
                            gender=gender,
                            base_path=base_path
                        )
                        if audio_path:
                            st.success("✅ Generated audio")
                            st.audio(audio_path)
                        else:
                            st.error("❌ Failed to generate audio")
                            st.stop()
                
                # Generate image
                with st.spinner("Creating alien character..."):
                    image_result = generate_character_image(
                        alien_data['character_name'],
                        alien_data['emotion'],
                        timestamp,
                        gender=gender,
                        base_path=base_path,
                        use_character_file=use_character_file,
                        service=image_service
                    )
                    
                    # Handle the returned value properly based on service
                    if image_result:
                        if isinstance(image_result, tuple) and len(image_result) >= 1:
                            image_path = image_result[0]
                            prompt = image_result[1] if len(image_result) > 1 else None
                        else:
                            image_path = image_result
                            prompt = None
                        
                        if image_path and os.path.exists(image_path):
                            st.success("✅ Generated character image")
                            # Display the prompt in an expander if available
                            if prompt:
                                with st.expander("View Character Generation Prompt"):
                                    st.text(prompt)
                            else:
                                # If prompt is not available directly, create one for display purposes
                                display_prompt = f"""A captivating and hyper-realistic portrait of a cute and friendly humanoid alien journalist named {alien_data['character_name']}, clearly the central focus of the image, sitting confidently in a bright and modern news studio setting.

The alien displays a warm and inviting smile, with an overall {alien_data['emotion']} expression that is appealing to children.

The background showcases a bright and tidy news studio, visible but intentionally out of focus to keep the alien as the primary subject. The scene includes subtle elements like digital news screens displaying graphics, soft studio lights casting a clean white illumination, and a portion of a news desk.

The lighting is soft and even, ensuring a bright and well-lit composition. The entire scene communicates a sense of professionalism and approachability."""
                                
                                with st.expander("View Character Generation Prompt"):
                                    st.text(display_prompt)
                                    
                            st.image(image_path, use_container_width=True)
                        else:
                            st.error(f"❌ Image file not found at: {image_path}")
                            st.stop()
                    else:
                        st.error("❌ Failed to generate character image")
                        st.stop()
                
                # Generate video
                with st.spinner(f"Creating final video using {video_service}..."):
                    # Create output directory
                    os.makedirs(f"{base_path}/videos/{date}", exist_ok=True)
                    video_output_path = f"{base_path}/videos/{date}/alien_news_{timestamp}.mp4"
                    
                    try:
                        # For D-ID with text-to-speech
                        if video_service == "did" and use_text_to_speech:
                            # Get a random voice based on gender
                            voice = get_random_voice(gender)
                            selected_voice_id = voice["id"]
                            st.info(f"Using random voice: {voice.get('name', 'Unknown')}")
                            
                            st.info("Generating video with text-to-speech...")
                            video_path = generate_video(
                                image_path=image_path,
                                text=audio_text,
                                voice_id=selected_voice_id,
                                output_path=video_output_path,
                                service=video_service
                            )
                        # For RunningHub or D-ID with audio file
                        else:
                            if not audio_path:
                                st.error("❌ Audio file is required but not available")
                                st.stop()
                                
                            st.info("Generating video with pre-generated audio...")
                            if video_service == "runninghub":
                                video_path = generate_video(
                                    image_path=image_path,
                                    audio_path=audio_path,
                                    output_path=video_output_path,
                                    service=video_service,
                                    quality=video_quality
                                )
                            else:
                                video_path = generate_video(
                                    image_path=image_path,
                                    audio_path=audio_path,
                                    output_path=video_output_path,
                                    service=video_service
                                )
                            
                        if video_path and os.path.exists(video_path):
                            st.success("✅ Generated video")
                            st.video(video_path)
                            
                            # Create database entry and save to database
                            from main import News
                            try:
                                news_entry = News(
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
                                db_session.add(news_entry)
                                db_session.commit()
                                st.success("✅ Saved to database")
                            except Exception as db_error:
                                st.warning(f"⚠️ Database insertion warning: {str(db_error)}")
                                db_session.rollback()
                        else:
                            st.error(f"❌ Video file not found at expected path: {video_path}")
                            st.stop()
                    except Exception as e:
                        st.error(f"❌ Error generating video: {str(e)}")
                        st.stop()
                
                progress_bar.progress(20 + (80 * i // len(articles)))
                st.markdown("---")
    
            # Final success message
            progress_bar.progress(100)
            st.success("🎉 Demo completed successfully!")
            st.info("All demo files have been saved in the data/demo directory and database records created")
            
            # Close database session
            db_session.close()
            
        except Exception as e:
            st.error(f"❌ Error during demo: {str(e)}")
            # Ensure database session is closed in case of error
            if 'db_session' in locals():
                db_session.close()
            st.stop()

with tab2:
    st.markdown("### Alien Adventure Story Generator")
    
    st.markdown("""
    This demo creates original adventure stories featuring alien characters.
    The process includes:
    1. Generating a unique alien character (or using a predefined one)
    2. Creating an adventure story with multiple scenes
    3. Generating images for each scene
    4. Creating audio narration for the scenes
    
    All story content is saved in the demo directory and inserted into the story database automatically.
    """)
    
    # Check API keys availability
    gemini_available = os.getenv('GEMINI_API_KEY') is not None
    elevenlabs_available = os.getenv('ELEVENLABS_API_KEY') is not None
    
    if not gemini_available:
        st.error("❌ GEMINI_API_KEY environment variable is not set. Story generation requires this API key.")
    
    if not elevenlabs_available:
        st.warning("⚠️ ELEVENLABS_API_KEY environment variable is not set. Audio narration will be skipped.")
    
    # Always use predefined characters (removed the checkbox)
    use_predefined_character = True
    
    # Set character_file to None to use random selection
    character_file = None
    
    # Button to generate story
    if st.button("🚀 Generate Adventure Story"):
        if not gemini_available:
            st.error("Cannot generate story without Gemini API key")
            st.stop()
            
        st.write("Starting adventure story generation...")
        progress_bar = st.progress(0)
        
        try:
            # Set paths for demo
            story_base_path = f"{base_path}/story"
            db_path = f"data/story.db"
            
            # Generate timestamp for unique filenames
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            
            # Step 1: Set up environment
            with st.spinner("Setting up story environment..."):
                env_result = setup_story_environment(story_base_path, timestamp)
                if not env_result:
                    st.error("❌ Failed to set up story environment")
                    st.stop()
                story_dir, character_dir, scene_dir, voice_dir, date = env_result
                st.success("✅ Created story directories")
                progress_bar.progress(10)
            
            # Step 2: Prepare character
            with st.spinner("Preparing character..."):
                # If using predefined character, get the file path
                if use_predefined_character:
                    # Get a list of all character files
                    character_files = glob.glob("resource/characters/*.yaml")
                    character_files.extend(glob.glob("resource/characters/*.yml"))
                    
                    if character_files:
                        # Select a random file
                        random_character_file = random.choice(character_files)
                        if random_character_file:
                            try:
                                with open(random_character_file, 'r') as f:
                                    character_yaml = f.read()
                                st.success(f"✅ Selected character: {os.path.basename(random_character_file)}")
                                with st.expander("View character data"):
                                    st.code(character_yaml, language="yaml")
                                character_file = random_character_file
                            except Exception as e:
                                st.warning(f"Could not read character file: {str(e)}")
                
                # Use the prepare_character function
                char_result = prepare_character(character_file)
                if not char_result:
                    st.error("❌ Failed to prepare character")
                    st.stop()
                character_data, gender, voice, character_data_path = char_result
                
                st.success(f"✅ Prepared character: {character_data.get('name', 'Unnamed')} ({gender})")
                progress_bar.progress(20)
            
            # Step 3: Create character image
            with st.spinner("Generating character image..."):
                # Get the character prompt first to display it
                name = character_data.get('name', 'Alien Character')
                appearance = character_data.get('appearance', 'A humanoid alien with unique features')
                personality = character_data.get('personality', 'Friendly and curious')
                
                character_prompt = f"""Reference image to be used as a style guide, create a detailed, high-quality portrait image of an alien character named {name} from another planet.

Physical appearance: {appearance}

Personality: {personality}

The alien should be shown against a space-themed or alien world background that highlights their otherworldly features.
Make the image colorful, child-friendly, and expressive. The image should be detailed enough to see the character's unique alien features and convey their personality.
Include subtle elements that suggest their alien origin such as unusual skin textures, non-human anatomical features, or cosmic elements.
"""
                
                character_image_path = create_character_image(character_data, character_dir, timestamp)
                if not character_image_path:
                    st.error("❌ Failed to generate character image")
                    st.stop()
                
                st.success("✅ Generated character image")
                
                # Display the character generation prompt in an expander
                with st.expander("View Character Generation Prompt"):
                    st.text(character_prompt)
                    
                st.image(character_image_path, use_container_width=True)
                progress_bar.progress(40)
            
            # Step 4: Create adventure story
            with st.spinner("Creating adventure story..."):
                story_result = create_adventure_story(character_data, story_dir, timestamp)
                if not story_result:
                    st.error("❌ Failed to generate adventure story")
                    st.stop()
                story_data, story_path = story_result
                
                st.success(f"✅ Created adventure story: {story_data.get('title', 'Untitled')}")
                st.subheader(story_data.get('title', 'Untitled'))
                with st.expander("View story", expanded=True):
                    st.markdown(story_data.get('story', ''))
                st.markdown("### Story Moral")
                st.markdown(f"*{story_data.get('moral', '')}*")
                progress_bar.progress(60)
            
            # Step 5: Generate scene images and audio
            with st.spinner("Generating scene images and audio..."):
                scene_images, audio_paths = generate_scene_images_and_audio(
                    story_data, character_image_path, scene_dir, voice_dir, 
                    timestamp, voice, story_base_path, date
                )
                
                st.success(f"✅ Generated {len(scene_images)} scene images and {len([a for a in audio_paths if a])} audio narrations")
                progress_bar.progress(80)
                
                # Display scene images and audio in tabs
                st.markdown("### Story Scenes")
                scene_tabs = st.tabs([f"Scene {i+1}" for i in range(len(scene_images))])
                
                for i, (tab, image_path) in enumerate(zip(scene_tabs, scene_images), 1):
                    with tab:
                        col1, col2 = st.columns([3, 2])
                        
                        with col1:
                            if os.path.exists(image_path):
                                st.image(image_path, use_container_width=True)
                            else:
                                st.error(f"Scene {i} image not found")
                        
                        with col2:
                            scene_key = f"scene{i}_story"
                            if scene_key in story_data:
                                st.markdown("#### Narration")
                                st.info(story_data[scene_key])
                                
                                # Display audio if available
                                audio_path = audio_paths[i-1] if i <= len(audio_paths) else None
                                if audio_path and os.path.exists(audio_path):
                                    st.markdown("#### Listen")
                                    st.audio(audio_path)
                                elif audio_path:
                                    st.warning(f"Audio file not found")
                            else:
                                st.warning(f"No narration text found for scene {i}")
            
            # Step 6: Save results
            with st.spinner("Saving story data..."):
                result, story_id = save_story_results(
                    story_dir, character_data, character_image_path, story_data, story_path,
                    scene_images, audio_paths, timestamp, date, db_path
                )
                
                if not result:
                    st.warning("⚠️ Failed to save story results, but generation completed")
                else:
                    st.success(f"✅ Saved story data (ID: {story_id})")
                
                progress_bar.progress(100)
                st.success("🎉 Adventure story generation completed!")
                st.info(f"Content saved to: {story_base_path}/story/{date}")
                
        except Exception as e:
            st.error(f"❌ Error during story generation: {str(e)}")
            import traceback
            st.code(traceback.format_exc())
            st.stop()