from firebase_functions import https_fn
from firebase_admin import initialize_app, storage
from flask import Request
import uuid
import base64
import time   
from settings import *
from auth.auth_user_wrapper import uauth
import traceback

import re

MAX_IMAGE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB per image
MAX_IMAGES_PER_REQUEST = 10
ALLOWED_FILENAME_PATTERN = re.compile(r'^[a-zA-Z0-9_\-/]+\.(jpg|jpeg|png|gif|webp)$')

@uauth
@https_fn.on_request()
def uploadImages_fn(req: Request):
    try:
        if req.method != 'POST':
            return ("Method not allowed", 405)

        pdata = req.get_json()

        if "image_data" not in pdata:
            return jsonify({"success": False, "error": "couldn't read image data"}), 400

        image_data = pdata["image_data"]

        # Limit number of images per request
        if len(image_data) > MAX_IMAGES_PER_REQUEST:
            return jsonify({"success": False, "error": f"Max {MAX_IMAGES_PER_REQUEST} images per request"}), 400

        download_urls = []
        bucket = storage.bucket()
        for filename_key, imagedata_base64_value in image_data.items():
            # Validate filename to prevent path traversal
            if not ALLOWED_FILENAME_PATTERN.match(filename_key):
                return jsonify({"success": False, "error": f"Invalid filename: {filename_key}"}), 400
            if '..' in filename_key:
                return jsonify({"success": False, "error": "Invalid filename"}), 400

            lg.t("upload image ~ " + str(filename_key))
            imagedata_bytes = base64.b64decode(imagedata_base64_value)

            # Validate file size
            if len(imagedata_bytes) > MAX_IMAGE_SIZE_BYTES:
                return jsonify({"success": False, "error": f"Image too large (max {MAX_IMAGE_SIZE_BYTES // (1024*1024)}MB)"}), 400

            # Validate image content type by checking magic bytes
            content_type = "image/jpeg"
            if imagedata_bytes[:8] == b'\x89PNG\r\n\x1a\n':
                content_type = "image/png"
            elif imagedata_bytes[:4] == b'RIFF' and imagedata_bytes[8:12] == b'WEBP':
                content_type = "image/webp"
            elif imagedata_bytes[:3] == b'GIF':
                content_type = "image/gif"
            elif imagedata_bytes[:2] not in (b'\xff\xd8',):
                return jsonify({"success": False, "error": "Invalid image format"}), 400

            blob = bucket.blob(filename_key)
            blob.upload_from_string(imagedata_bytes, content_type=content_type)

            for _ in range(10):
                try:
                    blob.reload()
                    blob.make_public()
                    download_urls.append(blob.public_url)  # Fixed: append on success, not failure
                    break
                except Exception as e:
                    time.sleep(0.5)

        response = {"success": True,
                    "download_urls": download_urls
                    }

        return response
    except Exception as e:
        lg.e("Exp ~ " + str(e))
        if debug_responses:
            return jsonify({'success': False, 'error': str(e)}), 500
        else:
            return std_exception_response()