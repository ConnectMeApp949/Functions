from proto.datetime_helpers import DatetimeWithNanoseconds
import traceback
import copy
from util.hash_methods import createUUIDLower
from firebase_admin import auth
from settings import *
from common import fdb
from firebase_admin.firestore import GeoPoint
import random
import threading
from datetime import timezone, timedelta, datetime

""" Firebase emulator is running twice, this will only prevent in the emulator
"""
insert_lock = threading.Lock()
already_seeded = False

def seedBookingData_fn(request):
    pdata = request.get_json()

    if pdata.get("password") != admin_utils_password:
        return jsonify({"success": False, "reason": "Unauthorized"}), 401

    global already_seeded

    if insert_lock.locked() or already_seeded:
            return jsonify({"success": False, "reason": "Seeding already in progress"}), 429
    def do_inserts():
        global already_seeded
        with insert_lock:
            try:
                clientTestUserId = "cp5t39isqq0euy7sgkrw4u7l"
                vendorTestUserId = "vp5t39isqq0euy7sgkrw4u7l"

                # batch = fdb.batch()
                # bookings_test_data = []
                t_mult = 5
                i = 0
                switch_sign = 1
                while i < 100:

#                     booking_time = datetime.datetime.now() + \
#                                             datetime.timedelta(days= ( i * switch_sign ) )
                    booking_time = (datetime.now(timezone.utc) + timedelta(hours=(i * switch_sign * t_mult)))
                    booking_time_str = booking_time

                    create_time = booking_time - timedelta(days=1)
                    create_time_str = create_time                   

                    if switch_sign == 1:
                        r = random.randint(0, 9)
                        if r >= 5:
                            status = "confirmed"
                        if r < 5:
                            status = "pending"
                    if switch_sign == -1:
                        r = random.randint(0, 14)
                        if r < 5:
                            status = "confirmed"
                        if r >= 5 and r < 10:
                            status = "pending"
                    if r >= 10:  # complete
                            status = "complete"
                    site = "remote"
                    if i%3 == 0:
                        site = "client-site"
                    else:
                        site = "on-site"
                    if i%3 == 0:
                        price_add = 2000
                        time_add = 30
                    if i%3 == 1:
                        price_add = 4000
                        time_add = 60
                    if i%3 == 2:
                        price_add = 6000
                        time_add = 90

                    booking_id = "abooking" + str(i)
                    tbi = {
                        "address": "11 North 4th Street St. Louis, Missouri 63102",
                        "bookingTime":booking_time_str,
                        "createTime": create_time_str,
                        "clientUserId": clientTestUserId,
                        "clientUserName": "caroline",
                        "bookingId": booking_id,
                        "priceCents": 80000 + price_add,
                        "serviceId": "aaaaaaaservice" + str(i),
                        "serviceName": "Service " + str(i),
                        "site": site,
                        "status": status,
                        "timeLength": 60 + time_add,
                        "vendorBusinessName": "Vanessa's business",
                        "vendorUserId": vendorTestUserId,
                        "vendorUserName": "Vanessa",
                    }
                    lg.t("Adding booking ~ " + str(i))
                    i += 1
                    switch_sign = -switch_sign


                # for tbi in bookings_test_data:
                    fdb.collection(booking_collection).document(booking_id).set(tbi)


    #             return jsonify({"success": True,
    #                             "reason": "firebase test bookings seeded"}, )

            except Exception as e:
                lg.e("Exception caught ~ ", str(e))
                # traceback.print_exc()
                if debug_responses:
                    return jsonify({"success": False, "reason": str(e)}, ), 500
                else:
                    return std_exception_response()     

    threading.Thread(target=do_inserts).start() # start thread

    return jsonify({"success": True,
                    "reason": "firebase test bookings seeded"}, )