from firebase_functions import https_fn
from services.get_services import getServices_fn, getRemoteServices_fn, getVendorServices_fn
from services.create_services import createService_fn
from services.delete_service import deleteService_fn
from common import common_cors


@https_fn.on_request(cors=common_cors)
def getServices(req: https_fn.Request) -> https_fn.Response:
    return getServices_fn(req)

@https_fn.on_request(cors=common_cors)
def getRemoteServices(req: https_fn.Request) -> https_fn.Response:
    return getRemoteServices_fn(req)

@https_fn.on_request(cors=common_cors)
def getVendorServices(req: https_fn.Request) -> https_fn.Response:
    return getVendorServices_fn(req)


@https_fn.on_request(cors=common_cors)
def createNewService(req: https_fn.Request) -> https_fn.Response:
    return createService_fn(req)

@https_fn.on_request(cors=common_cors)
def deleteService(req: https_fn.Request) -> https_fn.Response:
    return deleteService_fn(req)
