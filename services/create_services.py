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
def createService_fn(request):

    pdata = request.get_json()
    # lg.t("[createService_fn] with pdata ~ " + str(pdata))

    try:
        lg.t("[createService_fn] build service item")
        make_uuid = createUUIDMixedCase(16)

        get_location_type_safe = None
        if pdata.get("location"):        
            if "lat" in pdata.get("location") and "lng" in pdata.get("location"):
                get_location_type_safe = GeoPoint(
                                float(pdata.get("location")["lat"]),
                                float(pdata.get("location")["lng"])
                            )
        
        # keywords list is required, cant be null
        kw_list = clean(pdata.get("keywords"))

        if kw_list == None:
            kw_list = []

        # search_terms = []
        keywords_lower = []
        # for term in kw_list:
        #     search_terms.extend(term.split())

        cat_clean_get = "other"
        try:
            cat_clean_get = clean(pdata.get("category").lower())
            
        except:
            print("err converting category")

        if cat_clean_get != "other":
            keywords_lower.extend(cat_clean_get.split())

        # Add keywords after category seems better ordering
        for kw in kw_list:
            if kw not in keywords_lower: # avoid double adding category if they keyword it or add duplicate somehow
                keywords_lower.append(kw.lower())

        si = {
            "address": pdata.get("address"),
            "category" : cat_clean_get,
            "createTime": datetime.now(timezone.utc),
            "description" : pdata.get("description"),
            "email" : pdata.get("email"),
            "featureImageId": pdata.get("featureImageId"),
            "imageIds" : pdata.get("imageIds"),
            "geoHash" : pdata.get("geoHash"),
            "keywords" : keywords_lower,
            # "searchTerms": search_terms,
            "location": get_location_type_safe,
            "name": pdata.get("name"),
            "phoneNumber": pdata.get("phoneNumber"),
            "priceCents" : pdata.get("priceCents"),
            "radius": pdata.get("radius"),
            "rating": None,
            "ratingCount":0,
            "serviceId": make_uuid,
            "site" : pdata.get("site"),
            "timeLength" : pdata.get("timeLength"),
            "vendorUserId": pdata.get("vendorUserId"),
            "vendorBusinessName": pdata.get("vendorBusinessName"),
            "vendorUserName": pdata.get("vendorUserName"),

        }

        lg.t("service item ~ " + str(si))

        fdb.collection(service_collection).document(make_uuid).set(si)

        return jsonify({'success': True, "serviceId": make_uuid})

    except Exception as e:
        lg.e("Exp ~ " + str(e) + " trace ~ " + str(traceback.format_exc()))
        if debug_responses:
            return jsonify({'success': False,           
            'error': str(e),
            'trace': traceback.format_exc()
            }), 500   
        else:
            return std_exception_response()