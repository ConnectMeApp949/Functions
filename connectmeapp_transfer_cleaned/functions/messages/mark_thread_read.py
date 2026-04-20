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
from google.cloud.firestore_v1 import ArrayRemove, ArrayUnion

@uauth
def markThreadAsRead_fn(request):
    try:
        request_json = request.get_json()
        user_id = request_json.get('userId')
        thread_id = request_json.get('threadId')

        threads_ref = fdb.collection(thread_collection).document(thread_id)


        threads_ref.update({         
            'unread': ArrayRemove([user_id]),  
        })

        return jsonify({"success": True})
    
    except Exception as e:
        lg.e("Exp ~ " + str(e) + " trace ~ " + str(traceback.format_exc()))
        if debug_responses:
            return jsonify({'success': False,           
            'error': str(e),
            }), 500   
        else:
            return std_exception_response()