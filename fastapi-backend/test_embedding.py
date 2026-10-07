from app.services.embedding import generate_embedding


text = "DocuChat is an AI-powered document question answering system."

embedding = generate_embedding(text)

print()
print("=== SINGLE EMBEDDING TEST ===")
print("Embedding generated successfully!")
print("Dimensions:", len(embedding))
print("First 5 values:", embedding[:5])
print()
