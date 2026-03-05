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
def getMessageThreads_fn(request):
    try:
        request_json = request.get_json()
        user_id = request_json.get('userId')
        user_name = request_json.get('userName')

        threads_ref = fdb.collection(thread_collection).where('userIds', 'array_contains', user_id)
        docs = threads_ref.order_by('lastUpdated', direction=firestore.Query.DESCENDING).stream()

        threads = []
        for doc in docs:
            data = doc.to_dict()
            other_user_id = next(uid for uid in data['userIds'] if uid != user_id)
            other_user_name = next(uname for uname in data['userNames'] if uname != user_name)
            # Assume you have a user profile collection:
            # user_doc = db.collection('users').document(other_user_id).get()
            # other_user_name = user_doc.to_dict().get('name', 'Unknown')

            threads.append({
                'lastMessage': data['lastMessage'],
                'lastUpdated': data['lastUpdated'].isoformat(),
                'otherUserId': other_user_id,
                'otherUserName': other_user_name,
                'threadId': doc.id,
                'wantBlock': data.get("want_block"),         
                'unread': data.get("unread")   
            })

        return jsonify(threads)

    except Exception as e:
        lg.e("Exp ~ " + str(e) + " trace ~ " + str(traceback.format_exc()))
        if debug_responses:
            return jsonify({'success': False,           
            'error': str(e),
            'trace': traceback.format_exc()
            }), 500   
        else:
            return std_exception_response()