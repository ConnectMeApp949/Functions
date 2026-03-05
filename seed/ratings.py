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
from datetime import timezone, datetime, timedelta

""" Firebase emulator is running twice, this will only prevent in the emulator
"""
insert_lock = threading.Lock()
already_seeded = False

def seedRatingData_fn(request):
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
                vendorServiceId = "aservice1"
                vendorServiceName = "Vanessa's Service 1"

                numberToSeed = 10
                
                rating_total_avg = 0
                i = 0
                while i < numberToSeed:

#                     booking_time = datetime.datetime.now() + \
#                                             datetime.timedelta(days= ( i * switch_sign ) )
                    booking_time = (datetime.now(timezone.utc) - timedelta(days=(i)))
                    rating_time = (datetime.now(timezone.utc) - timedelta(days=(2*i)))

                    rating_make = random.randint(1, 5)
                    rating_total_avg += rating_make

                    r = random.randint(0, 1)
                    if r == 0:
                        rating_status = "completed"
                    if r==1:
                        rating_status = "unused"

                    rating_id = "arating" + str(i)
                    
                    tri = {   
                                "createTime": rating_time, 
                                "bookingId": "aaabookingID" + str(i),
                                "clientUserId": clientTestUserId,
                                "clientUserName": "caroline",
                                'rating': rating_make,
                                'ratingComment': f"This is a review of {vendorServiceName} it was really something and I something'd it a lot",
                                'ratingId': rating_id,
                                "ratingStatus": "completed",
                                "serviceId": vendorServiceId,
                                "serviceName": vendorServiceName,
                                "bookingTime": booking_time,
                                "vendorUserId": vendorTestUserId,
                                "vendorUserName": "Vanessa",
                            
                            }
                    lg.t("Adding rating ~ " + str(i))
                    # for tbi in bookings_test_data:
                    fdb.collection(rating_collection).document(rating_id).set(tri)
                    i += 1

                new_vendor_average = rating_total_avg / numberToSeed
                vendor_doc_ref = fdb.collection(user_collection).document(vendorTestUserId)
                vendor_doc_ref.update({
                    "userMeta.rating": new_vendor_average,
                    "userMeta.ratingCount": numberToSeed
                })


            except Exception as e:
                lg.e("Exception caught ~ ", str(e))
                # traceback.print_exc()
                if debug_responses:
                    return jsonify({"success": False, "reason": str(e)}, ), 500
                else:
                    return std_exception_response()     

    threading.Thread(target=do_inserts).start() # start thread

    return jsonify({"success": True,
                    "reason": "firebase test ratings seeded"}, )