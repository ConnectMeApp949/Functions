from proto.datetime_helpers import DatetimeWithNanoseconds
import traceback
import copy
import random
from util.hash_methods import createUUIDLower
from firebase_admin import auth
from settings import *
from common import fdb
from firebase_admin.firestore import GeoPoint
import geohash2
from firebase_functions import https_fn
import threading
from datetime import datetime, timezone, timedelta

""" Firebase emulator is running twice, this will only prevent in the emulator
"""
insert_lock = threading.Lock()
already_seeded = False

def seedServicesData_fn(request):
    lg.t("seedServicesData_fn called")
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

                vendorTestUserId = "vp5t39isqq0euy7sgkrw4u7l"

                categories = ["Professional Services", "Education", "Transportation", "Health", "Entertainment", "Other"]

                i = 0
                i_lim = 10
                while i < i_lim:
                    i += 1
                    sign = 1
                    if i%2 == 0:
                        sign = -1
                    create_time = datetime.now(timezone.utc) \
                           - timedelta(days=i)

                    if i%3 == 0:
                        site = "client-site"
                    if i%3 == 1:
                        site = "on-site"
                    if i%3 == 2:
                        site = "delivery"
                    
                    if i%3 == 0:
                        price_add = 2000
                        time_add = 0
                        rating_gen = 3.5
                    if i%3 == 1:
                        price_add = 4000
                        time_add = 30
                        rating_gen = 4
                    if i%3 == 2:
                        price_add = 6000
                        time_add = 90
                        rating_gen = 5
                    cati = i % len(categories)
                    category_gen = categories[cati].lower()

                    if i%13 == 0:
                        rating_gen = None
                    rand_lat = random.uniform(30, 50)
                    rand_lon = random.uniform(-120, -70)
                    #             latitude = 38.6
                    #             longitude = -90.2

                    geo_hash = geohash2.encode(rand_lat, rand_lon, precision=9)
                    service_id = "aservice"+str(i)

                    tsi ={
                        "address": "11 Random Street Somewhere, SomeState 12345" ,
                         "category": category_gen.lower(),
                         "createTime": create_time,
                         "description": f"This is a description of service {i}, please contact us if you have any questions",
                         "email": "v_test_email@connectme.dev",
                         "featureImageId": "service_images/tim_1.jpeg",        
                         "geoHash": geo_hash,
                         "imageIds": ["service_images/tim_1.jpeg", "service_images/tim_2.jpeg", "service_images/tim_3.jpg"],          
                         "keywords": [category_gen],
                         "location": GeoPoint(rand_lat, rand_lon),
                         "name": "Vanessa's Service " + str(i),
                         "phoneNumber": "+1 (555) 555-5555",
                         "priceCents": 2000 + price_add,
                         "radius": 156, # needs to be one of the dropdown options
                         "rating": rating_gen,
                         "ratingCount": 3,
                         "serviceId":service_id,
                         "site": site,
                         "timeLength": 60 + time_add,
                         "vendorUserId": vendorTestUserId,
                         "vendorBusinessName": "Vanessa's business",
                         "vendorUserName": "Vanessa",
                       }
                    lg.t("Adding service ~ " + tsi["name"])
                    fdb.collection(service_collection).document(service_id).set(tsi)


                """Seed remote services
                """
                ri = 0
                ri_lim = 10
                while ri < ri_lim:
                    sign = 1
                    if ri%2 == 0:
                        sign = -1
                    create_time = datetime.now(timezone.utc) \
                           - timedelta(days=ri)


                    if ri%3 == 0:
                        price_add = 2000
                        time_add = 30
                        rating_gen = 3
                    if ri%3 == 1:
                        price_add = 4000
                        time_add = 60
                        rating_gen = 4.5
                    if ri%3 == 2:
                        price_add = 6000
                        time_add = 90
                        rating_gen = 5
                    cati = ri % len(categories)
                    category_gen = categories[cati].lower()
                     
                    if ri%3 == 0:
                        rating_gen = None
                    #             rand_lat = random.uniform(30, 50)
                    #             rand_lon = random.uniform(-120, -70)
                    #             latitude = 38.6
                    #             longitude = -90.2

                    geo_hash = geohash2.encode(rand_lat, rand_lon, precision=9)

                    remote_service_id = "rservice"+str(ri)
                    
                    keyword_split_category = category_gen
                    
                    tsi ={
        #                 "address": "Test Address, Ks 92672",
                         "category": category_gen,
                         "createTime": create_time,
                         "description": f"This is a description of service {i}, please contact us if you have any questions",
                         "email": "v_test_email@connectme.dev",
                        "featureImageId": "service_images/tim_2.jpeg",
                          "imageIds":["service_images/tim_1.jpeg", "service_images/tim_2.jpeg", "service_images/tim_3.jpg"],        
    #                  "geoHash": geo_hash,                     
                         "keywords": category_gen.split(),
        #                  "location": GeoPoint(rand_lat, rand_lon),
                        "name": "Vanessa's Remote Service " + str(ri),
        #                  "phoneNumber": "+1 (555) 555-5555",
                         "priceCents": 2000 + price_add,
        #                  "radius": 100,
                         "rating": rating_gen,
                         "ratingCount": 3,
                         "serviceId":remote_service_id,
                         "site":"remote",
        #                  "site": site,
#                            "serviceId":"aaaaaaaservice" + str(i),
                         "timeLength": 60 + time_add,
                         "vendorUserId": vendorTestUserId,
                         "vendorBusinessName": "Vanessa's business",
                         "vendorUserName": "Vanessa",
                       }

                    lg.t("Adding service ~ " + tsi["name"])
                    docRef = fdb.collection(service_collection).document(remote_service_id)
                    docRef.set(tsi)
                    ri += 1

            except Exception as e:
                lg.e("Exception caught ~ ", str(e))
                # traceback.print_exc() # uncomment to see traceback
                if debug_responses:
                    return jsonify({"success": False, "reason": str(e)}, ), 500
                else:
                    return std_exception_response()

    threading.Thread(target=do_inserts).start() # start thread

    return jsonify({"success": True,
                    "reason": "firebase test services seeded"}, )

