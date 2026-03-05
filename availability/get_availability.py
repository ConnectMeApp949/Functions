from firebase_admin import firestore
from flask import request, jsonify
from common import fdb
from settings import *
import traceback         
from auth.auth_user_wrapper import uauth


"""
 gets initialized with 200 response {baseAvailibility:null success:true}
   - INIT in lib/requests/scheduling/base_availability.dart getBaseAvailability ```if (decResp["baseAvailability"] == null)```
   - INIT in lib/views/vendor_app/calendar/base_availability_page.dart WeeklyAvailabilitySelector initState
       important init point -> noted in get_availability.py

 jsonToBaseAvailability -> returns empty list for disabled day
 updateBaseAvailabilityObject -> takes days map and inputs empty list for disabled day
"""

def getBaseAvailability_fn(request):

    pdata = request.get_json()
    lg.t("[getBaseAvailability_fn] with pdata ~ " + str(pdata))   

    user_id = pdata.get("userId")

    try:                
        lg.t("[getBaseAvailability_fn] get query")
        
        availability_doc = fdb.collection(availability_collection) \
           .document(user_id).get().to_dict() \
           
        return jsonify({'success': True, "baseAvailability": availability_doc})

    except Exception as e:
        lg.e("Exp ~ " + str(e) + " trace ~ " + str(traceback.format_exc()))
        return jsonify({'success': False,
        'error': str(e),
        'trace': traceback.format_exc()
        }), 500