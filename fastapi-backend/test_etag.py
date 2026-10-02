from app.cache import generate_etag


document = {
    "id": "doc123",
    "title": "Petroleum Engineering Fundamentals",
}

etag = generate_etag(document)

print("ETag:", etag)
