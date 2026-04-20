from firebase_admin import firestore
from flask import request, jsonify
from common import fdb
from settings import *
from datetime import datetime, timezone
from util.collection import clean
from firebase_admin.firestore import GeoPoint, FieldFilter
import traceback
from auth.auth_user_wrapper import uauth


def testUserAuth_fn(request):

    pdata = request.get_json()
    lg.t("testUserAuth_fn with pdata ~ " + str(pdata))
     
    try:
        lg.t("get magic word")

        password = pdata.get("password")

        if password != test_user_password:
            return jsonify({'success': False, 'error': "Incorrect password"}), 401
        else:
            return jsonify({'success': True})

    except Exception as e:              
        lg.e("Exp ~ " + str(e) + " trace ~ " + str(traceback.format_exc()))
        return jsonify({'success': False,           
        'error': str(e),
        }), 500   