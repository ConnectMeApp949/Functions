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
def blockThread_fn(request):
    request_json = request.get_json()
    user_id = request_json.get('userId')
    other_user_id = request_json.get('otherUserId')
    thread_id = request_json.get('threadId')
    block_action = request_json.get('blockAction')

    try:

        # threads_ref = (
        #     fdb.collection(thread_collection)
        #     .where('userIds', 'array_contains', user_id)
        #     .where('userIds', 'array_contains', other_user_id)
        # )
        lg.t("get thread ref")
        thread_ref = fdb.collection(thread_collection).document(thread_id)

        lg.t("set doc ref")
        doc_ref = thread_ref

        lg.t("check block action")
        if block_action == "block":
            lg.t("block action block")
            doc_ref.update({
                'want_block': firestore.ArrayUnion([user_id])
            }
            )
        elif block_action == "unblock":
            lg.t("block action unblock")
            doc_ref.update({
                'want_block': firestore.ArrayRemove([user_id])
            }
            )

        return jsonify({"success": True})
    
    
    except Exception as e:
        lg.e("Exp ~ " + str(e) + " trace ~ " + str(traceback.format_exc()))
        return jsonify({'success': False,           
        'error': str(e),
        }), 500   
    
@uauth
def reportMessageUser_fn(request):
    request_json = request.get_json()
    user_id = request_json.get('userId')
    other_user_id = request_json.get('otherUserId')
    thread_id = request_json.get('threadId')
    report_message = request_json.get('reportMessage')


    try:
        thread_ref = fdb.collection(report_collection).document(user_id).collection("reports").document()
        
        thread_ref.set({
            "createTime": datetime.now(timezone.utc),
            "reportType": "message",
            "thread_id": thread_id,
            "other_user_id": other_user_id,
            "user_id": user_id,
            "report_text": report_message,
        })


        return jsonify({"success": True})
    
    
    except Exception as e:
        lg.e("Exp ~ " + str(e) + " trace ~ " + str(traceback.format_exc()))
        return jsonify({'success': False,           
        'error': str(e),
        }), 500   