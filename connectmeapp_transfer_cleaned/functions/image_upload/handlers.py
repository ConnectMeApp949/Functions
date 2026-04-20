

from firebase_functions import https_fn
from image_upload.image_upload import uploadImages_fn
from common import common_cors


@https_fn.on_request(cors=common_cors)
def uploadImages(req: https_fn.Request) -> https_fn.Response:
    return uploadImages_fn(req)

