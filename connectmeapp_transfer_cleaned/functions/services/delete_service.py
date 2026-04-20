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
        lg.t("deleteService_fn called")

        doc_id = pdata.get("serviceId")
        user_id = pdata.get("userId")

        # Ownership check: only the service owner can delete
        service_doc = fdb.collection(service_collection).document(doc_id).get()
        if not service_doc.exists:
            return jsonify({'success': False, 'reason': 'Service not found'}), 404
        if service_doc.to_dict().get("vendorUserId") != user_id:
            return jsonify({'success': False, 'reason': 'Unauthorized'}), 403

        fdb.collection(service_collection).document(doc_id).delete()

        response = {'success': True,
        }

        return jsonify(response)

    except Exception as e:
        lg.e("Exp ~ " + str(e) + " trace ~ " + str(traceback.format_exc()))
        if debug_responses:
            return jsonify({'success': False,           
            'error': str(e),
            }), 500   
        else:
            return std_exception_response()