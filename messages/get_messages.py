from firebase_admin import firestore
from flask import jsonify, request
from common import fdb
from settings import *
from datetime import datetime, timezone 
from auth.auth_user_wrapper import uauth
import traceback

@uauth
def getMessages_fn(request):
    try:
        req_json = request.get_json()
        thread_id = req_json.get('threadId')
        limit = int(req_json.get('limit', 20))
        start_after = req_json.get('startAfter')  # ISO 8601 string
        # for polling
        start_before = req_json.get('startBefore')

        lg.t("Start after ~ " + str(start_after))

        if not thread_id:
            return jsonify({'error': 'Missing threadId'}), 400

        fsq_direction = firestore.Query.DESCENDING
        if start_after:
            fsq_direction = firestore.Query.DESCENDING
        if start_before:
            fsq_direction = firestore.Query.ASCENDING

        lg.t("get messages ref")
        messages_ref = (
            fdb
            .collection(thread_collection)
            .document(thread_id)
            .collection(messages_sub_collection)
            .order_by('timestamp', direction=fsq_direction)
            .limit(limit)
        )

        lg.t("Get starts")

        if start_after:
            lg.t("found start after")
            start_after_dt = firestore.SERVER_TIMESTAMP
            try:
                # start_after_dt = firestore.client()._helpers._datetime_from_isoformat(start_after)
                start_after_dt = datetime.strptime(start_after, "%Y-%m-%dT%H:%M:%S.%fZ")
                start_after_dt = start_after_dt.replace(tzinfo=timezone.utc)
            except Exception:
                return jsonify({'error': 'Invalid startAfter format'}), 400
            messages_ref = messages_ref.start_after({'timestamp': start_after_dt})

        if start_before:
            lg.t("found start before")
            start_before_dt = firestore.SERVER_TIMESTAMP
            try:
                # start_after_dt = firestore.client()._helpers._datetime_from_isoformat(start_after)
                start_before_dt = datetime.strptime(start_before, "%Y-%m-%dT%H:%M:%S.%fZ")
                start_before_dt = start_before_dt.replace(tzinfo=timezone.utc)
            except Exception:
                return jsonify({'error': 'Invalid startBefore format'}), 400
            messages_ref = messages_ref.start_after({'timestamp': start_before_dt})

        docs = messages_ref.stream()
        messages = []

        for doc in docs:
            data = doc.to_dict()
            messages.append({
                'messageId': doc.id,
                'receiverId': data['receiverId'],
                'senderName': data['senderName'],
                'senderId': data['senderId'],
                'text': data['text'],
                'threadId': data['threadId'],
                'timestamp': data['timestamp'].isoformat() if data['timestamp'] else None,
            })

        return jsonify(messages)
    
    except Exception as e:
        lg.e("Exp ~ " + str(e) + " trace ~ " + str(traceback.format_exc()))
        if debug_responses:
            return jsonify({'success': False,           
            'error': str(e),
            'trace': traceback.format_exc()
            }), 500   
        else:
            return std_exception_response()
        