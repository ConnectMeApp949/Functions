from firebase_admin import firestore
from flask import request, jsonify
from common import fdb
from settings import *
from datetime import datetime, timezone
from firebase_admin.firestore import GeoPoint, FieldFilter
import traceback


def getAllServices_fn(request):
    try:

        query = fdb.collection('services') \
            .order_by('createTime', direction=firestore.Query.DESCENDING)
#             .where(filter=FieldFilter("vendorUserId", "==", pdata['vendorUserId'])) \

        docs = query.stream()

        services = []

        service_names = []
        for doc in docs:
            data = doc.to_dict()

            service_names.append(data['name'])

            data['id'] = doc.id
            data["createTime"] = data["createTime"].isoformat().replace('+00:00', 'Z')
            if "location" in data:
                if isinstance(data['location'], GeoPoint):
                    data["location"] = {'lat': data['location'].latitude, 'lng': data['location'].longitude}
            services.append(data)

        lg.t("returning services len ~ " + str(len(services)))

        service_names.sort()

        lg.t("getAllServices service names ~ " + str(service_names))

        response = {'success': True,
        'services': services,
        }


        return jsonify(response)

    except Exception as e:
        return jsonify({'success': False,
        'error': str(e),
        }), 500