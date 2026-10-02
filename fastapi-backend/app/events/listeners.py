from app.events.emitter import event_emitter
from app.utils.logger import logger


def user_registered_listener(data):
   logger.info(
       "USER_REGISTERED event received | email=%s",
       data["email"],
   )


event_emitter.on(
    "auth:user-registered",
    user_registered_listener
)


def user_logged_in_listener(data):
    logger.info(
        "USER_LOGGED_IN event received | email=%s",
        data["email"],
    )


event_emitter.on(
    "auth:user-logged-in",
    user_logged_in_listener
)
