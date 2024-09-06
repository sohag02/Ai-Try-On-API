import os
import threading
import uuid
import json
import redis
from dotenv import load_dotenv
from flask import Flask, jsonify, request, url_for
from gradio_client import Client, handle_file
from werkzeug.utils import secure_filename

from utils import get_base_url, move_to_result_folder

load_dotenv()

app = Flask(__name__)

app.config['APPLICATION_ROOT'] = '/'
app.config['PREFERRED_URL_SCHEME'] = 'http'


redis_client = redis.Redis(
    host=os.environ.get('REDIS_HOST'),
    port=int(os.environ.get('REDIS_PORT')),
    password=os.environ.get('REDIS_PASSWORD'),
    ssl=bool(os.environ.get('REDIS_SSL'))
)

UPLOAD_FOLDER = 'tmp'
RESULT_FOLDER = 'static/results'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

# Ensure the upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.before_request
def setup():
    app.before_request_funcs[None].remove(setup)
    app.config['SERVER_NAME'] = get_base_url(request.base_url)
    # Check DB
    res = redis_client.ping()
    if res:
        print("Redis is connected")


@app.route('/')
def working():
    return jsonify({'status': 'Working'})


@app.route('/upload', methods=['POST'])
def upload_images():
    if 'personImage' not in request.files or 'garmentImage' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    person_image = request.files['personImage']
    garment_image = request.files['garmentImage']

    if person_image.filename == '' or garment_image.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if person_image and allowed_file(person_image.filename) and garment_image and allowed_file(garment_image.filename):
        task_id = str(uuid.uuid4())  # Generate a unique task ID
        person_image_path = os.path.join(
            UPLOAD_FOLDER, secure_filename(person_image.filename))
        garment_image_path = os.path.join(
            UPLOAD_FOLDER, secure_filename(garment_image.filename))

        person_image.save(person_image_path)
        garment_image.save(garment_image_path)

        # Initialize task status in Redis
        data = {
            'status': 'Processing'
        }
        redis_client.set(task_id, json.dumps(data))

        # Process the images asynchronously
        process_images_async(task_id, person_image_path, garment_image_path)

        return jsonify({'taskId': task_id})

    return jsonify({'error': 'Invalid file format'}), 400


@app.route('/status/<task_id>', methods=['GET'])
def get_status(task_id):
    if status := redis_client.get(task_id):
        data = json.loads(status.decode('utf-8'))
        return jsonify(data)
    return jsonify({'status': 'Task not found'}), 404


def process_images_async(task_id, person_image_path, garment_image_path):
    def process():
        try:
            # Update task status
            data = {
                'status': 'Processing'
            }
            redis_client.set(task_id, json.dumps(data))

            # Replace with your actual image processing logic
            result_image_path, error = process_virtual_try_on(
                person_image_path, garment_image_path)

            # Simulate task completion
            if result_image_path:
                data = {
                    'status': 'Completed',
                    'url': result_image_path
                }
                redis_client.set(task_id, json.dumps(data))
            else:
                data = {
                    'status': 'Error',
                    'error': f'Image processing failed : {error}'
                }
                redis_client.set(task_id, json.dumps(data))

            # Delete the temporary files
            os.remove(person_image_path)
            os.remove(garment_image_path)

        except Exception as e:
            print(e)
            data = {
                'status': 'Error',
                'error': str(e.__class__.__name__)
            }
            redis_client.set(task_id, json.dumps(data))

    # Run the processing in a separate thread
    thread = threading.Thread(target=process)
    thread.start()


def process_virtual_try_on(person_image_path, garment_image_path):
    try:
        client = Client("yisol/IDM-VTON", )
        result = client.predict(
            dict={"background": handle_file(
                person_image_path), "layers": [], "composite": None},
            garm_img=handle_file(garment_image_path),
            garment_des="Hello!!",
            is_checked=True,
            is_checked_crop=False,
            denoise_steps=30,
            seed=42,
            api_name="/tryon",
        )
        path = move_to_result_folder(result, RESULT_FOLDER)
        with app.app_context():
            url = url_for('static', filename=path.replace('static/', '', 1))
        return url, None
    except Exception as e:
        print(e)
        return None, str(e.__class__.__name__)


if __name__ == '__main__':
    app.run(host='0.0.0.0')
