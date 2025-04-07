# pip install -U pip setuptools wheel
# pip install spacy
# python -m spacy download en_core_web_sm
import spacy

# Load the SpaCy language model
nlp = spacy.load("en_core_web_sm")

# Sample sentence
sentence = "He cut the bread with a knife."

# Parse the sentence
doc = nlp(sentence)

# Extract components
verb = None
object_ = None
oblique = []

list_for_debug = []
for token in doc:
    if token.dep_ == "ROOT":  # The main verb
        verb = token.text
    elif token.dep_ in {"dobj", "obj"}:  # Direct object
        object_ = token.text
    elif token.dep_ == "obl":  # Oblique (prepositional modifiers)
        oblique.append(token.text)
    list_for_debug.append(token)

from spacy import displacy
# Render and save to an HTML file
html = displacy.render(doc, style="dep", page=True)
# with open("dependency_visualization.html", "w", encoding="utf-8") as f:
#     f.write(html)
displacy.serve(doc, style="dep", port=8888)

#
# print(f"Verb: {verb}")
# print(f"Object: {object_}")
# print(f"Oblique: {' '.join(oblique)}")