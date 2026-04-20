from firebase_functions import https_fn
from booking.booking import getBookings_fn, getBookingByID_fn
from booking.create_booking import createBooking_fn
from booking.confirm_booking_and_pay import confirmBookingAndPay_fn
from booking.cancel_booking import cancelBooking_fn
from common import common_cors


@https_fn.on_request(cors=common_cors)
def getBookings(req: https_fn.Request) -> https_fn.Response:
    return getBookings_fn(req)

@https_fn.on_request(cors=common_cors)
def createBooking(req: https_fn.Request) -> https_fn.Response:
    return createBooking_fn(req)

@https_fn.on_request(cors=common_cors)
def confirmBookingAndPay(req: https_fn.Request) -> https_fn.Response:
    return confirmBookingAndPay_fn(req)

@https_fn.on_request(cors=common_cors)
def cancelBooking(req: https_fn.Request) -> https_fn.Response:
    return cancelBooking_fn(req)

@https_fn.on_request(cors=common_cors)
def getBookingByID(req: https_fn.Request) -> https_fn.Response:
    return getBookingByID_fn(req)