from firebase_functions import https_fn
from messages.send_message import sendMessage_fn
from messages.get_threads import getMessageThreads_fn
from messages.get_or_create_thread import getOrCreateThread_fn
from messages.get_messages import getMessages_fn
from messages.block_and_report import blockThread_fn, reportMessageUser_fn
from messages.mark_thread_read import markThreadAsRead_fn
from common import common_cors


@https_fn.on_request(cors=common_cors)
def getMessageThreads(req: https_fn.Request) -> https_fn.Response:
    return getMessageThreads_fn(req)

@https_fn.on_request(cors=common_cors)
def getMessages(req: https_fn.Request) -> https_fn.Response:
    return getMessages_fn(req)

@https_fn.on_request(cors=common_cors)
def sendMessage(req: https_fn.Request) -> https_fn.Response:
    return sendMessage_fn(req)

@https_fn.on_request(cors=common_cors)
def getOrCreateThread(req: https_fn.Request) -> https_fn.Response:
    return getOrCreateThread_fn(req)

@https_fn.on_request(cors=common_cors)
def blockThread(req: https_fn.Request) -> https_fn.Response:
    return blockThread_fn(req)

@https_fn.on_request(cors=common_cors)
def reportMessageUser(req: https_fn.Request) -> https_fn.Response:
    return reportMessageUser_fn(req)

@https_fn.on_request(cors=common_cors)
def markThreadAsRead(req: https_fn.Request) -> https_fn.Response:
    return markThreadAsRead_fn(req)
