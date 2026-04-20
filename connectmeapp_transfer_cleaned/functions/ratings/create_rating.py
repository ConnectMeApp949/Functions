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



@uauth
def createRating_fn(request):

    try:    
        pdata = request.get_json()
        lg.t("[createRating_fn] with pdata ~ " + str(pdata))   

        if pdata.get("clientUserId") != pdata.get("userId"):
            return jsonify({'success': False,
            'error': "clientUserId and userId do not match",}), 401

        # Validate rating value
        rating_value = pdata.get("rating")
        if not isinstance(rating_value, (int, float)) or rating_value < 1 or rating_value > 5:
            return jsonify({'success': False, 'error': 'Rating must be between 1 and 5'}), 400

        lg.t("[createRating_fn] build rating item")
        make_uuid = createUUIDMixedCase(16)

        # need a rating id to be able to update
        rating_id = pdata.get("ratingId")
        ri = {   
            "createTime": datetime.now(timezone.utc), 
            "bookingId": pdata.get("bookingId"),
            "clientUserId": pdata.get("clientUserId"),
            "clientUserName": pdata.get("clientUserName"),
            # "createTime": datetime.fromisoformat(pdata.get("createTime")),
            'rating': pdata.get("rating"),
            'ratingComment': pdata.get("ratingComment"),
            'ratingId': rating_id,
            "ratingStatus": "completed",
            "serviceId": pdata.get("serviceId"),
            "serviceName": pdata.get("serviceName"),
            "bookingTime": datetime.fromisoformat(pdata.get("bookingTime")),
            "vendorUserId": pdata.get("vendorUserId"),
            "vendorUserName": pdata.get("vendorUserName"),
           
        }

        lg.t("checking for rating and continue")
        doc_ref = fdb.collection(rating_collection).document(rating_id)
        if doc_ref.get().exists:
            doc_ref.delete()
            print("Deleted existing document.")
        else:
            print("Document did not exist, security measures")
            return jsonify({'success': False, "reason": "unauthorized"}), 401


        lg.t("Inserting completed rating")
        fdb.collection(rating_collection) \
            .document(rating_id).set(ri)
        

        # update service rating
        service_item = fdb.collection(service_collection). \
        document(pdata.get("serviceId")).get().to_dict()

        lg.t("update service rating doc")
        old_rating = service_item.get("rating")
        if old_rating == None:
            old_rating = 0
        old_rating_count = service_item.get("ratingCount")
        newest_rating = pdata.get("rating")
        new_rating_count = old_rating_count + 1
        new_average = ((old_rating * old_rating_count) + newest_rating) / (new_rating_count)


        service_doc_ref = fdb.collection(service_collection). \
            document(pdata.get("serviceId"))

        service_doc_ref.update({
            "rating": new_average,
            "ratingCount": new_rating_count
        })

        lg.t("update vendor rating doc")

        vendor_services = fdb.collection(service_collection).where("vendorUserId", "==", pdata.get("vendorUserId")).stream()
        service_count = 0
        service_rating_sum = 0
        service_rating_count = 0
        for doc in vendor_services:
            dd = doc.to_dict()
            get_rating_safe = dd.get("rating")
            if get_rating_safe is not None:
                service_count += 1
                service_rating_sum += dd.get("rating")
                service_rating_count += dd.get("ratingCount")

        lg.t("summed service ratings")
        if service_count != 0:
            new_vendor_average = service_rating_sum / service_count
            vendor_doc_ref = fdb.collection(user_collection).document(pdata.get("vendorUserId"))
            vendor_doc_ref.update({
                "userMeta.rating": new_vendor_average,
                "userMeta.ratingCount": service_rating_count
            })


        return jsonify({'success': True, "ratingId": rating_id})

    except Exception as e:
        lg.e("Exp ~ " + str(e) + " trace ~ " + str(traceback.format_exc()))
        if debug_responses:
            return jsonify({'success': False,           
            'error': str(e),
            }), 500   
        else:
            return std_exception_response()