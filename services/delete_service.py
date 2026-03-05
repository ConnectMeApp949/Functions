from firebase_admin import firestore
from flask import request, jsonify
from common import fdb
from settings import *
from datetime import datetime, timezone
from util.collection import clean
import traceback
from auth.auth_user_wrapper import uauth

@uauth
def deleteService_fn(request):
    try:
        pdata = request.get_json()
        lg.t("deleteService_fn called w pdata ~ " + str(pdata))
        pdata = request.get_json()

        doc_id = pdata.get("serviceId")
        fdb.collection(service_collection).document(doc_id).delete()

        response = {'success': True,
        }

        return jsonify(response)

    except Exception as e:
        lg.e("Exp ~ " + str(e) + " trace ~ " + str(traceback.format_exc()))
        if debug_responses:
            return jsonify({'success': False,           
            'error': str(e),
            'trace': traceback.format_exc()
            }), 500   
        else:
            return std_exception_response()