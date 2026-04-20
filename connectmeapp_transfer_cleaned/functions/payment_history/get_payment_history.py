
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


# fdb.collection(stripe_receipts_collection).document(intent.id).set({ 
#     "createTime": datetime.now(timezone.utc),
#     "client_stripe_customer_id": client_stripe_customer_id,
#     "client_payment_method_id": client_payment_method_id,
#     "client_user_id": client_user_id,
#     "vendor_stripe_account_id": vendor_stripe_account_id,
#     "vendor_user_id": vendor_user_id,
#     "payment_amount_cents": payment_amount_cents,
#     "payment_intent_id": intent.id,
#     "service_id": service_id,
#     "booking_id": booking_id,
#     "service_name": bi.get("serviceName"),
#     "vendor_business_name": bi.get("vendorBusinessName"),
# })



@uauth
def getPaymentsHistory_fn(request):

    try:

        pdata = request.get_json()
        lg.t("[getPaymentsHistory_fn] with pdata ~ " + str(pdata))   

        user_id = pdata.get("userId")

        client_or_vendor_id = "vendor_user_id"
        if pdata.get("clientOrVendor") == "client":
            client_or_vendor_id = "client_user_id"      
        elif pdata.get("clientOrVendor") == "vendor":
            client_or_vendor_id = "vendor_user_id"
                    
        
        lg.t("[getPaymentsHistory_fn] order query")
        query = fdb.collection(stripe_receipts_collection) \
            .where(client_or_vendor_id, "==", user_id)

        direction = firestore.Query.DESCENDING
        query = query.order_by('createTime', direction=direction)

        lg.t("[getPaymentsHistory_fn] stream query")
        docs = query.stream()

        lg.t("[getPaymentsHistory_fn] loop payments")
        payments_records = []
        for doc in docs:
            data = doc.to_dict()
            lg.t("looping payment doc data ~ " + str(data))
            data["createTime"] = data["createTime"].isoformat().replace('+00:00', 'Z')
            payments_records.append(data)
        lg.t("returning ratings len ~ " + str(len(payments_records))) 

        return jsonify({'success': True, "records": payments_records}) 

    except Exception as e:
        lg.e("Exp ~ " + str(e) + " trace ~ " + str(traceback.format_exc()))
        if debug_responses:
            return jsonify({'success': False,           
            'error': str(e),
            }), 500   
        else:
            return std_exception_response()