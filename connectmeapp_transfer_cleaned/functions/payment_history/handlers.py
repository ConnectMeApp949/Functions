from firebase_functions import https_fn
from common import common_cors
from payment_history.get_payment_history import getPaymentsHistory_fn



@https_fn.on_request(cors=common_cors)
def getPaymentsHistory(req: https_fn.Request) -> https_fn.Response:
    return getPaymentsHistory_fn(req)