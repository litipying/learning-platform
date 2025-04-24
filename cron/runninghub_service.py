import os
import json
import time
import http.client
import requests
from codecs import encode
from typing import Optional, Dict, Any, List

class RunningHubService:
    def __init__(self):
        self.api_key = os.getenv('RUNNINGHUB_API_KEY')
        self.api_url = "www.runninghub.ai"
        if not self.api_key:
            raise ValueError("RUNNINGHUB_API_KEY environment variable is not set")

    def upload_file(self, file_data: bytes, file_type: str) -> Optional[str]:
        """
        Upload a file to RunningHub.
        
        Args:
            file_data: The file data to upload
            file_type: The type of file ('image' or 'audio')
            
        Returns:
            str: The fileName from the response if successful, None otherwise
        """
        try:
            # Create connection
            conn = http.client.HTTPSConnection(self.api_url)
            
            # Create the multipart form data
            boundary = "---011000010111000001101001"
            dataList = []
            
            # Add API key
            dataList.append(encode('--' + boundary))
            dataList.append(encode('Content-Disposition: form-data; name=apiKey;'))
            dataList.append(encode('Content-Type: {}'.format('text/plain')))
            dataList.append(encode(''))
            dataList.append(encode(f"{self.api_key}"))
            
            # Add file
            dataList.append(encode('--' + boundary))
            dataList.append(encode(f'Content-Disposition: form-data; name=file; filename="file.{file_type}"'))
            dataList.append(encode('Content-Type: {}'.format(file_type)))
            dataList.append(encode(''))
            dataList.append(file_data)
            
            # Add file type
            dataList.append(encode('--' + boundary))
            dataList.append(encode('Content-Disposition: form-data; name=fileType;'))
            dataList.append(encode('Content-Type: {}'.format('text/plain')))
            dataList.append(encode(''))
            dataList.append(encode("image"))
            
            # End boundary
            dataList.append(encode('--'+boundary+'--'))
            dataList.append(encode(''))
            
            # Join all parts
            body = b'\r\n'.join(dataList)
            
            headers = {
                'Host': self.api_url,
                'Content-type': f'multipart/form-data; boundary={boundary}'
            }
            
            conn.request("POST", "/task/openapi/upload", body, headers)
            
            # Get response
            response = conn.getresponse()
            response_data = json.loads(response.read().decode("utf-8"))
            
            if response.status == 200 and response_data.get('code') == 0:
                file_name = response_data.get('data', {}).get('fileName')
                if file_name:
                    print(f"Successfully uploaded {file_type} file")
                    print(f"File name: {file_name}")
                    return file_name
                else:
                    print("No fileName in response data")
                    return None
            else:
                error_msg = response_data.get('msg', 'Unknown error')
                print(f"Error uploading {file_type} file: {response.status}")
                print(f"Error message: {error_msg}")
                return None
                
        except Exception as e:
            print(f"Error uploading {file_type} file: {str(e)}")
            print(f"Error details: {repr(e)}")
            return None

    def create_task(self, workflow_id: str, node_info_list: List[Dict[str, str]]) -> Optional[Dict[str, Any]]:
        """
        Create a task in RunningHub API.
        
        Args:
            workflow_id: The ID of the workflow to execute
            node_info_list: List of node information
            
        Returns:
            dict: Response from the API containing task details
            None: If the request fails
        """
        try:
            # Prepare the payload
            payload = {
                "apiKey": self.api_key,
                "workflowId": workflow_id,
                "nodeInfoList": node_info_list
            }

            # Create connection
            conn = http.client.HTTPSConnection(self.api_url)
            
            headers = {
                'Host': self.api_url,
                'Content-Type': 'application/json'
            }

            # Make the request
            conn.request(
                "POST",
                "/task/openapi/create",
                json.dumps(payload),
                headers
            )

            # show the request payload
            print(f"Request payload: {payload}")
            # Get response
            response = conn.getresponse()
            response_data = json.loads(response.read().decode("utf-8"))
            
            if response.status == 200 and response_data.get('code') == 0:
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
                return None

        except Exception as e:
            print(f"Error creating RunningHub task: {str(e)}")
            print(f"Error details: {repr(e)}")
            return None

    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Check the status of a RunningHub task.
        
        Args:
            task_id: The ID of the task to check
            
        Returns:
            dict: Response from the API containing status information
            None: If the request fails
        """
        try:
            # Prepare the payload
            payload = {
                "apiKey": self.api_key,
                "taskId": task_id
            }

            # Create connection
            conn = http.client.HTTPSConnection(self.api_url)
            
            headers = {
                'Host': self.api_url,
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

    def get_task_outputs(self, task_id: str) -> Optional[List[Dict[str, Any]]]:
        """
        Get the outputs of a completed RunningHub task.
        
        Args:
            task_id: The ID of the task to get outputs for
            
        Returns:
            list: List of output files with their URLs and metadata
            None: If the request fails
        """
        try:
            # Prepare the payload
            payload = {
                "apiKey": self.api_key,
                "taskId": task_id
            }

            # Create connection
            conn = http.client.HTTPSConnection(self.api_url)
            
            headers = {
                'Host': self.api_url,
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

    def wait_for_task(self, task_id: str, max_attempts: int = 100, delay_seconds: int = 10) -> Optional[Dict[str, Any]]:
        """
        Wait for a RunningHub task to complete and get its outputs.
        
        Args:
            task_id: The ID of the task to wait for
            max_attempts: Maximum number of status check attempts
            delay_seconds: Delay between status checks in seconds
            
        Returns:
            dict: Task outputs if successful
            None: If the task failed or timed out
        """
        print(f"Waiting for RunningHub task {task_id} to complete...")
        
        for attempt in range(max_attempts):
            response = self.get_task_status(task_id)
            
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
                outputs = self.get_task_outputs(task_id)
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

    def generate_video(self, image_path: str, audio_path: str, output_path: str, quality: str = "medium") -> Optional[str]:
        """
        Generate a video using RunningHub service.
        
        Args:
            image_path: Path to the image file
            audio_path: Path to the audio file
            output_path: Path where to save the output video
            quality: Video quality setting - "high", "medium", or "low" (default: "medium")
            
        Returns:
            str: Path to the generated video if successful, None otherwise
        """
        try:
            print(f"\nStarting RunningHub video generation with {quality} quality...")
            
            # Select workflow based on quality
            workflow_id = "1911463855787077633"  # Default medium quality
            if quality == "high":
                workflow_id = "1911463855787077633"  # High quality workflow
            elif quality == "low":
                workflow_id = "1911463855787077633"  # Low quality workflow
                
            # Read the files
            with open(audio_path, 'rb') as f:
                audio_data = f.read()
            with open(image_path, 'rb') as f:
                image_data = f.read()
                
            # Upload files to RunningHub
            uploaded_audio = self.upload_file(audio_data, 'audio')
            uploaded_image = self.upload_file(image_data, 'image')
            
            if not uploaded_audio or not uploaded_image:
                print("Failed to upload audio or image files")
                return None
                
            # Create RunningHub task using the uploaded file names
            create_response = self.create_task(
                workflow_id=workflow_id,
                node_info_list=[
                    {
                        "nodeId": "3",
                        "fieldName": "image",
                        "fieldValue": uploaded_image
                    },
                    {
                        "nodeId": "2",
                        "fieldName": "audio",
                        "fieldValue": uploaded_audio
                    }
                ]
            )
            
            if not create_response:
                print("Failed to create RunningHub task for video generation")
                return None
                
            task_id = create_response.get('taskId')
            if not task_id:
                print("No task ID in RunningHub response for video generation")
                return None
                
            # Wait for task completion and get outputs
            output = self.wait_for_task(task_id)
            if not output:
                print("Video generation task failed or timed out")
                return None
                
            # Get video URL from output
            video_url = output.get('fileUrl')
            if not video_url:
                print("No file URL in video generation task output")
                return None
                
            # Create videos directory if it doesn't exist
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
                
            # Download the generated video
            video_response = requests.get(video_url)
            if video_response.status_code == 200:
                # Save the video
                with open(output_path, 'wb') as f:
                    f.write(video_response.content)
                
                print(f"\n✅ Successfully generated video at: {output_path}")
                print(f"Task cost time: {output.get('taskCostTime', 'unknown')} seconds")
                return output_path
            else:
                print(f"Error downloading video: {video_response.status_code}")
                return None
                
        except Exception as e:
            print(f"\n❌ Error in RunningHub video generation:")
            print(f"Error: {str(e)}")
            return None 