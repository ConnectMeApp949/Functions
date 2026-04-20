import uuid
from firebase_admin import firestore
from datetime import datetime, timezone
from flask import jsonify, request
from common import fdb
from auth.auth_user_wrapper import uauth
from settings import *
import traceback


@uauth
def sendMessage_fn(request):
    try:
        req_json = request.get_json()
        message_id = req_json.get('messageId')
        receiver_id = req_json.get('receiverId')
        sender_name = req_json.get('userName')
        sender_id = req_json.get('userId')  # Use authenticated userId, not client-supplied senderId
        thread_id = req_json.get('threadId')
        msg_text = req_json.get('text')

        if not all([thread_id, sender_id, msg_text]):
            return jsonify({'error': 'Missing required fields'}), 400


        now = datetime.now(timezone.utc)


        message_data = {
            'messageId': message_id,
            'receiverId': receiver_id,
            'senderName': sender_name,
            'senderId': sender_id,
            'text': msg_text,
            'threadId': thread_id,
            'timestamp': now,
        }

        message_ref = fdb.collection('threads').document(thread_id).collection('messages').document(message_id)
        thread_ref = fdb.collection('threads').document(thread_id)




        # Write the message and update the thread's metadata
        batch = fdb.batch()
        batch.set(message_ref, message_data)
        batch.update(thread_ref, {
            'lastMessage': msg_text,
            'lastUpdated': now,
            'unread': firestore.ArrayUnion([receiver_id])
        })
        batch.commit()


        return jsonify({'status': 'success', 'messageId': message_id})
    
    except Exception as e:
        lg.e("Exp ~ " + str(e) + " trace ~ " + str(traceback.format_exc()))
        if debug_responses:
            return jsonify({'success': False,           
            'error': str(e),
            }), 500   
        else:
            return std_exception_response()