#!/usr/bin/env python

import argparse
import time
from functools import lru_cache
from pathlib import Path
from typing import List

from signwriting.tokenizer import SignWritingTokenizer
from sockeye.inference import TranslatorOutput

from signwriting_translation.tokenizer import tokenize_spoken_text

sw_tokenizer = SignWritingTokenizer()


def process_translation_output(output: TranslatorOutput):
    all_factors = [output.tokens] + output.factor_tokens
    symbols = [" ".join(f).replace("M c0 r0", "M") for f in list(zip(*all_factors))]
    return sw_tokenizer.tokens_to_text((" ".join(symbols)).split(" "))


@lru_cache(maxsize=None)
def load_sockeye_translator(model_path: str, log_timing: bool = False):
    if not Path(model_path).is_dir():
        from huggingface_hub import snapshot_download
        model_path = snapshot_download(repo_id=model_path)

    from sockeye.translate import parse_translation_arguments, load_translator_from_args

    now = time.time()
    args = parse_translation_arguments([
        "-m", model_path,
        "--beam-size", "5",
    ])
    translator = load_translator_from_args(args, True)
    if log_timing:
        print("Loaded sockeye translator in", time.time() - now, "seconds")

    tokenizer_path = str(Path(model_path) / 'tokenizer.json')

    return translator, tokenizer_path


def translate(translator, texts: List[str], log_timing: bool = False):
    from sockeye.inference import make_input_from_plain_string

    inputs = [make_input_from_plain_string(sentence_id=i, string=s)
              for i, s in enumerate(texts)]

    now = time.time()
    outputs = translator.translate(inputs)
    translation_time = time.time() - now
    avg_time = translation_time / len(texts)
    if log_timing:
        print("Translated", len(texts), "texts in", translation_time, "seconds", f"({avg_time:.2f} seconds per text)")
    return [process_translation_output(output) for output in outputs]


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', type=str, help='Path to trained model',
                        default="sign/sockeye-text-to-factored-signwriting")
    parser.add_argument('--spoken-language', required=True, type=str, help='spoken language code')
    parser.add_argument('--signed-language', required=True, type=str, help='signed language code')
    parser.add_argument('--input', required=True, type=str, help='input text or signwriting sequence')
    return parser.parse_args()


def signwriting_to_text():
    # pylint: disable=unused-variable
    args = get_args()

    translator, tokenizer_path = load_sockeye_translator(args.model)
    # tokenized_text = " ".join(tokenizer.encode(args.input).tokens)
    tokenized_text = tokenize_spoken_text(args.input)  # , tokenizer_path)
    model_input = f"${args.spoken_language} ${args.signed_language} {tokenized_text}"
    outputs = translate(translator, [model_input])
    print(outputs[0])


def text_to_signwriting():
    # pylint: disable=unused-variable
    args = get_args()

    return translate(args.model, [args.input])


if __name__ == '__main__':
    signwriting_to_text()
