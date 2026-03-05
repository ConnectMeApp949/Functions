
from proto.datetime_helpers import DatetimeWithNanoseconds
import traceback
import copy
from datetime import datetime, timezone
from time import time
from util.hash_methods import createUUIDLower, hashItemAsUUID
from firebase_admin import auth
from settings import *
from common import fdb
from firebase_admin import auth, initialize_app, get_app


"""
An iOS app store review 
        "full decced jwtoken ~ {'iss': 'https://securetoken.google.com/connectme-app-11465', 'aud': 'connectme-app-11465', 'auth_time': 1757248657, 'user_id': 'ueH52W97nSTtVaqbxcgLOse0QJf1', 'sub': 'ueH52W97nSTtVaqbxcgLOse0QJf1', 'iat': 1757248657, 'exp': 1757252257, 'firebase': {'identities': {'apple.com': ['001189.9c0d78389c454951909631cf8c2f187e.1237']}, 'sign_in_provider': 'apple.com'}, 'uid': 'ueH52W97nSTtVaqbxcgLOse0QJf1'}"

A facebook login
        full decced jwtoken ~ {'name': 'Ryan Adrig', 'picture': 'https://graph.facebook.com/10240829952473166/picture', 'iss': 'https://securetoken.google.com/connectme-app-11465', 'aud': 'connectme-app-11465', 'auth_time': 1751501881, 'user_id': 'ZLSgiLwO5qWr8hZCL5yNXKOkuFW2', 'sub': 'ZLSgiLwO5qWr8hZCL5yNXKOkuFW2', 'iat': 1751501881, 'exp': 1751505481, 'email': 'ryanadrig@gmail.com', 'email_verified': False, 'firebase': {'identities': {'facebook.com': ['10240829952473166'], 'email': ['ryanadrig@gmail.com']}, 'sign_in_provider': 'facebook.com'}, 'uid': 'ZLSgiLwO5qWr8hZCL5yNXKOkuFW2'}

A google login
        full decced jwtoken ~ {'name': 'Ryan Adrig', 'picture': 'https://lh3.googleusercontent.com/a/ACg8ocKUomcUB9Ogli2rEjKAdRqakQC5bSCVNYgO2_ZzMZ1iB--O9g=s96-c', 'iss': 'https://securetoken.google.com/connectme-app-11465', 'aud': 'connectme-app-11465', 'auth_time': 1757197453, 'user_id': 'wR6cnmazNRY4vs2MFT45bZJILMM2', 'sub': 'wR6cnmazNRY4vs2MFT45bZJILMM2', 'iat': 1757197453, 'exp': 1757201053, 'email': 'ryanadrig@gmail.com', 'email_verified': True, 'firebase': {'identities': {'google.com': ['112131602195922675429'], 'email': ['ryanadrig@gmail.com']}, 'sign_in_provider': 'google.com'}, 'uid': 'wR6cnmazNRY4vs2MFT45bZJILMM2'}

"""

"""Allegedly need this if firebase is not 'touched'"""
try:
    get_app()
except ValueError:
    initialize_app()


def loginWithGoogle_fn(request):
    try:
        pdata = request.get_json()
        lg.t("loginWithGoogle called with pdata ~ " + str(pdata))

        required_args = [ "firebaseUid", "firebaseIdToken"]

        for required_arg in required_args:
            if required_arg not in pdata:
                if debug_responses:
                    return jsonify({"success": False, "reason": f"{required_arg} not found in request"}), 400
                else:
                    return jsonify({"success": False, "reason": "request failed"}, ), 500

        user_dict = {}

        get_fb_id_token = pdata.get("firebaseIdToken")

        try:
            # returns dict of key value pairs from parsed JWT
            decoded_token = auth.verify_id_token(get_fb_id_token)
        except Exception as e:
            lg.e("could not verify id token exception ~ " + str(e))
            return jsonify({"success": False,
                            "reason": "firebase token unverified"}), 404

        lg.t("full decced jwtoken ~ " + str(decoded_token))
        identities = None
        
        # not really used
        if "google.com" in decoded_token['firebase']['identities']:
            identities = decoded_token['firebase']['identities']['google.com'][0] 

        if "facebook.com" in decoded_token['firebase']['identities']:
            identities = decoded_token['firebase']['identities']['facebook.com'][0] 

        if "apple.com" in decoded_token['firebase']['identities']:
            identities = decoded_token['firebase']['identities']['apple.com'][0] 

        get_jwt_user_email = None
        if pdata.get("firebaseUserEmail") != None:
            get_jwt_user_email = pdata.get("firebaseUserEmail")
        elif "email" in decoded_token:
            get_jwt_user_email = decoded_token['email']
        elif "email" in decoded_token["firebase"]:
            get_jwt_user_email = decoded_token['firebase']['email'][0]
        
        lg.t("get_jwt_user_email ~ " + str(get_jwt_user_email))
        
        get_jwt_user_id = None
        if "user_id" in decoded_token:
            get_jwt_user_id = decoded_token["user_id"]

        lg.t("get_jwt_user_id ~ " + str(get_jwt_user_id))
        
        # if email not available to iOS users use user_id
        if get_jwt_user_email == None:
            get_jwt_user_email = get_jwt_user_id + "@placeholder.com"
        
        if get_jwt_user_email == None or get_jwt_user_id == None:
            return jsonify({"success": False,
                            "reason": "auth failed to find email or id"})

        lg.t("lookup user id ~ " + str(get_jwt_user_id))
        users_ref = fdb.collection(user_collection)
        # use hash of email for user id

        user_hash_id = hashItemAsUUID(28, get_jwt_user_email)
        lg.t("hashed email ~ " + str(user_hash_id))
        # uq_res = users_ref.where("firebaseUserId", "==", get_jwt_user_id ).get()
        uqh_it = users_ref.document(user_hash_id).get() # user query hash item


        lg.t("check uq res")

        if not uqh_it.exists:
            lg.t("return user not found resp")
            return jsonify({"success": True,
                "userFound": False,
                "reason": "user not found"})

        lg.t("found uq res")
        # create a new token and insert with doc`
        # if len(uq_res) == 1:
        lg.t("found user doc")

        lg.t("create token")
        cr_token = createUUIDLower(32)
        user_dict = uqh_it.to_dict()

        lg.t("do metrics")
        newest_login = datetime.now(timezone.utc)
        # login_history = uqh_it.to_dict().get("loginHistory",[])
        # last_login = uqh_it.to_dict().get("lastLogin")

        # start rate limiting check
        # need to add to any other login methods
        ip_address_full = request.headers.get('X-Forwarded-For', request.remote_addr)
        
        # current_ip_array = uqh_it.get("ip_address", [])
        current_lh_array = user_dict.get("loginHistory", [])

        if not isinstance(current_lh_array, list):
            current_lh_array = [current_lh_array]

        # if ip_address_full not in current_lh_array:
        # rather see multiple last logins from same ip
        login_history = current_lh_array[-8:]
        # user_ref.update({"ip_address": firestore.ArrayUnion([ip_address_full])})
        new_lh_entry = {"ip": ip_address_full, "timestamp": newest_login}
        login_history.append(new_lh_entry)
        # user_ref.update({"ip_address": update_array })
        # user_dict["ip_address"] = update_array
        # login_history = update_array

        # end rate limiting check

        curr_millis = int(time() * 1000)

        # start subscription downgrade check
        millisPerMinute = 60000
        millisPerHour = 3600000
        hoursPerDay = 24
        daysPerMonth = 30

        lg.t("check acct levl")
        if user_dict["accountLevel"] != "free":
            lg.t("check sconfig optns")
            if "sConfigOptions" in pdata:
                lg.t("check sandbx timing")
                if pdata.get("sConfigOptions").get("useSandboxSubTiming"):
                    lg.t("found config options use sandbox timing")
                    if not user_dict.get("latestPurchaseTimeMillis"):
                        lg.e("Need latest purchase millis should be set err")
                    else:
                        lg.t("purchaseMillis found")
                        if  (curr_millis - user_dict.get("latestPurchaseTimeMillis") ) > ( millisPerMinute * 3 ):
                            lg.t("sbx sub up downgrade")
                            user_dict["accountLevel"] = "free"
                        else:
                            lg.t("sub current with sandbox timing")

                else:
                    lg.t("use normal timing")
                    if not user_dict.get("latestPurchaseTimeMillis"):
                        lg.e("Need latest purchase millis should be set err")
                    else:
                        lg.t("purchaseMillis found")
                        if (  curr_millis - user_dict.get("latestPurchaseTimeMillis") ) > ( millisPerHour * hoursPerDay * daysPerMonth ):
                            lg.t("sbx sub up downgrade")
                            user_dict["accountLevel"] = "free"
                        else:
                            lg.t("sub current with normal timing")

            else:
                lg.t("config options not set")




        lg.t("Resping")                
        # set new tokens
        user_dict["token"] = cr_token
        user_dict["firebaseIdToken"] = get_fb_id_token
        # set other user data
        user_dict["userEmail"] = get_jwt_user_email
        user_dict["loginHistory"] = login_history 
        

        ins_dict = user_dict 

        # lg.t("set users_ref doc ~ " + str(ins_dict))

        users_ref.document(uqh_it.id).set(ins_dict)

        lg.t("user login success")

        return jsonify({"success": True,
                        "userFound": True,
                        "reason": "user found",
                        "data": ins_dict,
                        "jwtData": decoded_token
                        })


        # else:
        #     return jsonify({"success": False,
        #                     "userFound": False,
        #                     "reason": "multiple user documents",
        #                     }, ), 500


    except Exception as e:
        lg.e("Exception caught ~ ", str(e))
        if debug_responses:
            return jsonify({"success": False, "reason": str(e)}, ), 500
        else:
            return std_exception_response()



# Need to verify with revenue cat later
"""
import requests

def verify_subscription(app_user_id):
    response = requests.get(
        f"https://api.revenuecat.com/v1/subscribers/{app_user_id}",
        headers={"Authorization": "Bearer YOUR_REVENUECAT_API_KEY"}
    )
    data = response.json()
    entitlements = data["subscriber"]["entitlements"]
    
    # You can check if your entitlement is active
    if "premium_access" in entitlements and entitlements["premium_access"]["expires_date"] is not None:
        return True
    return False
    
"""


# Creates a new user using a firebase auth token 
def createAccountFirebaseToken_fn(request):
    try:
        pdata = request.get_json()
        required_args = ["userName", 
        "userEmail", "userType", "firebaseUid", "firebaseIdToken"]

        for required_arg in required_args:
            if required_arg not in pdata:
                if debug_responses:
                    return jsonify({"success": False, "reason": f"{required_arg} not found in request"}), 400
                else:
                    return jsonify({"success": False, "reason": "request failed"}, ), 500

        get_fb_id_token = pdata["firebaseIdToken"]

        try:
            # returns dict of key value pairs from parsed JWT
            decoded_token = auth.verify_id_token(get_fb_id_token)
        except Exception as e:
            lg.e("did not find user, uid is incorrect or user DNE")

        userName = pdata["userName"]
        userEmail = pdata["userEmail"]
        userType = pdata["userType"]
        fb_userID =   pdata["firebaseUid"]

        if userEmail == no_email_hash_seed_placeholder_email:
            lg.t("found not found email creating uid for hash")
            userEmail = fb_userID + "@placeholder.com"


        # looks for existing user with name,
        users_ref = fdb.collection(user_collection)
        uq_res = users_ref.where("userName", "==", userName).get()
        if len(uq_res) > 0:
            return jsonify({"success": True,
                            "reason": "user name exists"}, )

        users_ref = fdb.collection(user_collection)
        # uq_res = users_ref.where("userName", "==", pdata["userName"]).get()

        create_user_doc = {}
        un_id_exist_or_create = None

        platformDesc = "pd::" + str(pdata.get("platformDesc"))
        
        # un_id_exist_or_create = createUUIDLower(32)
        un_id_exist_or_create = hashItemAsUUID(28, userEmail)


        # start rate limiting check
        newest_login = datetime.now(timezone.utc)
        ip_address_full = request.headers.get('X-Forwarded-For', request.remote_addr)
        new_lh_entry = {"ip": ip_address_full, "timestamp": newest_login}
        login_history= [new_lh_entry]

        create_user_doc = {"userName": userName,
                            "accountLevel": "free",
                            "purchaseEver": False,
                            "userId": un_id_exist_or_create,
                            "createTime": datetime.now(timezone.utc),
                            "userEmail": userEmail,
                            "userType": userType,
                            "platformDesc": platformDesc,
                            "firebaseUserId": fb_userID,
                            "userMeta": {"userType": userType,
                                         "userName": userName,
                                         },
                            "loginHistory": login_history,

                            }


        ctoken = createUUIDLower(32)
        create_user_doc["firebaseUserId"] = fb_userID
        create_user_doc["firebaseIdToken"] = get_fb_id_token
        create_user_doc["token"] = ctoken

        fdb.collection(user_collection).document(un_id_exist_or_create).set(create_user_doc)

        return jsonify({"success": True,
                        "data": create_user_doc,
                        "reason": "firebase user created"}, )

    except Exception as e:
        lg.e("Exception caught ~ ", str(e))
        # traceback.print_exc()
        if debug_responses:
            return jsonify({"success": False, "reason": str(e)}, ), 500
        else:
            return std_exception_response()