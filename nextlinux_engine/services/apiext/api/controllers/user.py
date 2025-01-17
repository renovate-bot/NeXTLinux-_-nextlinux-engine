"""
API handlers for /user routes

These are handlers for routes available to standard users for managing their own credentials etc

"""

from nextlinux_engine.apis.authorization import get_authorizer
from nextlinux_engine.apis.context import ApiRequestContextProxy
from nextlinux_engine.common.helpers import make_response_error
from nextlinux_engine.db import UserAccessCredentialTypes, session_scope
from nextlinux_engine.services.apiext.api.controllers.accounts import (
    credential_db_to_msg,
    user_db_to_msg,
)
from nextlinux_engine.subsys import identities, logger

authorizer = get_authorizer()


@authorizer.requires([])
def get_user():
    """
    GET /user

    :return: User json object
    """
    try:
        with session_scope() as session:
            mgr = identities.manager_factory.for_session(session)
            usr = mgr.get_user(ApiRequestContextProxy.identity().username)
            return user_db_to_msg(usr), 200
    except Exception as ex:
        logger.exception("API Error")
        return make_response_error(errmsg=str(ex), in_httpcode=500), 500


@authorizer.requires([])
def get_credentials():
    """
    GET /user/credentials

    Fetches the credentials list for the authenticated user
    :return:
    """
    try:
        with session_scope() as session:
            mgr = identities.manager_factory.for_session(session)
            usr = mgr.get_user(ApiRequestContextProxy.identity().username)

            creds = [
                credential_db_to_msg(
                    usr.get("credentials")[UserAccessCredentialTypes.password]
                )
            ]
            if creds is None:
                return [], 200
            else:
                return creds, 200
    except Exception as ex:
        logger.exception("API Error")
        return make_response_error(errmsg=str(ex), in_httpcode=500), 500


@authorizer.requires([])
def add_credential(credential):
    """
    POST /user/credentials

    The same logic as /users/{userId}/credentials, but gets the userId from the auth context rather than path.
    This is for use by regular (non-admin) users to update their own credentials.
    :param credential:
    :return: credential json object

    """

    try:
        if credential["type"] != UserAccessCredentialTypes.password.value:
            return make_response_error("Invalid credential type", in_httpcode=400), 400
        else:
            cred_type = UserAccessCredentialTypes(credential["type"])

        with session_scope() as session:
            mgr = identities.manager_factory.for_session(session)
            user = ApiRequestContextProxy.identity().username
            result = mgr.add_user_credential(
                username=user, credential_type=cred_type, value=credential["value"]
            )
            return credential_db_to_msg(result), 200
    except Exception as ex:
        logger.exception("API Error")
        return make_response_error(errmsg=str(ex), in_httpcode=500), 500
