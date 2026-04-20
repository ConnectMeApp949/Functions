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
def getRatingsForService_fn(request):

    try:
        pdata = request.get_json()
        lg.t("[getRatingsForService_fn] with pdata ~ " + str(pdata))   

        user_id = pdata.get("userId")
        rating_type = pdata.get("ratingType") # should be completed
        service_id = pdata.get("serviceId")

        lg.t("[getRatingsForService_fn] build rating query")
        
        # query = fdb.collection(rating_collection) \
                        #   .document(user_id).collection(rating_collection_subtype)
        query = fdb.collection(rating_collection) \
           .where("serviceId", "==", service_id) \
            .where("ratingStatus", "==", "completed")
           
        lg.t("[getRatingsForService_fn] order query")
        direction = firestore.Query.DESCENDING
        query = query.order_by('bookingTime', direction=direction)

        lg.t("[getRatingsForService_fn] stream query")
        docs = query.stream()

        lg.t("[getRatingsForService_fn] loop ratings")
        ratings = []
        for doc in docs:
            data = doc.to_dict()
            lg.t("looping rating doc data ~ " + str(data))
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