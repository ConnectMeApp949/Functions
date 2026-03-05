from firebase_admin import firestore
from flask import request, jsonify
from common import fdb
from settings import *
import traceback         
from auth.auth_user_wrapper import uauth



@uauth
def setBaseAvailability_fn(request):

    pdata = request.get_json()
    # lg.t("[setBaseAvailability_fn] with pdata ~ " + str(pdata))   

    user_id = pdata.get("userId")
    new_availability = pdata.get("baseAvailability")

    # set to avoid issues but not needed
    if new_availability.get("double_booking_enabled") == None:
        new_availability["double_booking_enabled"] = False

    try:                
        lg.t("[setBaseAvailability_fn] do insert")
        
        availability_doc = fdb.collection(availability_collection) \
           .document(user_id).set(new_availability) 
           
        return jsonify({'success': True})

    except Exception as e:
        lg.e("Exp ~ " + str(e) + " trace ~ " + str(traceback.format_exc()))
        return jsonify({'success': False,
        'error': str(e),
        'trace': traceback.format_exc()
        }), 500