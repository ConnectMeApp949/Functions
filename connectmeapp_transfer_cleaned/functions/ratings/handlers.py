from firebase_functions import https_fn
from common import common_cors
from ratings.get_ratings import getRatings_fn, getVendorRatings_fn, getVendorRatingsAgg_fn
from ratings.create_rating import createRating_fn
from ratings.get_ratings_for_service import getRatingsForService_fn


@https_fn.on_request(cors=common_cors)
def getRatings(req: https_fn.Request) -> https_fn.Response:
    return getRatings_fn(req)

@https_fn.on_request(cors=common_cors)
def getVendorRatings(req: https_fn.Request) -> https_fn.Response:
    return getVendorRatings_fn(req)

@https_fn.on_request(cors=common_cors)
def createRating(req: https_fn.Request) -> https_fn.Response:
    return createRating_fn(req)

@https_fn.on_request(cors=common_cors)
def getServiceRatings(req: https_fn.Request) -> https_fn.Response:
    return getRatingsForService_fn(req)

@https_fn.on_request(cors=common_cors)
def getVendorRatingsAgg(req: https_fn.Request) -> https_fn.Response:
    return getVendorRatingsAgg_fn(req)