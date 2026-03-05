from proto.datetime_helpers import DatetimeWithNanoseconds
import traceback
import copy
import datetime
from util.hash_methods import createUUIDLower
from firebase_admin import auth
from settings import *
from common import fdb

def seedTestUsers_fn(request):
    try:
        pdata = request.get_json()

        if pdata.get("password") != admin_utils_password:
            return jsonify({"success": False, "reason": "Unauthorized"}), 401


        dt_retro = datetime.datetime(2025, 6, 9, 19, 7, 1, 438689)

        """
        required
            required String userName,
            required UserType userType,
        """

        clientTestUserId = "cp5t39isqq0euy7sgkrw4u7l"
        vendorTestUserId = "vp5t39isqq0euy7sgkrw4u7l"
        create_client_user_doc = {"userName": "Caroline",
                            "accountLevel": "free",
                            "purchaseEver": False,
                            "userId": clientTestUserId,
                            "createTime": dt_retro,
                            "userEmail": "c_test_email@connectme.dev",
                                       "userType": "client",
                            "firebaseUserId": "a_test_firebase_uid_client",
                             "platformDesc": "seedUser", # not checked for anything yet
                            "token": "c3bickid3dmr2ivodnby84b56sz5btoc",
                            "userMeta":{
                                "userType":"client",
                                "userName": "Caroline"
                            }
                            }

        """
        required
            required String userName,
            required UserType userType,
        """

        create_vendor_user_doc = {"userName": "Vanessa",
                            "accountLevel": vendor_account_sub_status_string,
                            "purchaseEver": True,
                            "userId": vendorTestUserId,
                            "createTime": dt_retro,
                            "userEmail": "v_test_email@connectme.dev",
                            "userType": "vendor",
                            "firebaseUserId": "a_test_firebase_uid_vendor",
                            "platformDesc": "seedUser", # not checked for anything yet
                            "token": "v3bickid3dmr2ivodnby84b56sz5btov",        
                            "userMeta":{
                                "userType":"vendor",
                                "userName": "Vanessa"
                            }
                            }


        fdb.collection(user_collection).document(clientTestUserId).set(create_client_user_doc)

        fdb.collection(user_collection).document(vendorTestUserId).set(create_vendor_user_doc)

        return jsonify({"success": True,
                        "reason": "firebase test users seeded"}, )

    except Exception as e:
        lg.e("Exception caught ~ ", str(e))
        # traceback.print_exc()
        if debug_responses:
            return jsonify({"success": False, "reason": str(e)}, ), 500
        else:
            return std_exception_response()