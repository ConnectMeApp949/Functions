import random, string
import hashlib


def createUUIDMixedCase(len):
    gen = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(len))
    return gen

def createUUIDLower(len):
    gen = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(len))
    return gen

def hashItemAsUUID(length, item):
    sha_1 = hashlib.sha1()
    hse = item.encode('utf-8')
    sha_1.update(hse)
    return sha_1.hexdigest()[0:length]