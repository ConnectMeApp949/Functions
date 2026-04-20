from firebase_admin import firestore
from flask import request, jsonify
from common import fdb
from settings import *
from datetime import datetime, timezone
from util.collection import clean
from firebase_admin.firestore import GeoPoint, FieldFilter
import traceback
from auth.auth_user_wrapper import uauth


@uauth
def getUserAccountSubscription_fn(request):
    pdata = request.get_json()
    lg.t("getUserAccountSubscription_fn called")
    try:
        lg.t("get user id")
        userId = pdata.get("userId")
        user_doc = fdb.collection(user_collection).document(userId).get().to_dict()
        al = user_doc.get("accountLevel")
        pe = user_doc.get("purchaseEver")
        as_data = {"accountLevel": al, "purchaseEver": pe}

        return jsonify({'success': True, "data": as_data})

    except Exception as e:
        lg.e("Exp ~ " + str(e) + " trace ~ " + str(traceback.format_exc()))
        if debug_responses:
            return jsonify({'success': False,
            'error': str(e),
            }), 500
        else:
            return std_exception_response()