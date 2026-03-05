from firebase_admin import firestore
from flask import request, jsonify
from common import fdb
from settings import *
from datetime import datetime, timezone
from util.collection import clean
from firebase_admin.firestore import GeoPoint, FieldFilter
import traceback


distanceToPrecision = {
    5: 5,
    39: 4,
    156: 3,
    1250: 2,                
    5000: 1,
  }


def getServices_fn(request):
    limit = 10
    pdata = request.get_json()
    lg.t("[getServices_fn] with pdata ~ " + str(pdata))
    try:
        category = clean(pdata.get("category"))
        keywords = clean(pdata.get("keywords"))
        rating = clean(pdata.get("rating"))
        lastGeoHash = clean(pdata.get("lastGeoHash"))
        lastDocId = clean(pdata.get("lastDocId"))
        distanceMetric = clean(pdata.get("distanceMetric"))
        lg.t("[getServices_fn] continue to query build")
        query = fdb.collection(service_collection)
        # === Determine geohash prefix length ===
        prefixLen = 1
        if distanceMetric:
            lg.t("[getServices_fn] found distanceMetric")
            try:
                prefixLen = distanceToPrecision.get(int(distanceMetric), 1)
            except (ValueError, TypeError):
                lg.e("[getServices_fn] Invalid distanceMetric; falling back to prefixLen = 1")

        if category:
            lg.t("[getServices_fn] found category")
            query = query.where('category', '==', category.lower())
            lg.t(f"[getServices_fn] Filtering by category: {category}")

        if rating:
            lg.t("[getServices_fn] found rating")
            try:
                rating_f = float(rating)
                query = query.where('rating', '>=', rating_f)
                lg.t(f"[getServices_fn] Filtering by rating >= {rating_f}")
            except (ValueError, TypeError):
                lg.e("[getServices_fn] Invalid rating value")

        if keywords:
            if isinstance(keywords, list) and keywords:
                keywords_lower = [str(kw).lower() for kw in keywords]
                query = query.where('keywords', 'array_contains_any', keywords_lower)
                lg.t(f"[getServices_fn] Filtering by keywords: {keywords_lower}")
            else:
                lg.e("[getServices_fn] Invalid keywords: must be a non-empty list")

        useGeoHashPagination = bool(lastGeoHash)

        if useGeoHashPagination:
            lg.t("[getServices_fn] found lastGeoHash")
            prefix = lastGeoHash[:prefixLen]
            query = query.where('geoHash', '>=', prefix) \
                         .where('geoHash', '<=', prefix + '\uf8ff') \
                         .order_by('geoHash')
                         
                        #  .order_by('__name__')  # document ID
            lg.t(f"[getServices_fn] Using geoHash prefix: {prefix} (precision={prefixLen})")

            if lastDocId:
                query = query.start_after([prefix])
                lg.t(f"[getServices_fn] Paginating with geoHash and docId: {lastDocId}")
        
        elif not (category or keywords or rating):
            lg.t("[getServices_fn] not category or keywords or rating")
            # ✅ Only use __name__ ordering when no other filters are applied
            query = query.order_by('__name__')
            if lastDocId:
                lg.t("[getServices_fn] found query lastDocId")
                query = query.start_after({ '__name__': lastDocId })
                lg.t(f"[getServices_fn] Paginating with docId only: {lastDocId}")
        else:
            lg.t("[getServices_fn] run else")
            # 🚫 Do not use order_by(__name__) if filters exist and no geohash
            if lastDocId:
                lg.t("[getServices_fn] Skipping pagination because __name__ ordering is unsafe with filters")

        # === Execute query ===
        lg.t("[getServices_fn] getServicesFn query ready, streaming...")
        docs = query.limit(limit).stream()

        services = []
        for doc in docs:
            data = doc.to_dict()
            # lg.t("[getServices_fn] appending doc ~ " + str(data))
            data['id'] = doc.id
            if "createTime" in data and hasattr(data["createTime"], "isoformat"):
                data["createTime"] = data["createTime"].isoformat().replace('+00:00', 'Z')
            if 'location' in data and isinstance(data['location'], GeoPoint):
                data["location"] = {
                    'lat': data['location'].latitude,
                    'lng': data['location'].longitude
                }
            services.append(data)
            # lg.t("[getServices_fn] appending doc ~ " + str(data))

        lg.t("[getServices_fn] returning services len ~ " + str(len(services)))
        response = {'success': True,
        'services': services,
        }

        response['lastGeoHash'] = None
        response['lastDocId'] = None

        if len(services)> 0:
            for s in services[::-1]:
                if 'geoHash' in s:
                    response['lastGeoHash'] = s["geoHash"]
                    break
            response['lastDocId'] = services[-1]["id"]

        return jsonify(response)

    except Exception as e:
        lg.e("Exp ~ " + str(e) + " trace ~ " + str(traceback.format_exc()))
        if debug_responses:
            return jsonify({'success': False,           
            'error': str(e),
            'trace': traceback.format_exc()
            }), 500   
        else:
            return std_exception_response()



def getRemoteServices_fn(request):
    limit = 10
    pdata = request.get_json()
    lg.t("[getRemoteServices_fn] with pdata ~ " + str(pdata))
    try:
        category = clean(pdata.get("category"))
        keywords = clean(pdata.get("keywords"))
        rating = clean(pdata.get("rating"))
        # lastGeoHash = clean(pdata.get("lastGeoHash"))
        lastDocId = clean(pdata.get("lastDocId"))
        # distanceMetric = clean(pdata.get("distanceMetric"))
        lg.t("[getRemoteServices_fn] continue to query build")
        query = fdb.collection(service_collection)


        if category:
            lg.t("[getRemoteServices_fn] found category")
            query = query.where('category', '==', category.lower())
            lg.t(f"[getRemoteServices_fn] Filtering by category: {category}")

        if rating:
            lg.t("[getRemoteServices_fn] found rating")
            try:
                rating_f = float(rating)
                query = query.where('rating', '>=', rating_f)
                lg.t(f"[getRemoteServices_fn] Filtering by rating >= {rating_f}")
            except (ValueError, TypeError):
                lg.e("[getRemoteServices_fn] Invalid rating value")

        if keywords:
            if isinstance(keywords, list) and keywords:
                keywords_lower = [str(kw).lower() for kw in keywords]
                query = query.where('keywords', 'array_contains_any', keywords_lower)
                lg.t(f"[getRemoteServices_fn] Filtering by keywords: {keywords_lower}")
            else:
                lg.e("[getRemoteServices_fn] Invalid keywords: must be a non-empty list")


        
        if not (category or keywords or rating):
            lg.t("[getRemoteServices_fn] not category or keywords or rating")
            # ✅ Only use __name__ ordering when no other filters are applied
            query = query.order_by('__name__')
            if lastDocId:
                lg.t("[getRemoteServices_fn] found query lastDocId")
                query = query.start_after({ '__name__': lastDocId })
                lg.t(f"[getRemoteServices_fn] Paginating with docId only: {lastDocId}")
        else:
            lg.t("[getRemoteServices_fn] run else")
            # 🚫 Do not use order_by(__name__) if filters exist and no geohash
            if lastDocId:
                lg.t("[getRemoteServices_fn] Skipping pagination because __name__ ordering is unsafe with filters")

        query = query.where('site', '==', 'remote')

        # === Execute query ===
        lg.t("[getRemoteServices_fn] getServicesFn query ready, streaming...")
        docs = query.limit(limit).stream()

        services = []
        for doc in docs:
            data = doc.to_dict()
            # lg.t("[getRemoteServices_fn] appending doc ~ " + str(data))
            data['id'] = doc.id
            if "createTime" in data and hasattr(data["createTime"], "isoformat"):
                data["createTime"] = data["createTime"].isoformat().replace('+00:00', 'Z')
            if 'location' in data and isinstance(data['location'], GeoPoint):
                data["location"] = {
                    'lat': data['location'].latitude,
                    'lng': data['location'].longitude
                }
            services.append(data)
            # lg.t("[getRemoteServices_fn] appending doc ~ " + str(data))

        lg.t("[getRemoteServices_fn] returning services len ~ " + str(len(services)))
        response = {'success': True,
        'services': services,
        }

        response['lastDocId'] = None

        if len(services)> 0: 
            response['lastDocId'] = services[-1]["id"]

        return jsonify(response)

    except Exception as e:
        lg.e("Exp ~ " + str(e) + " trace ~ " + str(traceback.format_exc()))
        if debug_responses:
            return jsonify({'success': False,           
            'error': str(e),
            'trace': traceback.format_exc()
            }), 500   
        else:
            return std_exception_response()



def getVendorServices_fn(request):
    try:
        pdata = request.get_json()
        lg.t("getVendorServices_fn called w pdata ~ " + str(pdata))

        lg.t("getVendorServices_fn start query ~ ")
        query = fdb.collection('services') \
            .where(filter=FieldFilter("vendorUserId", "==", pdata['vendorUserId'])) \
            .order_by('createTime', direction=firestore.Query.DESCENDING)
        #             .filter(field_path='vendorUserId', op_string='==', value=pdata['vendorUserId']) \

        lg.t("getVendorServices_fn fin query ~ ")
        docs = query.stream()

        services = []
        for doc in docs:
            data = doc.to_dict()
            data['id'] = doc.id
            data["createTime"] = data["createTime"].isoformat().replace('+00:00', 'Z')
            if "location" in data:
                if isinstance(data['location'], GeoPoint):
                    data["location"] = {'lat': data['location'].latitude, 'lng': data['location'].longitude}
            services.append(data)

        lg.t("returning services len ~ " + str(len(services)))
        response = {'success': True,
        'services': services,
        }

        return jsonify(response)

    except Exception as e:
        lg.e("Exp ~ " + str(e) + " trace ~ " + str(traceback.format_exc()))
        if debug_responses:
            return jsonify({'success': False,           
            'error': str(e),
            'trace': traceback.format_exc()
            }), 500   
        else:
            return std_exception_response()