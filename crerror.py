class CRBaseError(RuntimeError):
    pass

class CRCriticalError(CRBaseError):
    pass

class CRInputError(CRCriticalError):
    pass

class CRNotFoundError(CRCriticalError):
    pass

class CRCancelError(CRBaseError):
    pass

class CRMultiResultsError(CRBaseError):
    def __init__(self, results, msg):
        self.results = results
        self.msg = msg
        super().__init__(msg)

    def getResults(self):
        return self.results
