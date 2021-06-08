from django_koldar_utils.graphql.ErrorCode import ErrorCode

NO_ERROR = ErrorCode(0, "No error", [])
USERNAME_PRESENT = ErrorCode(1, "User already persent in database!", [])
BACKEND_ERROR = ErrorCode(2, "Standard Python exception occured. This is for sure a problem on the server!", [])
FORGET_TOKEN_ALREADY_SENT = ErrorCode(3, "A forget token has already been sent.", [])
INVALID_FORGET_TOKEN = ErrorCode(4, "Invalid forget password token", [])
OBJECT_ALREADY_PRESENT = ErrorCode(5, "Object is already stored in the persistence storage", ["object", "values"])
CREATION_FAILED = ErrorCode(6, "Insertion of a row in the database has failed", ["object", "values"])
OBJECT_NOT_FOUND = ErrorCode(7, "Object not found", ["object", "values"])