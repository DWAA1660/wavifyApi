import nltk
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

nltk.download('punkt')
nltk.download('stopwords')

def preprocess_text(text):
    # Tokenize the text
    tokens = nltk.word_tokenize(text.lower())
    
    # Remove stopwords and non-alphabetic words
    stop_words = set(stopwords.words('english'))
    tokens = [word for word in tokens if word.isalpha() and word not in stop_words]
    
    return ' '.join(tokens)

def search(query, documents):
    # Preprocess the query and documents
    query = preprocess_text(query)
    preprocessed_documents = [preprocess_text(doc) for doc in documents]
    
    # Combine the query and documents for vectorization
    all_texts = [query] + preprocessed_documents
    
    # Use TF-IDF vectorizer
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(all_texts)
    
    # Calculate cosine similarity between the query and documents
    cosine_similarities = cosine_similarity(tfidf_matrix[0], tfidf_matrix[1:]).flatten()
    
    # Sort the documents by similarity
    results = sorted(list(enumerate(cosine_similarities, start=0)), key=lambda x: x[1], reverse=True)
    
    return results

# Example usage
query = "luney tunes"
documents = [
    "Lunes",
    "cartunes",
    "car tunes",
]

search_results = search(query, documents)
for result in search_results:
    print(documents[result[0]], result[1])