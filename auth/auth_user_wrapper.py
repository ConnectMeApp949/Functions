from firebase_admin import firestore
from firebase_functions import https_fn
from functools import wraps
from common import fdb
from settings import *


def uauth(fn):
    @wraps(fn)
    def wrapper(req: https_fn.Request) -> https_fn.Response:
        # lg.t("running auth wrapper")
        # Extract from headers or JSON
        body = req.get_json()
        # lg.t("req body ~ " + str(body))
        user_id = req.headers.get("userId") or req.get_json(silent=True, force=True).get("userId")
        auth_token = req.headers.get("authToken") or req.get_json(silent=True, force=True).get("authToken")

        if not user_id or not auth_token:
            lg.t("user id or token missing")
            return jsonify({"success":False,
                           "reason":"Unauthorized: Missing auth value"}),401

        # lg.t("find user doc")
        # Check user in Firestore
        user_ref = fdb.collection(user_collection).document(user_id)
        user_doc = user_ref.get()
        
        # lg.t("check exists")
        if not user_doc.exists:             
            lg.t("user doc not exist: unauthorized: user not found")          
            return jsonify({"success":False,
                           "reason":"Unauthorized: user not found"}), 401

        if user_doc.get("token") != auth_token:
            # lg.t("user token not correct ~ " + str(user_data.get("token")))
            # lg.t("compare ~ " + str(auth_token))
            return jsonify({"success":False,
                           "reason":"Unauthorized: incorrect credentials"}), 401
        

        user_dict = user_doc.to_dict()

        # start rate limiting check ( COMPARE TO LOGIN  removed for now)
        # ip_address_full = req.headers.get('X-Forwarded-For', req.remote_addr)
        
        # current_array = user_dict.get("ip_address", [])
        
        # if not isinstance(current_array, list):
        #     current_array = [current_array]

        # if ip_address_full not in current_array:
        #     update_array = current_array[-8:]
        #     # user_ref.update({"ip_address": firestore.ArrayUnion([ip_address_full])})
        #     update_array.append(ip_address_full)
        #     user_ref.update({"ip_address": update_array })

        # end rate limiting check



        # lg.t("continue function")
        # All good, proceed to the actual function          
        # response = fn(req)
        # return response
        return fn(req)
        # Optionally modify response headers
        # headers = dict(response.headers)

        # return https_fn.Response(
        #     response.get_data(),
        #     status=response.status_code,
        #     headers=headers,
        #     content_type=response.content_type,
        # )

    return wrapper





# import geoip2.database
# from flask import Request

# # Load the MaxMind database once at cold start
# reader = geoip2.database.Reader('GeoLite2-Country.mmdb')  # Use relative or GCS path

# def only_us_allowed(request: Request):
#     # Get IP address (check behind proxies like Cloudflare/Google LB)
#     ip = request.headers.get("X-Forwarded-For", request.remote_addr)
#     ip = ip.split(',')[0].strip()  # Take the first IP if multiple

#     try:
#         response = reader.country(ip)
#         country = response.country.iso_code
#     except geoip2.errors.AddressNotFoundError:
#         return ("Forbidden: IP not found", 403)

#     if country != "US":
#         return ("Access Denied: US Only", 403)

#     return "Access Granted"