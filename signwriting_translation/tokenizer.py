from functools import lru_cache

import tiktoken


@lru_cache()
def load_tokenizer():
    return tiktoken.get_encoding("cl100k_base")


def tokenize_spoken_text(text: str):
    tokenizer = load_tokenizer()
    encoding = tokenizer.encode(text)

    tokens_text = [tokenizer.decode([t]) for t in encoding]
    # replace space with special token:
    tokens_text = [t.replace(" ", "Ġ") for t in tokens_text]

    return " ".join(tokens_text)


if __name__ == "__main__":
    print(tokenize_spoken_text("Hello world, my name is amit."))
