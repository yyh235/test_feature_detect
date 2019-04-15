import os


"""
Msg queue wrapper of rabbitmq.
Provide easy to use APIs.
"""
class MsgQueue(object):
    def __init__(self):
        pass

    #private method start with '_'
    def _privateMethod(self):
        pass
    

    # public API
    def createQueue(self, que_name):
        """
        create queue with name que_name
        """
        pass
    
    def putQue(self, msg, que_name):
        """
        Put msg to que_name
        """
        pass
    
    def getQue(self, que_name):
        """
        Non-block get method. If que is empty, just return None
        """
        pass
    
