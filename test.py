import requests
import time

BASE_URL = 'http://127.0.0.1:5000' #'https://ai-try-on-api.onrender.com'
# Replace with your Flask API URL
UPLOAD_URL = f'{BASE_URL}/upload'
STATUS_URL = f'{BASE_URL}/status'

# Paths to the images you want to upload
PERSON_IMAGE_PATH = 'a_photo_of_sj (9).jpeg'
GARMENT_IMAGE_PATH = '09164_00.jpg'

def upload_images(person_image_path, garment_image_path):
    files = {
        'personImage': open(person_image_path, 'rb'),
        'garmentImage': open(garment_image_path, 'rb'),
    }
    
    response = requests.post(UPLOAD_URL, files=files)
    return response.json()

def check_status(task_id):
    response = requests.get(f'{STATUS_URL}/{task_id}')
    print(response.json())
    return response.json()

def main():
    print("Uploading images...")
    upload_response = upload_images(PERSON_IMAGE_PATH, GARMENT_IMAGE_PATH)
    
    if 'taskId' in upload_response:
        task_id = upload_response['taskId']
        print(f'Upload successful. Task ID: {task_id}')
        
        print("Checking task status...")
        while True:
            status_response = check_status(task_id)
            status = status_response.get('status', 'Unknown')
            print(f'Task ID: {task_id}, Status: {status}')
            
            if status in ['Completed', 'Error']:
                break
            
            time.sleep(5)  # Wait before checking again

    else:
        print(f'Upload failed: {upload_response}')

if __name__ == '__main__':
    main()
