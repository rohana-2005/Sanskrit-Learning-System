import random
import json
from gen import get_verb_form, verbs, conjugations, nouns
from declensions import asmad_declension, yushmad_declension
from flask import Flask, jsonify
from flask_cors import CORS
# Load generated sentences
with open("sentences.json", "r", encoding="utf-8") as f:
    sentences = json.load(f)

app = Flask(__name__)
CORS(app)

def extract_subject(sentence):
    return sentence.split()[0]

def extract_verb(sentence):
    return sentence.split()[-1]

def replace_verb_with_blank(sentence_dict):
    sentence_text = sentence_dict["sentence"]
    verb_form = sentence_dict["verb"]["form"]
    parts = sentence_text.split()

    if verb_form in parts:
        parts[parts.index(verb_form)] = "____"
    else:
        parts[-1] = "____"

    return " ".join(parts)



def detect_person_number_from_subject(subject):
    decl_sources = {
        "1": asmad_declension,
        "2": yushmad_declension
    }

    for person, table in decl_sources.items():
        if subject in table['प्रथमा']:
            number_index = table['प्रथमा'].index(subject)
            return person, ["sg", "du", "pl"][number_index]

    if subject.endswith("ौ"):
        return "3", "du"
    elif subject.endswith("ाः") or subject.endswith("न्ति"):
        return "3", "pl"
    else:
        return "3", "sg"

# Detect person/number from conjugated verb form
def get_person_number_from_verb(form, verb_root, verb_class):
    stem = verb_root[:-1] if verb_root.endswith("्") else verb_root
    for key, suffix in conjugations[verb_class].items():
        expected = stem + suffix.replace("A", "") if "A" in suffix else verb_root + suffix
        if form == expected:
            return key.split("_")  # returns [person, number]
    return None, None

# Generate incorrect forms
def generate_distractors(correct_form, verb_root, verb_class):
    all_forms = []
    stem = verb_root[:-1] if verb_root.endswith("्") else verb_root
    for key, suffix in conjugations[verb_class].items():
        form = stem + suffix.replace("A", "") if "A" in suffix else verb_root + suffix
        if form != correct_form:
            person, number = key.split("_")
            all_forms.append((form, person, number))
    return random.sample(all_forms, 3)

# Label helper
def label(person, number):
    person_label = {"1": "First person", "2": "Second person", "3": "Third person"}
    number_label = {"sg": "singular", "du": "dual", "pl": "plural"}
    return f"{person_label.get(person)} {number_label.get(number)}"

def play_game():
    sentence = random.choice(sentences)
    correct_verb = extract_verb(sentence)
    subject = extract_subject(sentence)
    base_sentence = replace_verb_with_blank(sentence)

    # Match verb root
    matching_verb = None
    for v in verbs:
        if correct_verb.startswith(v["root"][:-1]):
            matching_verb = v
            break

    if not matching_verb:
        print("⚠ Verb root not found!")
        return

    verb_root = matching_verb["root"]
    verb_class = matching_verb["verb_class"]

    # Subject person/number
    subj_person, subj_number = detect_person_number_from_subject(subject)
    key = f"{subj_person}_{subj_number}"
    suffix = conjugations[verb_class][key]
    stem = verb_root[:-1] if verb_root.endswith("्") else verb_root
    correct_option = stem + suffix.replace("A", "") if "A" in suffix else verb_root + suffix

    # Options
    distractors = generate_distractors(correct_option, verb_root, verb_class)
    distractors.append((correct_option, subj_person, subj_number))
    random.shuffle(distractors)

    print("\n🧠 Fill in the blank:")
    print(base_sentence)
    for i, (opt, _, _) in enumerate(distractors):
        print(f"{i + 1}. {opt}")

    first_wrong = True  # Add this before the loop

    while True:
        try:
            choice = int(input("\nYour choice (1-4): "))
            selected = distractors[choice - 1]
            if selected[0] == correct_option:
                print("✅ Correct!\n")

                # Explanation as natural sentences
                print("📘 Explanation:")
                print(f"The subject '{subject}' is in {label(subj_person, subj_number).lower()} form.")
                print(f"The verb root is '{verb_root}', which belongs to class {verb_class} and means '{matching_verb.get('meaning', 'N/A')}'.")
                if matching_verb.get("requires_object"):
                    print("This verb requires an object.")
                    print(f"It can take objects of type: {', '.join(matching_verb.get('allowed_object_class', []))}.")
                else:
                    print("This verb does not require an object.")
                print(f"It can take subjects of type: {', '.join(matching_verb.get('allowed_subject_class', []))}.")
                print(f"The correct verb form is '{correct_option}' to match the subject.")
                print(f"The full sentence is: {sentence}")

                break
            else:
                wrong_person, wrong_number = selected[1], selected[2]
                if first_wrong:
                    print(f"\nℹ Hint: Subject *{subject}* is {label(subj_person, subj_number)}.")
                    first_wrong = False
                print(f"❌ Wrong. The form '{selected[0]}' is for {label(wrong_person, wrong_number)}. Try again.")
        except:
            print("❌ Invalid input. Please enter a number between 1-4.")


@app.route('/api/get-game')
def get_game():
    sentence = random.choice(sentences)
    correct_verb = sentence["verb"]["form"]
    subject_form = sentence["subject"]["form"]
    base_sentence = replace_verb_with_blank(sentence)

    verb_root = sentence["verb"]["root"]
    verb_class = sentence["verb"]["class"]
    verb_meaning = sentence["verb"].get("meaning", "N/A")
    subj_person = sentence["subject"]["person"]
    subj_number = sentence["subject"]["number"]

    key = f"{subj_person}_{subj_number}"
    suffix = conjugations[verb_class][key]
    stem = verb_root[:-1] if verb_root.endswith("्") else verb_root
    correct_option = stem + suffix.replace("A", "") if "A" in suffix else verb_root + suffix

    distractors = generate_distractors(correct_option, verb_root, verb_class)
    distractors.append((correct_option, subj_person, subj_number))
    random.shuffle(distractors)

    options = [opt for opt, _, _ in distractors]

    explanation = (
        f"The subject '{subject_form}' is in {label(subj_person, subj_number).lower()} form. "
        f"The verb root is '{verb_root}', which belongs to class {verb_class} and means '{verb_meaning}'. "
        + ("This verb requires an object. " if sentence["object"] else "This verb does not require an object. ")
        + f"The correct verb form is '{correct_option}' to match the subject. "
        f"The full sentence is: {sentence['sentence']}"
    )

    hint = f"Hint: Subject '{subject_form}' is {label(subj_person, subj_number)}."

    return jsonify({
        "sentence": base_sentence,
        "options": options,
        "correct": correct_option,
        "explanation": explanation,
        "hint": hint
    })


# Run
if __name__ == "__main__":
    app.run(debug=True)
