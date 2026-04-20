import functions_framework
from firebase_admin import firestore
from flask import jsonify
import hashlib
from common import fdb
from settings import *
from datetime import datetime, timezone
from auth.auth_user_wrapper import uauth
import traceback


# Helper: generate deterministic thread ID
def get_thread_id(user1: str, user2: str) -> str:
    sorted_ids = sorted([user1, user2])
    return hashlib.sha256(f"{sorted_ids[0]}_{sorted_ids[1]}".encode()).hexdigest()


@uauth
def getOrCreateThread_fn(request):
    try:
        lg.t("[getOrCreateThread_fn] called")
        req_json = request.get_json()
        # user1_id = req_json.get('user1Id')
        user1_id = req_json.get('userId') # security upgrade
        user2_id = req_json.get('user2Id')
        user1_name = req_json.get('user1Name')
        user2_name = req_json.get('user2Name')              

        if not all([user1_id, user2_id, user1_name, user2_name]):
            return jsonify({'error': 'Missing user IDs or names'}), 400

        thread_id = get_thread_id(user1_id, user2_id)
        thread_ref = fdb.collection(thread_collection).document(thread_id)
        doc = thread_ref.get()

        if doc.exists:
            data = doc.to_dict()
            return jsonify({
                'threadId': thread_id,
                'lastMessage': data.get('lastMessage', ''),
                'lastUpdated': data.get('lastUpdated').isoformat().replace('+00:00', 'Z'),
                'userIds': data.get('userIds', []),
                'userNames': data.get('userNames', []),
                'alreadyExisted': True
            })

        # Create new thread

        thread_data = {
            'threadId': thread_id,
            'lastMessage': '',
            'lastUpdated': datetime.now(timezone.utc),
            'userIds': sorted([user1_id, user2_id]),
            'userNames': sorted([user1_name, user2_name]),
        }

        thread_ref.set(thread_data)
        thread_data['lastUpdated'] = thread_data['lastUpdated'].isoformat().replace('+00:00', 'Z')
        return jsonify({**thread_data, 'alreadyExisted': False})

    except Exception as e:
        lg.e("Exp ~ " + str(e) + " trace ~ " + str(traceback.format_exc()))
        if debug_responses:
            return jsonify({'success': False,           
            'error': str(e),
            }), 500   
        else:
            return std_exception_response()