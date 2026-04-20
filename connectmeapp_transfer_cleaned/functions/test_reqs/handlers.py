from firebase_functions import https_fn
from test_reqs.services import getAllServices_fn
from test_reqs.bookings import getAllBookings_fn
from common import common_cors

@https_fn.on_request(cors=common_cors)
def getAllServices(req: https_fn.Request) -> https_fn.Response:
    return getAllServices_fn(req)

@https_fn.on_request(cors=common_cors)
def getAllBookings(req: https_fn.Request) -> https_fn.Response:
    return getAllBookings_fn(req)