import argparse
from functools import lru_cache
from typing import List

import tokenizers
from tokenizers import Tokenizer, pre_tokenizers, normalizers, decoders, trainers
from tokenizers.models import BPE


@lru_cache(maxsize=None)
def load_tokenizer(tokenizer_file: str = 'tokenizer.json'):
    return Tokenizer.from_file(tokenizer_file)


@lru_cache(maxsize=int(1e7))
def tokenize_spoken_text(text: str, tokenizer_file: str = 'tokenizer.json'):
    tokenizer = load_tokenizer(tokenizer_file)
    encoding = tokenizer.encode(text)
    return " ".join(encoding.tokens)


def train(files: List[str], target_file: str):
    tokenizer = Tokenizer(BPE())
    tokenizer.normalizer = normalizers.NFKD()
    # Take the pre tokenizer setting from GPT-4, https://gist.github.com/xenova/a452a6474428de0182b17605a98631ee
    tokenizer.pre_tokenizer = pre_tokenizers.Sequence([
        pre_tokenizers.Split(pattern=tokenizers.Regex(
            "(?i:'s|'t|'re|'ve|'m|'ll|'d)|[^\r\n\p{L}\p{N}]?\p{L}+|\p{N}{1,3}| ?[^\s\p{L}\p{N}]+[\r\n]*|\s*[\r\n]+|\s+(?!\S)|\s+"),
            behavior="removed", invert=True),
        # For non ascii characters, it gets completely unreadable, but it works nonetheless!
        pre_tokenizers.ByteLevel(add_prefix_space=False, use_regex=False)
    ])
    tokenizer.decoder = decoders.ByteLevel()
    trainer = trainers.BpeTrainer(vocab_size=8000)
    tokenizer.train(files=files, trainer=trainer)

    tokenizer.save(target_file)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--files", nargs='+', type=str, help="Files to train tokenizer on")
    parser.add_argument("--output", type=str, help="Output file for tokenizer model")
    args = parser.parse_args()

    train(args.files, args.output)
