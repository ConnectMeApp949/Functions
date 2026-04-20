from firebase_admin import firestore, auth, storage
from flask import request, jsonify
from common import fdb
from settings import *
from datetime import datetime, timezone
from util.collection import clean
from firebase_admin.firestore import GeoPoint, FieldFilter
import traceback
from auth.auth_user_wrapper import uauth
from util.retry_methods import delete_blob_with_retry


# takes userId, authToken, userType and userEmail
@uauth
def userDeleteAccount_fn(request):
    pdata = request.get_json()
    lg.t("userDeleteAccount_fn with pdata ~ " + str(pdata))

    try:

        if pdata.get("userType") == "vendor":
            
            # Delete vendor service images and move services to deleted_services (for accounting)
            query = fdb.collection('services') \
                .where(filter=FieldFilter("vendorUserId", "==", pdata['userId'])) 

            lg.t("getVendorServices_fn fin query ~ ")
            docs = query.stream()

            bucket = storage.bucket()
            
            deleted_services = []
            for doc in docs:
                data = doc.to_dict()
                images_to_delete = doc.get("imageIds")

                for image_id in images_to_delete:
                    delete_blob_with_retry(bucket, image_id)

                fdb.collection(deleted_service_collection).document(doc.id).set(data)
                fdb.collection(service_collection).document(doc.id).delete()


        # Move user to deleted_users
        user_doc_ref =fdb.collection(user_collection).document(pdata['userId'])
        get_user_doc = user_doc_ref.get().to_dict()
        user_doc_ref.delete()
        fdb.collection(deleted_user_collection).document(pdata['userId']).set(get_user_doc)


        # Delete Firebase auth entries
        user_email = pdata.get("userEmail")
        user = auth.get_user_by_email(user_email)
        auth.delete_user(user.uid)
    
        return {"success": True}
    
    except Exception as e:
        lg.e("Exp ~ " + str(e) + " trace ~ " + str(traceback.format_exc()))
        if debug_responses:
            return jsonify({'success': False,           
            'error': str(e),
            }), 500   
        else:
            return std_exception_response()
    

def requestDataDeletion_fn(request):
    return """
<section aria-labelledby="data-deletion-heading" style="font-family:system-ui, -apple-system, 'Segoe UI', Roboto, Arial, sans-serif; max-width:700px; margin:16px auto; line-height:1.5; color:#111;">
  <h2 id="data-deletion-heading" style="font-size:1.25rem; margin-bottom:0.5rem;">Data Deletion & Developer Contact</h2>

    <p><strong></strong> ConnectMe App</p> 

  <p><strong>Developer:</strong> SigInfinite</p>

  <h3 style="margin-top:1rem; font-size:1rem;">How to request deletion</h3>
  <p>You can request deletion of your data in either of the following ways:</p>
  <ul>
    <li>Email app support at <a href="mailto:connectmeappevents@gmail.com" rel="noopener noreferrer">connectmeappevents@gmail.com</a> with "Delete my data" in the subject line.</li>
    <li>Or delete your account directly from the app by going to <em>Settings &gt; Account &gt; Delete account</em>. Deleting your account will remove all your user data.</li>
  </ul>

  <h4 style="margin-top:1rem;">What will be deleted</h4>
  <p>All user data associated with your account will be deleted upon a validated deletion request or when you delete your account in Settings. This includes (but is not limited to) profile information, uploaded content, preferences, and usage data.</p>

  <p style="font-size:0.9rem; color:#555; margin-top:1rem;">If you have questions about the deletion process or need confirmation, contact ConnectMe App support at <a href="mailto:connectmeappevents@gmail.com">connectmeappevents@gmail.com</a>.</p>
</section>
"""