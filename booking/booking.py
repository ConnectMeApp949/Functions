from firebase_admin import firestore
from flask import request, jsonify
from common import fdb
from settings import *
from datetime import datetime, timezone
import traceback
from auth.auth_user_wrapper import uauth


# Takes either  elif 'startDate' in pdata and 'endDate' in pdata: for calendar
# or 'lastBookingTime' in pdata: for booking list
@uauth
def getBookings_fn(request):
    try:
        lg.t("getBookings_fn called")
        pdata = request.get_json()

        limit = 10

        user_id = pdata['userId']

        userIdForOwner = "clientUserId"
        if pdata['ownerType'] == "vendor":
            userIdForOwner = "vendorUserId"

        lg.t("query with userId ~ " + str(user_id))
        lg.t("query with userIdForOwner ~ " + str(userIdForOwner))

        query = fdb.collection(booking_collection) \
                          .where(userIdForOwner, '==', user_id)

        lg.t("made query start bookingtime lookup")
        if 'lastBookingTime' in pdata:
            if pdata['upcomingOrPast'] == "upcoming":
                direction = firestore.Query.ASCENDING
            else:
                direction = firestore.Query.DESCENDING
            last_booking_time_str = pdata['lastBookingTime']
#             lg.t("last_booking_time_str not null")
            last_booking_time = datetime.fromisoformat(last_booking_time_str.rstrip('Z')).replace(tzinfo=timezone.utc)
#             lg.t("query with last_booking_time ~ " + str(last_booking_time))

            query = query.order_by('bookingTime', direction=direction).start_after([last_booking_time])
#             query = query.start_after([last_booking_time])
            # Booking time is descending, so this paginates backward

            docs = query.limit(limit).stream()

            lg.t("check start and end dates")
        
        # For calendar
        elif 'startDate' in pdata and 'endDate' in pdata:
            lg.t("get by start and end date")
            start_date = datetime.fromisoformat(pdata['startDate']).replace(tzinfo=timezone.utc)
            end_date = datetime.fromisoformat(pdata['endDate']).replace(tzinfo=timezone.utc)
            lg.t("start date ~ " + str(start_date))
            lg.t("end date ~ " + str(end_date))
            query = query.where('bookingTime', '>=', start_date).where('bookingTime', '<=', end_date)
            docs = query.stream()


        bookings = []                               
        for doc in docs:
            data = doc.to_dict()
            data['id'] = doc.id
            if "createTime" in data:
                data["createTime"] = data["createTime"].isoformat().replace('+00:00', 'Z')
            if "bookingTime" in data:
                data["bookingTime"] = data["bookingTime"].isoformat().replace('+00:00', 'Z')
            bookings.append(data)

        lg.t("make bookings list with len ~ " + str(len(bookings)))

        return jsonify({'success': True, 'bookings': bookings})

    except Exception as e:
        lg.e("Exp ~ " + str(e) + " trace ~ " + str(traceback.format_exc()))
        return jsonify({'success': False,           
        'error': str(e),
        'trace': traceback.format_exc()
        }), 500   
    




@uauth
def getBookingByID_fn(request):
    try:
        lg.t("getBookingByID_fn called")
        pdata = request.get_json()

        user_id = pdata['userId']

        bookingId = pdata["bookingId"]

        lg.t("query with userId ~ " + str(user_id))

        booking_doc = fdb.collection(booking_collection).document(bookingId).get()
        
        if not booking_doc.exists:
            return jsonify({'success': False, 'bookings': []})
        
        data = booking_doc.to_dict()

        if "createTime" in data:
            data["createTime"] = data["createTime"].isoformat().replace('+00:00', 'Z')
        if "bookingTime" in data:
            data["bookingTime"] = data["bookingTime"].isoformat().replace('+00:00', 'Z')

        booking = data

        return jsonify({'success': True, 'bookings': [ booking ]})

    except Exception as e:
        lg.e("Exp ~ " + str(e) + " trace ~ " + str(traceback.format_exc()))
        return jsonify({'success': False,           
        'error': str(e),
        'trace': traceback.format_exc()
        }), 500   