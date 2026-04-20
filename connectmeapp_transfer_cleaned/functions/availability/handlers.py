from firebase_functions import https_fn
from availability.get_availability import getBaseAvailability_fn
from availability.set_availability import setBaseAvailability_fn
from common import common_cors


@https_fn.on_request(cors=common_cors)
def getBaseAvailability(req: https_fn.Request) -> https_fn.Response:
    return getBaseAvailability_fn(req)

@https_fn.on_request(cors=common_cors)
def setBaseAvailability(req: https_fn.Request) -> https_fn.Response:
    return setBaseAvailability_fn(req)