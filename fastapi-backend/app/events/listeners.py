from app.events.emitter import event_emitter


def user_registered_listener(data):
    print(
        f"USER_REGISTERED event received: "
        f"{data['email']}"
    )


event_emitter.on(
    "auth:user-registered",
    user_registered_listener
)


def user_logged_in_listener(data):
    print(
        f"USER_LOGGED_IN event received: "
        f"{data['email']}"
    )


event_emitter.on(
    "auth:user-logged-in",
    user_logged_in_listener
)
