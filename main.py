import datetime
import os
import pathlib
from threading import Thread
from logging import info, basicConfig, DEBUG

from flask import Flask, jsonify
from flask import request as flask_request
from flask_cors import CORS

from src.backend import Backend
from src.filter_manager import FilterManager
from src.local_storage import LocalStorage
from src.queue import Queue

log_dir = os.path.join(pathlib.Path().resolve(), "logs")
pathlib.Path(log_dir).mkdir(parents=True, exist_ok=True)
log_file = os.path.join(log_dir, f"log_file-{datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}.log")
print(f"Logging to {log_file}")

basicConfig(filename=log_file, encoding='utf-8', level=DEBUG)
tmp_folder_path = os.path.join(pathlib.Path().resolve(), "tmp")
filters_folder_path = os.path.join(pathlib.Path().resolve(), "ai_filters", "Style_GAN", "images")
pathlib.Path(tmp_folder_path).mkdir(parents=True, exist_ok=True)
info(msg=f"tmp folder path: {tmp_folder_path}")
info(msg=f"filters folder path: {filters_folder_path}")

info(msg="Creating LocalStorage")
storage = LocalStorage(tmp_folder_path=tmp_folder_path, filters_folder_path=filters_folder_path)
info(msg="Creating Queue")
queue = Queue()

filter_manager = FilterManager(storage=storage, queue=queue)
filter_manager.import_filters()
filter_manager.run()
backend = Backend(storage=storage, queue=queue)

app = Flask(__name__)

# enable CORS
CORS(app)


@app.route('/ping')
def ping():
    return jsonify(success=True)


@app.route('/get_size', methods=["POST"])
def get_image_size():
    w, h = backend.get_image(flask_request_local=flask_request)
    return jsonify(w=w, h=h)


@app.route('/get_last_saved', methods=["GET"])
def get_last_saved_image():
    path = backend.get_last_saved_image()
    if path:
        return jsonify(error="NO", path=path)
    return jsonify(error="YES")


@app.route('/', methods=["POST"])
def get_image():
    path, output_image_id = backend.get_image(flask_request_local=flask_request)

    # Thread(target=lambda: backend.delete_image(image_id=output_image_id)).start()

    return jsonify(path=path)
    # return path


@app.route('/save_image', methods=["POST"])
def save_image():
    return jsonify(success=backend.save_image(flask_request_local=flask_request))


app.run(host='localhost', port=5000, threaded=True, processes=1, debug=False)
