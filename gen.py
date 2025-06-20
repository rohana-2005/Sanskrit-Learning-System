import json
from declensions import (
    a_stem_masc_declension,
    ā_stem_fem_declension,
    a_stem_neut_declension,
    asmad_declension,
    yushmad_declension
)

# Load nouns
with open("nouns.json", "r", encoding="utf-8") as f:
    noun_groups = json.load(f)

nouns = []
for key, roots in noun_groups.items():
    parts = key.split("_")
    gender = None if parts[0] == "none" else parts[0]
    stem = None if parts[1] == "none" else parts[1]
    for root, info in roots.items():
        nouns.append({
            "root": root,
            "gender": gender,
            "stem_type": stem,
            "entity_classes": info["entity_classes"],
            "usable_as_subject": info["usable_as_subject"],
            "usable_as_object": info["usable_as_object"]
        })

# Load conjugations
with open("conjugations.json", "r", encoding="utf-8") as f:
    conjugations = json.load(f)

# Load verbs and flatten
with open("verbs.json", "r", encoding="utf-8") as f:
    raw_verbs = json.load(f)

verbs = []
for verb_class, content in raw_verbs.items():
    for verb_entry in content["verbs"]:
        verb_entry["verb_class"] = verb_class
        verbs.append(verb_entry)

# Declensions
declension_map = {
    ("masc", "अ"): a_stem_masc_declension,
    ("fem", "आ"): ā_stem_fem_declension,
    ("neut", "अ"): a_stem_neut_declension
}

role_to_vibhakti = {
    "subject": "प्रथमा",
    "object": "द्वितीया"
}

number_index = {
    "sg": 0,
    "du": 1,
    "pl": 2
}

def inflect_noun(noun, role):
    root = noun["root"]
    number = noun.get("number", "sg")
    index = number_index[number]
    vibhakti = role_to_vibhakti[role]

    if root == "अस्मद्":
        return asmad_declension[vibhakti][index]
    elif root == "युष्मद्":
        return yushmad_declension[vibhakti][index]

    gender = noun.get("gender")
    stem = noun.get("stem_type")
    decl_table = declension_map.get((gender, stem))
    if not decl_table or vibhakti not in decl_table:
        return root

    suffix = decl_table[vibhakti][index]

    if gender == "fem" and stem == "आ":
        return (root[:-1] if root.endswith("ा") else root) + suffix
    else:
        return root + suffix

def get_verb_form(verb, person, number):
    key = f"{person}_{number}"
    verb_class = verb["verb_class"]
    suffix = conjugations[verb_class][key]

    if "A" in suffix:
        stem = verb["root"][:-1] if verb["root"].endswith("्") else verb["root"]
        return stem + suffix.replace("A", "")
    else:
        return verb["root"] + suffix

def get_valid_nouns(entity_class, role):
    key = "usable_as_subject" if role == "subject" else "usable_as_object"
    return [
        n.copy() for n in nouns
        if entity_class in n["entity_classes"] and n.get(key, False)
    ]

def generate_sentence_for_verb(verb):
    sentence_data = []
    subject_classes = verb["allowed_subject_class"]
    object_required = verb["requires_object"]
    object_classes = verb.get("allowed_object_class", [])

    for subj_class in subject_classes:
        for subject in get_valid_nouns(subj_class, role="subject"):
            for number in ["sg", "du", "pl"]:
                subject["number"] = number
                person = {"अस्मद्": "1", "युष्मद्": "2"}.get(subject["root"], "3")
                subject_form = inflect_noun(subject, "subject")

                verb_form = get_verb_form(verb, person, number)

                if object_required:
                    for obj_class in object_classes:
                        for obj in get_valid_nouns(obj_class, role="object"):
                            for obj_number in ["sg", "du", "pl"]:
                                obj["number"] = obj_number
                                object_form = inflect_noun(obj, "object")
                                sentence = f"{subject_form} {object_form} {verb_form}"
                                sentence_data.append({
                                    "sentence": sentence,
                                    "subject": {
                                        "root": subject["root"],
                                        "form": subject_form,
                                        "number": number,
                                        "person": person,
                                        "gender": subject["gender"],
                                        "stem": subject["stem_type"]
                                    },
                                    "object": {
                                        "root": obj["root"],
                                        "form": object_form,
                                        "number": obj_number,
                                        "person": "3",
                                        "gender": obj["gender"],
                                        "stem": obj["stem_type"]
                                    },
                                    "verb": {
                                        "root": verb["root"],
                                        "form": verb_form,
                                        "person": person,
                                        "number": number,
                                        "class": verb["verb_class"],
                                        "meaning": verb.get("meaning", "")
                                    }
                                })
                else:
                    sentence = f"{subject_form} {verb_form}"
                    sentence_data.append({
                        "sentence": sentence,
                        "subject": {
                            "root": subject["root"],
                            "form": subject_form,
                            "number": number,
                            "person": person,
                            "gender": subject["gender"],
                            "stem": subject["stem_type"]
                        },
                        "object": None,
                        "verb": {
                            "root": verb["root"],
                            "form": verb_form,
                            "person": person,
                            "number": number,
                            "class": verb["verb_class"],
                            "meaning": verb.get("meaning", "")
                        }
                    })
    return sentence_data

if __name__ == "__main__":
    all_sentences = []
    for verb in verbs:
        all_sentences.extend(generate_sentence_for_verb(verb))

    with open("sentences.json", "w", encoding="utf-8") as f:
        json.dump(all_sentences, f, ensure_ascii=False, indent=2)

    print(f"{len(all_sentences)} sentences generated and saved to 'sentences.json'.")
