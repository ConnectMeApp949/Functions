from firebase_admin import firestore
from flask import request, jsonify
from common import fdb
from settings import *
from datetime import datetime, timezone
from util.collection import clean
from firebase_admin.firestore import GeoPoint, FieldFilter
import traceback
from util.hash_methods import *                  
from auth.auth_user_wrapper import uauth
from util.datetime_util import conv_dt_to_utc



# very important to call "clientUserId": pdata.get("userId"),
# these booking items are basically payment requests

@uauth
def createBooking_fn(request):

    pdata = request.get_json()
    lg.t("[createBooking_fn] with pdata ~ " + str(pdata))   


    try:                
        lg.t("[createBooking_fne_fn] build booking item")
        # make_uuid = createUUIDMixedCase(16)

        vendor_details = fdb.collection(stripe_vendors_collection).document(pdata.get("vendorUserId")).get().to_dict()
        client_details = fdb.collection(stripe_clients_collection).document(pdata.get("userId")).get().to_dict()

        parties_ready = True
        if not vendor_details["charges_enabled"] or not vendor_details["payouts_enabled"]:
            parties_ready = False
        if not client_details["stripe_customer_id"]:
            parties_ready = False

        if not parties_ready:
            return jsonify({
                "parties_ready": False,
            }), 200

        testBTime = datetime.fromisoformat(pdata.get("bookingTime"))
        testCTime = datetime.now(timezone.utc) 

        bi = {
            "address": pdata.get("address"),
            "bookingId": pdata.get("bookingId"),
            "bookingTime": testBTime,
            "createTime": testCTime,       
            "clientUserId": pdata.get("userId"),
            "clientUserName": pdata.get("clientUserName"),
            "priceCents": pdata.get("priceCents"),  
            "serviceId": pdata.get("serviceId"),
            "serviceName": pdata.get("serviceName"),
            "site": pdata.get("site"),
            "status": "pending",
            "timeLength": pdata.get("timeLength"),
            "vendorBusinessName": pdata.get("vendorBusinessName"),
            "vendorUserId": pdata.get("vendorUserId"),
            "vendorUserName": pdata.get("vendorUserName"),
        }

        lg.t("booking item ~ " + str(bi))       

        fdb.collection(booking_collection).document(pdata.get("bookingId")).set(bi)

        rating_id = createUUIDMixedCase(16)
        ri = {
            "bookingId": pdata.get("bookingId"),
            "clientUserId": pdata.get("userId"),
            "clientUserName": pdata.get("clientUserName"),
            "createTime": datetime.now(timezone.utc), 
            "ratingId": rating_id,
            "ratingStatus": "unused",
            "serviceId": pdata.get("serviceId"),
            "serviceName": pdata.get("serviceName"),
            "bookingTime": datetime.fromisoformat(pdata.get("bookingTime")),
            "vendorUserId": pdata.get("vendorUserId"),
            "vendorUserName": pdata.get("vendorUserName"),
        }

        fdb.collection(rating_collection) \
        .document(rating_id).set(ri)

        return jsonify({'success': True, "bookingId": pdata.get("bookingId")})

    except Exception as e:
        lg.e("Exp ~ " + str(e) + " trace ~ " + str(traceback.format_exc()))
        return jsonify({'success': False,
        'error': str(e),
        'trace': traceback.format_exc()
        }), 500