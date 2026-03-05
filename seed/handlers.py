from firebase_functions import https_fn
from seed.users import seedTestUsers_fn
# from seed.users_1 import seedTestUsers1_fn
from seed.services import seedServicesData_fn
from seed.services_1 import seedServicesData1_fn
from seed.bookings import seedBookingData_fn
from seed.ratings import seedRatingData_fn
from common import common_cors


@https_fn.on_request(cors=common_cors)
def seedTestUsers(req: https_fn.Request) -> https_fn.Response:
    return seedTestUsers_fn(req)


# @https_fn.on_request(cors=common_cors)
# def seedTestUsers_1(req: https_fn.Request) -> https_fn.Response:
#     return seedTestUsers1_fn(req)


@https_fn.on_request(cors=common_cors)
def seedTestServices(req: https_fn.Request) -> https_fn.Response:
    return seedServicesData_fn(req)

@https_fn.on_request(cors=common_cors)
def seedTestServices_1(req: https_fn.Request) -> https_fn.Response:
    return seedServicesData1_fn(req)


@https_fn.on_request(cors=common_cors)
def seedTestBookings(req: https_fn.Request) -> https_fn.Response:
    return seedBookingData_fn(req)

@https_fn.on_request(cors=common_cors)
def seedRatings(req: https_fn.Request) -> https_fn.Response:
    return seedRatingData_fn(req)