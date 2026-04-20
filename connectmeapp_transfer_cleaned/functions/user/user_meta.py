from firebase_admin import firestore
from flask import request, jsonify
from common import fdb
from settings import *
from datetime import datetime, timezone
from util.collection import clean
from firebase_admin.firestore import GeoPoint, FieldFilter
import traceback
from auth.auth_user_wrapper import uauth
import datetime


@uauth
def getUserMeta_fn(request):

    pdata = request.get_json()
    lg.t("getUserMeta_fn called")
     
    try:
        lg.t("get user id")
        userId = pdata.get("userId")

        user_doc = fdb.collection(user_collection).document(userId).get().to_dict()

        meta_data = user_doc.get("userMeta") 

        return jsonify({'success': True, "data": meta_data})
    
    except Exception as e:
        lg.e("Exp ~ " + str(e) + " trace ~ " + str(traceback.format_exc()))
        if debug_responses:
            return jsonify({'success': False,           
            'error': str(e),
            }), 500   
        else:
            return std_exception_response()

@uauth
def updateUserMeta_fn(request):

    pdata = request.get_json()
    lg.t("updateUserMeta_fn with pdata ~ " + str(pdata))
     
    try:
        lg.t("get user id")
        userId = pdata.get("userId")
        lg.t("get update data")
        updateUserMeta = pdata.get("updateUserMeta") 
        lg.t("insert update data")
        fdb.collection(user_collection).document(userId).update({"userMeta": updateUserMeta })

        return jsonify({'success': True})
    
    except Exception as e:
        lg.e("Exp ~ " + str(e) + " trace ~ " + str(traceback.format_exc()))
        if debug_responses:
            return jsonify({'success': False,           
            'error': str(e),
            }), 500   
        else:
            return std_exception_response()





@uauth
def updateUserAccountSub_fn(request):

    pdata = request.get_json()
    lg.t("updateUserAccountSub_fn with pdata ~ " + str(pdata))

    try:
        lg.t("get user id")
        userId = pdata.get("userId")
        lg.t("get update data")
#         updateUserMeta = pdata.get("purchaseEver")
#         lg.t("insert update data")

        purchaseProductId = pdata.get("purchaseProductId")

        now = datetime.datetime.now()
        currMillis = int(now.timestamp() * 1000)

        fdb.collection(user_collection).document(userId).update(
        {"purchaseEver": True ,
         "accountLevel": vendor_account_sub_status_string,
         "latestPurchaseProductId": purchaseProductId,
         "latestPurchaseTimeMillis": currMillis
        })

        return jsonify({'success': True})

    except Exception as e:
        lg.e("Exp ~ " + str(e) + " trace ~ " + str(traceback.format_exc()))
        if debug_responses:
            return jsonify({'success': False,
            'error': str(e),
            }), 500
        else:
            return std_exception_response()