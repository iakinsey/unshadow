from datetime import datetime
from json import JSONEncoder



class RPCEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        else:
            return super(RPCEncoder, self).default(obj)
