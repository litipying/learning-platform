from runninghub_service import RunningHubService
import requests
import os

def generate_character_image(character_name, emotion, today, sequence_num, base_path="data"):
    """
    Generate a hyper-realistic portrait of the alien character with the specified emotion using RunningHub API.
    
    Args:
        character_name: Name of the alien character
        emotion: Emotional state of the character
        today: Date string in YYYYMMDD format
        sequence_num: Sequence number for the image
        base_path: Base path for saving files
        
    Returns:
        tuple: (image_path, prompt) if successful, (None, None) if failed
            - image_path (str): Path to the generated image
            - prompt (str): The prompt used to generate the image
    """
    try:

        # Initialize RunningHub service
        runninghub_service = RunningHubService()

        lora_names = ["mpeachv6.safetensors","taylorswift.safetensors"]
        lora_name = lora_names[1]

        print(f"Lora name: {lora_name}")

        # Create RunningHub task
        node_info_list = [
            {
                "nodeId": "28",
                "fieldName": "lora_name",
                "fieldValue": lora_name
            }
        ]

        print(f"RunningHub task data: {node_info_list}")

        # Create task and get task ID
        task_data = runninghub_service.create_task(
            workflow_id="1914854282569445377",  # Workflow ID for image generation
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
            # Create images directory if it doesn't exist
            os.makedirs(f"{base_path}/images/{today}", exist_ok=True)
            
            # Save the image
            image_path = f"{base_path}/test/images/{today}/{today}_{sequence_num}.png"
            with open(image_path, 'wb') as f:
                f.write(image_response.content)
            
            print(f"Successfully generated image at: {image_path}")
            return image_path
        else:
            print(f"Error downloading image: {image_response.status_code}")
            return None, None
            
    except Exception as e:
        print(f"Error generating image: {str(e)}")
        print(f"Error details: {repr(e)}")
        return None, None
    

if __name__ == "__main__":
    generate_character_image("alien", "happy", "20250423", 1, "data") 