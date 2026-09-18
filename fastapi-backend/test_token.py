from app.security.tokens import verify_refresh_token
from app.security.tokens import verify_access_token
from types import SimpleNamespace

from app.security.tokens import (
    generate_access_token,
    generate_refresh_token,
)


user = SimpleNamespace(
    id="test-user-123",
    tier="free",
)


access_token = generate_access_token(user)
refresh_token = generate_refresh_token(user)


print("ACCESS TOKEN:")
print(access_token)

print("\nREFRESH TOKEN:")
print(refresh_token)


payload = verify_access_token(access_token)

print("\nACCESS PAYLOAD:")
print(payload)


payload = verify_refresh_token(refresh_token)

print("\nREFRESH PAYLOAD:")
print(payload)
