from firebase_admin import firestore
from flask import request, jsonify
from common import fdb
from settings import *
from datetime import datetime, timezone
from firebase_admin.firestore import GeoPoint, FieldFilter
import traceback


def getAllBookings_fn(request):
    lg.t("getAllBookings_fn called method ~ " + request.method)
    try:

        query = fdb.collection(booking_collection) \
            .order_by('createTime', direction=firestore.Query.DESCENDING)
#             .where(filter=FieldFilter("vendorUserId", "==", pdata['vendorUserId'])) \

        docs = query.stream()

        bookings = []

        booking_names = []
        for doc in docs:
            data = doc.to_dict()

            booking_names.append(data['id'])

            data['id'] = doc.id
            data["createTime"] = data["createTime"].isoformat().replace('+00:00', 'Z')
            if "location" in data:
                if isinstance(data['location'], GeoPoint):
                    data["location"] = {'lat': data['location'].latitude, 'lng': data['location'].longitude}
            bookings.append(data)

        lg.t("returning bookings len ~ " + str(len(bookings)))

        booking_names.sort()

        lg.t("getAllBookings booking names ~ " + str(booking_names))

        response = {'success': True,
        'bookings': bookings,
        }


        return jsonify(response)

    except Exception as e:
        return jsonify({'success': False,
        'error': str(e),
        }), 500