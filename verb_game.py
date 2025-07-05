import random
import json
from flask import Flask, jsonify
from flask_cors import CORS
from gen import conjugations, verbs  # Make sure gen.py has correct conjugations & verbs
from declensions import asmad_declension, yushmad_declension

# Load sentence data
with open("sentences.json", "r", encoding="utf-8") as f:
    sentences = json.load(f)

app = Flask(__name__)
CORS(app)

def label(person, number):
    person_label = {"1": "First person", "2": "Second person", "3": "Third person"}
    number_label = {"sg": "singular", "du": "dual", "pl": "plural"}
    return f"{person_label.get(person)} {number_label.get(number)}"

def generate_distractors(correct_form, verb_root, verb_class, verb_tense):
    all_forms = []
    verb_data = conjugations.get(verb_tense, {}).get(verb_class, {})

    # 🔍 Find the exact verb entry to get stem info
    matching_verb = next(
        (v for v in verbs if v["root"] == verb_root and v["verb_class"] == verb_class),
        {"root": verb_root}
    )

    for key, suffix in verb_data.items():
        person, number = key.split("_")

        # 🧠 Choose correct stem
        if verb_tense == "future":
            stem = matching_verb.get("future_stem", verb_root)
        elif verb_tense == "past":
            stem = matching_verb.get("past_stem", verb_root)
        else:
            stem = verb_root

        # ✂️ Drop halant (unless present 4P)
        if not (verb_tense == "present" and verb_class == "4P"):
            if stem.endswith("्"):
                stem = stem[:-1]

        form = stem + suffix.replace("A", "")

        if form != correct_form:
            all_forms.append((form, person, number))

    return random.sample(all_forms, min(3, len(all_forms)))

def replace_verb_with_blank(sentence_dict):
    sentence_text = sentence_dict["sentence"]
    verb_form = sentence_dict["verb"]["form"]
    parts = sentence_text.split()

    if verb_form in parts:
        parts[parts.index(verb_form)] = "_____"
    else:
        parts[-1] = "_____"

    return " ".join(parts)

@app.route('/api/get-game')
def get_game():
    sentence = random.choice(sentences)

    subject = sentence["subject"]
    subject_form = subject["form"]
    subj_person = subject["person"]
    subj_number = subject["number"]

    verb = sentence["verb"]
    verb_root = verb["root"]
    verb_class = verb["class"]
    verb_meaning = verb.get("meaning", "N/A")
    correct_form = verb["form"]
    verb_tense = sentence["tense"]  # ✅ Use sentence tense

    base_sentence = replace_verb_with_blank(sentence)
    key = f"{subj_person}_{subj_number}"

    # ✅ Generate distractors using same tense
    distractors = generate_distractors(correct_form, verb_root, verb_class, verb_tense)
    distractors.append((correct_form, subj_person, subj_number))
    random.shuffle(distractors)
    options = [opt for opt, _, _ in distractors]

    explanation = (
        f"The subject '{subject_form}' is in {label(subj_person, subj_number).lower()} form. "
        f"The verb root is '{verb_root}', which belongs to class {verb_class} and means '{verb_meaning}'. "
        + ("This verb requires an object. " if sentence["object"] else "This verb does not require an object. ")
        + f"The correct verb form is '{correct_form}' to match the subject. "
        f"The full sentence is: {sentence['sentence']}"
    )

    hint = f"Hint: Subject '{subject_form}' is {label(subj_person, subj_number)}."

    return jsonify({
        "sentence": base_sentence,
        "options": options,
        "correct": correct_form,
        "explanation": explanation,
        "hint": hint
    })

# Run the app
if __name__ == "__main__":
    app.run(debug=True)
