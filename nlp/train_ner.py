import json
import random
from pathlib import Path

import spacy
from spacy.training import Example



def load_training_data(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    training_examples = []
    for record in data:
        training_examples.append((record["text"], {"entities": record["entities"]}))
    return training_examples


def train_custom_ner(training_data_path, output_dir, iterations=30):
    nlp = spacy.blank("en")
    ner = nlp.add_pipe("ner")

    training_data = load_training_data(training_data_path)
    for _, annotations in training_data:
        for start, end, label in annotations["entities"]:
            ner.add_label(label)

    optimizer = nlp.begin_training()
    for epoch in range(iterations):
        random.shuffle(training_data)
        losses = {}
        for text, annotations in training_data:
            doc = nlp.make_doc(text)
            example = Example.from_dict(doc, annotations)
            nlp.update([example], sgd=optimizer, losses=losses)
        print(f"Epoch {epoch + 1}/{iterations} losses: {losses}")

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    nlp.to_disk(output_path)
    print(f"Custom model saved to: {output_path}")


if __name__ == "__main__":
    train_custom_ner(
        training_data_path="nlp/training_data/sample_contracts.json",
        output_dir="nlp/custom_model",
        iterations=30,
    )
