import os
import requests
import json
from typing import Optional, Dict, Any

class DIDService:
    def __init__(self):
        self.api_key = os.getenv('DID_API_KEY')
        self.api_url = "https://api.d-id.com"
        if not self.api_key:
            raise ValueError("DID_API_KEY environment variable is not set")
        
        self.headers = {
            "Authorization": f"Basic {self.api_key}",
            "Content-Type": "application/json",
            "accept": "application/json"
        }

    def upload_image(self, image_path: str) -> Optional[str]:
        """
        Upload an image to D-ID.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            str: Full image URL if successful, None otherwise
        """
        try:
            # Verify the image file has a valid extension
            valid_extensions = ('.jpg', '.jpeg', '.png')
            print(f"Image path: {image_path}")
            if not any(image_path.lower().endswith(ext) for ext in valid_extensions):
                print(f"Error: Image must have one of these extensions: {valid_extensions}")
                return None
            
            # Prepare the file upload
            with open(image_path, 'rb') as image_file:
                files = {'image': image_file}
                
                # Remove Content-Type from headers for file upload
                headers = self.headers.copy()
                headers.pop("Content-Type", None)
                
                response = requests.post(
                    f"{self.api_url}/images",
                    headers=headers,
                    files=files
                )

                print(f"Upload image response: {response.text}")
                
                if response.status_code == 201:
                    response_data = response.json()
                    # Return the full URL that D-ID expects
                    return response_data.get('url')
                else:
                    print(f"Error uploading image: {response.status_code}")
                    print(f"Response: {response.text}")
                    return None
                    
        except Exception as e:
            print(f"Error uploading image: {str(e)}")
            print(f"Error details: {repr(e)}")
            return None

    def upload_audio(self, audio_path: str) -> Optional[str]:
        """
        Upload an audio file to D-ID.
        
        Args:
            audio_path: Path to the audio file
            
        Returns:
            str: Audio URL if successful, None otherwise
        """
        try:
            # Prepare the file upload
            with open(audio_path, 'rb') as audio_file:
                files = {'audio': audio_file}
                
                # Remove Content-Type from headers for file upload
                headers = self.headers.copy()
                headers.pop("Content-Type", None)
                
                response = requests.post(
                    f"{self.api_url}/audios",
                    headers=headers,
                    files=files
                )

                print(f"Response: {response.text}")
                
                if response.status_code == 201:
                    return response.json().get('url')
                else:
                    print(f"Error uploading audio: {response.status_code}")
                    print(f"Response: {response.text}")
                    return None
                    
        except Exception as e:
            print(f"Error uploading audio: {str(e)}")
            return None

    def create_talk(self, image_id: str, audio_url: Optional[str] = None, text: Optional[str] = None, voice_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Create a talking video using D-ID.
        
        Args:
            image_id: ID or URL of the uploaded image
            audio_url: URL of the uploaded audio (optional)
            text: Text to be spoken (optional)
            voice_id: ID of the voice to use for text-to-speech (optional)
            
        Returns:
            dict: Response data if successful, None otherwise
            
        Note:
            Either audio_url OR (text AND voice_id) must be provided
        """
        try:
            if not audio_url and not (text and voice_id):
                print("Error: Must provide either audio_url or both text and voice_id")
                return None
            
            # Create script based on input
            if audio_url:
                script = {
                    "type": "audio",
                    "audio_url": audio_url
                }
            else:
                script = {
                    "type": "text",
                    "input": text,
                    "provider": {
                        "type": "elevenlabs",
                        "voice_id": voice_id
                    }
                }
            
            payload = {
                "script": script,
                "config": {
                    "result_format": "mp4",
                    "fluent": True,
                    "pad_audio": "0.5",
                    "stitch": True
                },
                "source_url": image_id
            }
            
            print(f"Creating talk with payload: {json.dumps(payload, indent=2)}")
            
            response = requests.post(
                f"{self.api_url}/talks",
                headers=self.headers,
                json=payload
            )
            
            print(f"Response status: {response.status_code}")
            print(f"Response: {response.text}")
            
            if response.status_code == 201:
                return response.json()
            else:
                print(f"Error creating talk: {response.status_code}")
                print(f"Response: {response.text}")
                return None
                
        except Exception as e:
            print(f"Error creating talk: {str(e)}")
            print(f"Error details: {repr(e)}")
            return None

    def get_talk_status(self, talk_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the status of a talk.
        
        Args:
            talk_id: ID of the talk to check
            
        Returns:
            dict: Talk status if successful, None otherwise
        """
        try:
            response = requests.get(
                f"{self.api_url}/talks/{talk_id}",
                headers=self.headers
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Error getting talk status: {response.status_code}")
                print(f"Response: {response.text}")
                return None
                
        except Exception as e:
            print(f"Error getting talk status: {str(e)}")
            return None

    def generate_video(
        self,
        image_path: str,
        audio_path: Optional[str] = None,
        text: Optional[str] = None,
        voice_id: Optional[str] = None,
        output_path: str = "data/video/output.mp4",
        max_retries: int = 60,
        delay_seconds: int = 10
    ) -> Optional[str]:
        """
        Generate a video using D-ID service with either audio file or text-to-speech.
        
        Args:
            image_path: Path to the image file
            audio_path: Path to the audio file (optional)
            text: Text to be spoken (optional)
            voice_id: Voice ID for text-to-speech (optional)
            output_path: Path where to save the output video
            max_retries: Maximum number of status check attempts
            delay_seconds: Delay between status checks in seconds
            
        Returns:
            str: Path to the generated video if successful, None otherwise
            
        Note:
            Either audio_path OR (text AND voice_id) must be provided
        """
        try:
            print("\nStarting D-ID video generation...")
            
            # Validate inputs
            if not audio_path and not (text and voice_id):
                print("Error: Must provide either audio_path or both text and voice_id")
                return None
            
            # Upload image
            print("Uploading image...")
            image_url = self.upload_image(image_path)
            if not image_url:
                print("Failed to upload image")
                return None
            
            # Upload audio if provided
            audio_url = None
            if audio_path:
                print("Uploading audio...")
                audio_url = self.upload_audio(audio_path)
                if not audio_url:
                    print("Failed to upload audio")
                    return None
            
            # Create talk
            print("Creating talk...")
            talk_response = self.create_talk(image_url, audio_url, text, voice_id)
            print(f"Talk response: {talk_response}")
            if not talk_response:
                print("Failed to create talk")
                return None
            
            talk_id = talk_response.get('id')
            if not talk_id:
                print("No talk ID in response")
                return None
            
            # Wait for completion
            print("Waiting for video generation to complete...")
            import time
            for attempt in range(max_retries):
                status = self.get_talk_status(talk_id)
                print(f"Get talk status: {status}")
                if not status:
                    print(f"Failed to get status on attempt {attempt + 1}")
                    time.sleep(delay_seconds)
                    continue
                
                status_value = status.get('status', '')
                print(f"Attempt {attempt + 1}/{max_retries}: Status = {status_value}")
                
                if status_value == 'done':
                    # Get result URL and download video
                    result_url = status.get('result_url')
                    if result_url:
                        print("Video created successfully, downloading...")
                        if self.download_video(result_url, output_path):
                            print(f"Video saved to {output_path}")
                            return output_path
                        else:
                            print("Failed to download video")
                            return None
                    else:
                        print("No result URL in status")
                        return None
                
                elif status_value in ('error', 'rejected'):
                    print(f"Talk generation failed with status: {status_value}")
                    print(f"Error details: {status.get('error', 'Unknown error')}")
                    return None
                
                # For any other status (started, processing, etc.), wait and retry
                time.sleep(delay_seconds)
            
            print(f"Exceeded maximum retries ({max_retries})")
            return None
            
        except Exception as e:
            print(f"Error generating video: {str(e)}")
            print(f"Error details: {repr(e)}")
            return None

    def download_video(self, video_url: str, output_path: str) -> bool:
        """
        Download a video from the given URL.
        
        Args:
            video_url: URL of the video to download
            output_path: Path where to save the video
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Download the video
            print(f"Downloading video from {video_url}")
            response = requests.get(video_url)
            
            if response.status_code == 200:
                # Save the video
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                print(f"Video downloaded and saved to {output_path}")
                return True
            else:
                print(f"Error downloading video: {response.status_code}")
                print(f"Response: {response.text if hasattr(response, 'text') else 'No text'}")
                return False
                
        except Exception as e:
            print(f"Error downloading video: {str(e)}")
            print(f"Error details: {repr(e)}")
            return False 