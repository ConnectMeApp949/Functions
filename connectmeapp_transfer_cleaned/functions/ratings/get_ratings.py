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


# Get a clients ratings they've made
@uauth
def getRatings_fn(request):

    try:
        pdata = request.get_json()
        lg.t("[getRatings_fn] with pdata ~ " + str(pdata))   

        user_id = pdata.get("userId")
        rating_status = pdata.get("ratingStatus")
          
        lg.t("[getRatings_fn] build rating query")
        
        # query = fdb.collection(rating_collection) \
                        #   .document(user_id).collection(rating_collection_subtype)
        query = fdb.collection(rating_collection) \
           .where("clientUserId", "==", user_id) \
           .where("ratingStatus", "==", rating_status)
           
        # lg.t("[getRatings_fn] order query")
        direction = firestore.Query.DESCENDING
        query = query.order_by('bookingTime', direction=direction)

        # lg.t("[getRatings_fn] stream query")
        docs = query.stream()

        # lg.t("[getRatings_fn] loop ratings")
        ratings = []
        for doc in docs:
            data = doc.to_dict()
            # lg.t("looping rating doc data ~ " + str(data))
            data["createTime"] = data["createTime"].isoformat().replace('+00:00', 'Z')
            data["bookingTime"] = data["bookingTime"].isoformat().replace('+00:00', 'Z')
            ratings.append(data)
        lg.t("returning ratings len ~ " + str(len(ratings))) 

        return jsonify({'success': True, "ratings": ratings})

    except Exception as e:
        lg.e("Exp ~ " + str(e) + " trace ~ " + str(traceback.format_exc()))
        if debug_responses:
            return jsonify({'success': False,           
            'error': str(e),
            }), 500   
        else:
            return std_exception_response()
    

@uauth
def getVendorRatings_fn(request):

    try:
        pdata = request.get_json()
        lg.t("[getVendorRatings_fn] with pdata ~ " + str(pdata))   

        vendor_user_id = pdata.get("vendorUserId")

        lg.t("[getVendorRatings_fn] build rating query")
        
        # query = fdb.collection(rating_collection) \
                        #   .document(user_id).collection(rating_collection_subtype)
        query = fdb.collection(rating_collection) \
           .where("vendorUserId", "==", vendor_user_id) \
           .where("ratingStatus", "==", "completed")
           
        lg.t("[getVendorRatings_fn] order query")
        direction = firestore.Query.DESCENDING
        query = query.order_by('bookingTime', direction=direction)

        # lg.t("[getVendorRatings_fn] stream query")
        docs = query.stream()

        # lg.t("[getRatings_fn] loop ratings")
        ratings = []
        for doc in docs:
            try:
                data = doc.to_dict()
                # lg.t("looping rating doc data ~ " + str(data))
                data["createTime"] = data["createTime"].isoformat().replace('+00:00', 'Z')
                data["bookingTime"] = data["bookingTime"].isoformat().replace('+00:00', 'Z')
                ratings.append(data)
            except Exception as e:
                lg.e("Exp caught converting rating doc to data, continuing doc loop")
        
        lg.t("returning ratings len ~ " + str(len(ratings))) 

        return jsonify({'success': True, "ratings": ratings})

    except Exception as e:
        lg.e("Exp ~ " + str(e))
        if debug_responses:
            return jsonify({'success': False, 'error': str(e)}), 500
        else:
            return std_exception_response()



def getVendorRatingsAgg_fn(request):
    try:
        pdata = request.get_json()

        query = fdb.collection(user_collection).document(pdata.get("vendorUserId"))

        user_doc = query.get().to_dict()
        rating = user_doc.get("userMeta").get("rating")
        rating_count = user_doc.get("userMeta").get("ratingCount")

        resp = {"success":True,
                "review_data":{
                    "vendorRating":rating,
                    "vendorRatingCount":rating_count
                   }
                }
                

        return jsonify(resp)


    except Exception as e:
        lg.e("Exp ~ " + str(e) + " trace ~ " + str(traceback.format_exc()))
        if debug_responses:
            return jsonify({'success': False,           
            'error': str(e),
            }), 500   
        else:
            return std_exception_response()