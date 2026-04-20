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

        # Server-side price validation: look up actual service price
        service_id = pdata.get("serviceId")
        service_doc = fdb.collection(service_collection).document(service_id).get()
        if not service_doc.exists:
            return jsonify({'success': False, 'reason': 'Service not found'}), 404
        service_data = service_doc.to_dict()
        server_price_cents = service_data.get("priceCents")

        testBTime = datetime.fromisoformat(pdata.get("bookingTime"))
        testCTime = datetime.now(timezone.utc)

        # Generate bookingId server-side instead of trusting client
        booking_id = createUUIDMixedCase(16)

        bi = {
            "address": pdata.get("address"),
            "bookingId": booking_id,
            "bookingTime": testBTime,
            "createTime": testCTime,
            "clientUserId": pdata.get("userId"),
            "clientUserName": pdata.get("clientUserName"),
            "priceCents": server_price_cents,  # Use server-side price, not client-supplied
            "serviceId": service_id,
            "serviceName": pdata.get("serviceName"),
            "site": pdata.get("site"),
            "status": "pending",
            "timeLength": service_data.get("timeLength"),  # Use server-side timeLength
            "vendorBusinessName": pdata.get("vendorBusinessName"),
            "vendorUserId": pdata.get("vendorUserId"),
            "vendorUserName": pdata.get("vendorUserName"),
        }

        lg.t("booking created with server-validated price")

        fdb.collection(booking_collection).document(booking_id).set(bi)

        rating_id = createUUIDMixedCase(16)
        ri = {
            "bookingId": booking_id,
            "clientUserId": pdata.get("userId"),
            "clientUserName": pdata.get("clientUserName"),
            "createTime": datetime.now(timezone.utc),
            "ratingId": rating_id,
            "ratingStatus": "unused",
            "serviceId": service_id,
            "serviceName": pdata.get("serviceName"),
            "bookingTime": testBTime,
            "vendorUserId": pdata.get("vendorUserId"),
            "vendorUserName": pdata.get("vendorUserName"),
        }

        fdb.collection(rating_collection) \
        .document(rating_id).set(ri)

        return jsonify({'success': True, "bookingId": booking_id})

    except Exception as e:
        lg.e("Exp ~ " + str(e))
        if debug_responses:
            return jsonify({'success': False, 'error': str(e)}), 500
        else:
            return std_exception_response()