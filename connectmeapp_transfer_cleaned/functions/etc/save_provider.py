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
def getSavedProviders_fn(request):

    pdata = request.get_json()
    lg.t("getSavedProviders_fn with pdata ~ " + str(pdata))
     
    try:
        lg.t("get user id")

        userId = pdata.get("userId")

        saved_providers = []

        try:
            # will throw before user saves any
            doc_ref = fdb.collection(saved_provider_collection).document(userId)
            saved_providers = doc_ref.get().to_dict().get("saved_providers",[])
        except Exception as e:
            pass

        return jsonify({'success': True, "data": saved_providers})

    except Exception as e:              
        lg.e("Exp ~ " + str(e) + " trace ~ " + str(traceback.format_exc()))
        return jsonify({'success': False,           
        'error': str(e),
        }), 500   


@uauth
def saveProvider_fn(request):

    pdata = request.get_json()
    lg.t("saveProvider_fn with pdata ~ " + str(pdata))
     
    try:
        lg.t("get user id")

        userId = pdata.get("userId")
        vendorUserId = pdata.get("vendorUserId")

        remove = pdata.get("remove")

        doc_ref = fdb.collection(saved_provider_collection).document(userId)

        if not remove:
            doc_ref.set(
            { 'saved_providers': firestore.ArrayUnion([vendorUserId]) },
                merge=True
            )
        elif remove:
            doc_ref.update({
                'saved_providers': firestore.ArrayRemove([vendorUserId])
            })

        return jsonify({'success': True})

    except Exception as e:
        lg.e("Exp ~ " + str(e) + " trace ~ " + str(traceback.format_exc()))
        return jsonify({'success': False,           
        'error': str(e),
        }), 500   