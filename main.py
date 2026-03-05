# Welcome to Cloud Functions for Firebase for Python!
# To get started, simply uncomment the below code or create your own.
# Deploy with `firebase deploy`

from firebase_functions import https_fn
from firebase_admin import initialize_app, firestore
import google.cloud.firestore
from common import *


# from test_reqs.handlers import * # not ok for prod
from test_reqs.test_endpoints import * # used on prod
from auth.handlers import *
from seed.handlers import *
from booking.handlers import *
from messages.handlers import *
from services.handlers import *
from image_upload.handlers import *         
from user.handlers import *
from etc.handlers import *
from stripe_eps.handlers import *
from ratings.handlers import *
from availability.handlers import *
from payment_history.handlers import *
from static.handlers import *

@https_fn.on_request(cors=common_cors)
def on_request_example(req: https_fn.Request) -> https_fn.Response:
    return https_fn.Response("Hello world!")



