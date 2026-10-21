"""Local, inspectable NLP retrieval planner. No LLM, credentials, or remote inference."""
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

CAPABILITIES = {
 'session': 'Enter Demo password header customer Log out logout protected dashboard access refreshing session',
 'accounts': 'dashboard checking savings account name masked identifier type balance USD decimal selecting detail agree',
 'transfer': 'transfer source destination amount positive blank zero negative non-numeric over-precision insufficient atomic memo committed refresh balances history',
 'history': 'transaction history row date time description type amount status account filter inclusive boundary empty clear',
 'profile': 'profile synthetic customer display name masked email password token full identifier',
 'interface': 'desktop viewport narrower readable labels loading duplicate navigation recoverable error retry',
}

def extract(prd):
    section = ''; requirements = []
    for line in prd.splitlines():
        if line.startswith('## '): section = line[3:]
        if line.startswith('- ') and section not in ('Out of scope',):
            requirements.append({'id': f'R{len(requirements)+1:02}', 'section': section, 'text':line[2:]})
    return requirements

def plan(prd):
    reqs = extract(prd)
    names = list(CAPABILITIES)
    vectorizer = TfidfVectorizer(ngram_range=(1,2), stop_words='english', sublinear_tf=True)
    matrix = vectorizer.fit_transform(list(CAPABILITIES.values()) + [r['text'] for r in reqs])
    scores = cosine_similarity(matrix[len(names):], matrix[:len(names)])
    for r, row in zip(reqs, scores):
        index = int(row.argmax()); r['capability'] = names[index]; r['similarity'] = round(float(row[index]),4)
    return reqs
