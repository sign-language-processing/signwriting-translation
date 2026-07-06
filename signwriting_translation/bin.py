#!/usr/bin/env python

import argparse
import time
from functools import cache
from itertools import chain
from pathlib import Path

from signwriting.tokenizer import SignWritingTokenizer, normalize_signwriting
from sockeye.inference import TranslatorOutput

from signwriting_translation.tokenizer import tokenize_spoken_text

sw_tokenizer = SignWritingTokenizer()


def process_translation_output(output: TranslatorOutput):
    all_factors = [output.tokens] + output.factor_tokens
    symbols = [" ".join(f).replace("M c0 r0", "M") for f in list(zip(*all_factors, strict=True))]
    return sw_tokenizer.tokens_to_text((" ".join(symbols)).split(" "))


def tokenize_signwriting(fsw: str) -> str:
    signs = normalize_signwriting(fsw).split(" ")
    return " ".join(chain.from_iterable(sw_tokenizer.text_to_tokens(sign) for sign in signs))


def process_text_output(output: TranslatorOutput) -> str:
    # target side is subword-nmt BPE; "@@" marks a split within a word
    return " ".join(output.tokens).replace("@@ ", "").strip()


@cache
def load_sockeye_translator(model_path: str, log_timing: bool = False):
    if not Path(model_path).is_dir():
        from huggingface_hub import snapshot_download
        # training-only artifacts; the optimizer state alone is ~388MB, larger than the weights
        model_path = snapshot_download(repo_id=model_path,
                                       ignore_patterns=["optimizer_best.pkl", "lr_scheduler_best.pkl"])

    from sockeye.translate import load_translator_from_args, parse_translation_arguments

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


def _run_translator(translator, texts: list[str], log_timing: bool = False):
    from sockeye.inference import make_input_from_plain_string

    inputs = [make_input_from_plain_string(sentence_id=i, string=s)
              for i, s in enumerate(texts)]

    now = time.time()
    outputs = translator.translate(inputs)
    translation_time = time.time() - now
    if log_timing:
        avg_time = translation_time / len(texts)
        print("Translated", len(texts), "texts in", translation_time, "seconds", f"({avg_time:.2f} seconds per text)")
    return outputs


def translate(translator, texts: list[str], log_timing: bool = False):
    outputs = _run_translator(translator, texts, log_timing)
    return [process_translation_output(output) for output in outputs]


def translate_to_text(translator, texts: list[str], log_timing: bool = False):
    outputs = _run_translator(translator, texts, log_timing)
    return [process_text_output(output) for output in outputs]


def get_args(default_model: str):
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', type=str, help='Path to trained model', default=default_model)
    parser.add_argument('--spoken-language', required=True, type=str, help='spoken language code')
    parser.add_argument('--signed-language', required=True, type=str, help='signed language code')
    parser.add_argument('--input', required=True, type=str, help='input text or signwriting sequence')
    return parser.parse_args()


def text_to_signwriting():
    args = get_args("sign/sockeye-text-to-factored-signwriting")

    translator, _ = load_sockeye_translator(args.model)
    tokenized_text = tokenize_spoken_text(args.input)
    model_input = f"${args.spoken_language} ${args.signed_language} {tokenized_text}"
    outputs = translate(translator, [model_input])
    print(outputs[0])


def signwriting_to_text():
    args = get_args("sign/sockeye-signwriting-to-text")

    translator, _ = load_sockeye_translator(args.model)
    model_input = f"${args.spoken_language} ${args.signed_language} {tokenize_signwriting(args.input)}"
    outputs = translate_to_text(translator, [model_input])
    print(outputs[0])


if __name__ == '__main__':
    text_to_signwriting()
