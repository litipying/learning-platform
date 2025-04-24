import os
from datetime import datetime
import argparse
import json
import base64
from main import (
    generate_alien_news,
    clean_json_response,
    generate_audio,
    generate_audio_content,
    generate_character_image,
    setup_database,
    News,
    generate_video,
    check_folders_exist
)
from sqlalchemy.orm import sessionmaker

def test_article_generation(title, description):
    """Test generating alien news from a custom title and description."""
    try:
        print("\n=== Testing Article Generation ===")
        print(f"Input Title: {title}")
        print(f"Input Description: {description}")
        
        # Generate alien news
        alien_news = generate_alien_news(title, description)
        alien_data = clean_json_response(alien_news)
        
        print("\nGenerated Content:")
        print(f"Character Name: {alien_data['character_name']}")
        print(f"Emotion: {alien_data['emotion']}")
        print(f"Alien Title: {alien_data['alien_title']}")
        print(f"Alien Content: {alien_data['alien_content']}")
        print("\nVocabulary Words:")
        for i, vocab in enumerate(alien_data['vocab'], 1):
            print(f"{i}. {vocab['word']}: {vocab['explanation']}")
        
        # Save the alien data to a temporary file for other tests to use
        with open('temp_alien_data.json', 'w') as f:
            json.dump(alien_data, f)
            print("\nSaved alien data to temp_alien_data.json for other tests to use")
        
        return alien_data
    
    except Exception as e:
        print(f"\n❌ Error in article generation:")
        print(f"Error: {str(e)}")
        print(f"Error details: {repr(e)}")
        return None

def test_audio_generation(audio_text, today, sequence_num, base_path="data", gender="male"):
    """
    Test audio generation by creating an audio file from the given text.
    
    Args:
        audio_text: Text to convert to speech
        today: Date string in YYYYMMDD format
        sequence_num: Sequence number for the file
        base_path: Base path for saving files
        gender: Voice gender to use
        
    Returns:
        str: Path to the generated audio file if successful, None otherwise
    """
    try:
        # Generate the audio
        audio_path = generate_audio(
            text=audio_text, 
            timestamp=today,  # Using today as timestamp for compatibility
            gender=gender, 
            base_path=base_path
        )
        
        if not audio_path:
            print("Failed to generate audio")
            return None
        
        # Verify the file exists
        if not os.path.exists(audio_path):
            print(f"Audio file not found at {audio_path}")
            return None
            
        print(f"Audio generated successfully at {audio_path}")
        return audio_path
    except Exception as e:
        print(f"Error in test_audio_generation: {str(e)}")
        return None

def test_image_generation(emotion="happy", base_path="data/test"):
    """Test generating character image with specific emotion."""
    try:
        print(f"\n=== Testing Image Generation ===")
        print(f"Testing emotion: {emotion}")
        
        # Generate unique filename
        today = datetime.now().strftime('%Y%m%d')
        sequence_num = 1
        
        # Ensure test folders exist
        if not check_folders_exist(today, base_path=base_path):
            print("\n❌ Failed to create test folders")
            return None

        character_name = "Zorby"
        print(f"\nGenerating image for character: {character_name}")
        print(f"Using emotion: {emotion}")
        
        # Generate image
        image_path, prompt = generate_character_image(
            character_name, 
            emotion, 
            today, 
            sequence_num,
            base_path=base_path
        )
        
        if image_path and prompt:
            print(f"\n✅ Image generated successfully at: {image_path}")
            print("\nPrompt used for generation:")
            print(prompt)
            
            # Save the image path to a temporary file for other tests to use
            with open('temp_image_path.txt', 'w') as f:
                f.write(image_path)
                print("\nSaved image path to temp_image_path.txt for other tests to use")
            return image_path
        else:
            print("\n❌ Image generation failed")
            return None
            
    except Exception as e:
        print(f"\n❌ Error in image generation:")
        print(f"Error: {str(e)}")
        print(f"Error details: {repr(e)}")
        return None

def test_video_generation(
    image_path=None,
    audio_path=None,
    text=None,
    voice_id=None,
    service="runninghub",
    base_path="data/test"
):
    """
    Test generating video using either audio file or text-to-speech.
    
    Args:
        image_path: Path to the image file (optional, will try to load from temp file)
        audio_path: Path to the audio file (optional, will try to load from temp file)
        text: Text to be spoken (optional, for D-ID text-to-speech)
        voice_id: Voice ID for text-to-speech (optional, for D-ID text-to-speech)
        service: Video service to use ('runninghub' or 'did')
        base_path: Base path for test files
    """
    try:
        print("\n=== Testing Video Generation ===")
        print(f"Using video service: {service}")
        
        # Try to load missing image path from temp file
        if image_path is None:
            try:
                with open('temp_image_path.txt', 'r') as f:
                    image_path = f.read().strip()
                print("Loaded image path from temp_image_path.txt")
            except FileNotFoundError:
                print("\n❌ No image path found. Please run image generation first.")
                return None
        
        # Verify image file exists
        if not os.path.exists(image_path):
            print(f"\n❌ Image file not found at: {image_path}")
            return None
        
        # Check if we're using text-to-speech with D-ID
        using_text_to_speech = service == "did" and text and voice_id
        
        # For RunningHub or D-ID with audio file, we need audio_path
        if service == "runninghub" or (service == "did" and not using_text_to_speech):
            # Try to load missing audio path from temp file
            if audio_path is None:
                try:
                    with open('temp_audio_path.txt', 'r') as f:
                        audio_path = f.read().strip()
                    print("Loaded audio path from temp_audio_path.txt")
                except FileNotFoundError:
                    print("\n❌ No audio path found. Please run audio generation first.")
                    return None
                    
            # Verify audio file exists
            if not os.path.exists(audio_path):
                print(f"\n❌ Audio file not found at: {audio_path}")
                return None
        
        # For D-ID with text-to-speech
        elif service == "did" and using_text_to_speech:
            if not text:
                print("\n❌ Text content is required for D-ID text-to-speech")
                return None
            if not voice_id:
                print("\n❌ Voice ID is required for D-ID text-to-speech")
                return None
        
        # Print input details
        print(f"\nUsing files and parameters:")
        print(f"- Image: {image_path}")
        if audio_path:
            print(f"- Audio: {audio_path}")
        if using_text_to_speech:
            print(f"- Text-to-speech: Enabled")
            print(f"- Text: {text[:50]}..." if len(text) > 50 else f"- Text: {text}")
            print(f"- Voice ID: {voice_id}")
        
        # Get today's date and ensure test folders exist
        today = datetime.now().strftime('%Y%m%d')
        if not check_folders_exist(today, base_path=base_path):
            print("\n❌ Failed to create test folders")
            return None
        
        # Set output path
        output_path = f"{base_path}/videos/{today}/test_video.mp4"
        
        # Generate video
        print(f"\nGenerating video using {service} service...")
        
        # For D-ID with text-to-speech
        if service == "did" and using_text_to_speech:
            video_path = generate_video(
                image_path=image_path,
                text=text,
                voice_id=voice_id,
                output_path=output_path,
                service=service
            )
        # For RunningHub or D-ID with audio file
        else:
            video_path = generate_video(
                image_path=image_path,
                audio_path=audio_path,
                output_path=output_path,
                service=service
            )
        
        if video_path and os.path.exists(video_path):
            print(f"\n✅ Video generated successfully at: {video_path}")
            print(f"Video file size: {os.path.getsize(video_path)} bytes")
            
            # Save the video path to a temporary file for other tests to use
            with open('temp_video_path.txt', 'w') as f:
                f.write(video_path)
                print("\nSaved video path to temp_video_path.txt for other tests to use")
            return video_path
        else:
            print("\n❌ Video generation failed!")
            print("Video was not generated or file does not exist")
            return None
            
    except Exception as e:
        print(f"\n❌ Error in video generation:")
        print(f"Error: {str(e)}")
        print(f"Error details: {repr(e)}")
        return None

def test_database_storage(alien_data=None, audio_path=None, image_path=None, video_path=None):
    """Test storing generated content in the database."""
    try:
        print("\n=== Testing Database Storage ===")
        
        # Try to load missing data from temp files
        if alien_data is None:
            try:
                with open('temp_alien_data.json', 'r') as f:
                    alien_data = json.load(f)
                print("Loaded alien data from temp_alien_data.json")
            except FileNotFoundError:
                print("\n❌ No alien data found. Please run article generation first.")
                return False

        if audio_path is None:
            try:
                with open('temp_audio_path.txt', 'r') as f:
                    audio_path = f.read().strip()
                print("Loaded audio path from temp_audio_path.txt")
            except FileNotFoundError:
                print("\n❌ No audio path found. Please run audio generation first.")
                return False

        if image_path is None:
            try:
                with open('temp_image_path.txt', 'r') as f:
                    image_path = f.read().strip()
                print("Loaded image path from temp_image_path.txt")
            except FileNotFoundError:
                print("\n❌ No image path found. Please run image generation first.")
                return False

        if video_path is None:
            try:
                with open('temp_video_path.txt', 'r') as f:
                    video_path = f.read().strip()
                print("Loaded video path from temp_video_path.txt")
            except FileNotFoundError:
                print("\n❌ No video path found. Please run video generation first.")
                return False
        
        # Setup database connection
        print("\nSetting up database connection...")
        engine = setup_database()
        Session = sessionmaker(bind=engine)
        session = Session()
        
        try:
            # Create news entry
            print("\nCreating news entry...")
            news = News(
                original_title="Test Title",
                original_content="Test Content",
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
            session.commit()
            print("\n✅ Successfully stored test data in database")
            return True
            
        except Exception as e:
            print(f"\n❌ Error storing data in database:")
            print(f"Error: {str(e)}")
            session.rollback()
            return False
            
        finally:
            session.close()
            print("\nDatabase connection closed")
            
    except Exception as e:
        print(f"\n❌ Error in test execution:")
        print(f"Error: {str(e)}")
        return False

def main():
    """Main function to run the tests."""
    parser = argparse.ArgumentParser(description='Test Alien News Generator functions')
    parser.add_argument('--function', choices=['article', 'audio', 'image', 'video', 'database', 'all'],
                      help='Which function to test: article, audio, image, video, database, or all')
    parser.add_argument('--title', type=str, default='SpaceX launches new rocket',
                      help='Article title for testing')
    parser.add_argument('--description', type=str, 
                      default='SpaceX successfully launched its latest rocket from Florida, heading to the ISS.',
                      help='Article description for testing')
    parser.add_argument('--emotion', type=str, default='happy',
                      help='Emotion for character generation (e.g., happy, sad, surprised)')
    parser.add_argument('--service', type=str, choices=['runninghub', 'did'], default='runninghub',
                      help='Video generation service to use')
    parser.add_argument('--base-path', type=str, default='data/test',
                      help='Base path for storing test files')
    parser.add_argument('--text-to-speech', action='store_true',
                      help='Use text-to-speech instead of pre-generated audio (only for D-ID)')
    parser.add_argument('--text', type=str,
                      help='Direct text input for text-to-speech (only for D-ID)')
    parser.add_argument('--voice-id', type=str, default='en-US-JennyNeural',
                      help='Voice ID for text-to-speech (only for D-ID)')
    
    args = parser.parse_args()
    
    if args.function == 'all':
        print("\n🚀 Running all tests in sequence...\n")
    
    alien_data = None
    audio_path = None
    audio_text = None
    image_path = None
    video_path = None
    
    # Set text-to-speech flag if direct text is provided
    if args.text and args.service == "did":
        args.text_to_speech = True
        audio_text = args.text
        if len(audio_text) > 50:
            print(f"\nUsing direct text input for text-to-speech: '{audio_text[:50]}...'")
        else:
            print(f"\nUsing direct text input for text-to-speech: '{audio_text}'")
    
    # Test article generation
    if args.function in ['article', 'all']:
        alien_data = test_article_generation(args.title, args.description)
        if not alien_data and args.function == 'all':
            print("\n❌ Article generation failed, stopping tests")
            return
    
    # Test audio generation and get text if needed for TTS
    if args.function in ['audio', 'all'] or (args.text_to_speech and not args.text and args.function in ['video', 'all']):
        if alien_data or args.function in ['all', 'audio']:
            if args.text_to_speech and not args.text:
                # Just generate the text content without creating the audio file
                print("\n=== Generating Speech Text ===")
                try:
                    # Try to load alien data if not already loaded
                    if not alien_data:
                        try:
                            with open('temp_alien_data.json', 'r') as f:
                                alien_data = json.load(f)
                            print("Loaded alien data from temp_alien_data.json")
                        except FileNotFoundError:
                            print("\n❌ No alien data found. Please run article generation first.")
                            return
                    
                    # Generate the text content
                    audio_text = generate_audio_content(
                        alien_data['alien_title'],
                        alien_data['alien_content'],
                        alien_data['vocab']
                    )
                    print("Successfully generated speech text")
                except Exception as e:
                    print(f"\n❌ Error generating speech text: {str(e)}")
                    return
            
            # Only generate audio file if not using text-to-speech
            if not args.text_to_speech:
                audio_path = test_audio_generation(audio_text, datetime.now().strftime('%Y%m%d'), 1, base_path=args.base_path)
                if not audio_path and args.function == 'all':
                    print("\n❌ Audio generation failed, stopping tests")
                    return
    
    # Test image generation
    if args.function in ['image', 'all']:
        image_path = test_image_generation(args.emotion, base_path=args.base_path)
        if not image_path and args.function == 'all':
            print("\n❌ Image generation failed, stopping tests")
            return
    
    # Test video generation
    if args.function in ['video', 'all']:
        if args.service == "did" and args.text_to_speech:
            if not audio_text:
                print("\n❌ No audio text available. Please run article generation first or provide text directly with --text.")
                return
            video_path = test_video_generation(
                image_path=image_path, 
                text=audio_text,
                voice_id=args.voice_id,
                service=args.service, 
                base_path=args.base_path
            )
        else:
            video_path = test_video_generation(
                image_path=image_path, 
                audio_path=audio_path,
                service=args.service, 
                base_path=args.base_path
            )
        if not video_path and args.function == 'all':
            print("\n❌ Video generation failed, stopping tests")
            return
    
    # Test database storage
    if args.function in ['database', 'all']:
        test_database_storage(alien_data, audio_path, image_path, video_path)
    
    if args.function == 'all':
        print("\n✅ All tests completed successfully!")

if __name__ == "__main__":
    main() 