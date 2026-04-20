from firebase_admin import firestore
from flask import request, jsonify
from common import fdb
from settings import *
from datetime import datetime, timezone
from util.collection import clean
from firebase_admin.firestore import GeoPoint, FieldFilter
import traceback
from auth.auth_user_wrapper import uauth


# Not called anymore, IP change to frequently to be useful 
def trackMeta_fn(request):
    try:
        if not request.is_json:
            return jsonify({"error": "Invalid request"}), 400

        data = request.get_json()
        if data.get("action") != "login":
            return jsonify({"error": "Invalid action"}), 400

        ip_address_full = request.headers.get('X-Forwarded-For', request.remote_addr)
        if ',' in ip_address_full:
            ip_address = ip_address_full.split(',')[0].strip()
        else:
            ip_address = ip_address_full

        now = datetime.now(timezone.utc)

        doc_ref = fdb.collection("track_meta").document(ip_address)
        doc = doc_ref.get()

        if doc.exists:
            doc_ref.update({
                "lastLoginAt": now,
                "fullIp": ip_address_full,
                "loginCount": firestore.Increment(1)
            })
        else:
            doc_ref.set({
                "lastLoginAt": now,
                "fullIp": ip_address_full,
                "loginCount": 1
            })

        return jsonify({"message": f"Login from IP {ip_address} logged."}), 200
    except Exception as e:
        lg.e("Exp ~ " + str(e) + " trace ~ " + str(traceback.format_exc()))
        return jsonify({'success': False,           
        'error': str(e),
        }), 500   