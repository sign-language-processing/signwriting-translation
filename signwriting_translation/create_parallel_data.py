import argparse
import csv
from itertools import chain
from pathlib import Path

from signwriting.formats.fsw_to_sign import fsw_to_sign
from signwriting.tokenizer import SignWritingTokenizer, normalize_signwriting
from tqdm import tqdm

from tokenizer import tokenize_spoken_text

csv.field_size_limit(int(1e6))


def load_csv(data_path: Path):
    with open(data_path, 'r', encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


DIRECTIONS = {
    "spoken-to-signed": {
        "expanded": 1,
        "more": 2,
        "cleaned": 2,
    },
    "signed-to-spoken": {
        "expanded": 1,
        "more": 3,
        "cleaned": 4,
    }
}

CLEAN_DIRECTIONS = {
    "spoken-to-signed": {
        "more": 1,
        "cleaned": 2,  # de emphasize fingerspelling
    },
    "signed-to-spoken": {
        "more": 1,
        "cleaned": 1,
    }
}

sw_tokenizer = SignWritingTokenizer()


def process_row(row, files, spoken_direction, repeats=1):
    lang_token_1, lang_token_2, *signs = row["source"].split(" ")
    # if not (lang_token_1 == "<en>" and lang_token_2 == "<ase>"):
    #     return

    signs = normalize_signwriting(" ".join(signs)).split(" ")

    tokenized_signs = [sw_tokenizer.text_to_tokens(sign) for sign in signs]
    signed_tokens = chain.from_iterable(tokenized_signs)
    signed = " ".join(signed_tokens)

    # sign language factors
    signs = [fsw_to_sign(sign) for sign in signs]
    for sign in signs:  # override box position same as the tokenizer does
        sign["box"]["position"] = (500, 500)
    units = list(chain.from_iterable([[sign["box"]] + sign["symbols"] for sign in signs]))

    spoken = tokenize_spoken_text(row["target"])

    if spoken_direction == "source":
        spoken = f"{lang_token_1} {lang_token_2} {spoken}"
    else:
        signed = f"{lang_token_1} {lang_token_2} {signed}"
        units.insert(0, {"symbol": lang_token_1, "position": [0, 0]})
        units.insert(0, {"symbol": lang_token_2, "position": [0, 0]})

    factors = [
        [s["symbol"][:4] for s in units],
        ["c" + (s["symbol"][4] if len(s["symbol"]) > 4 else '0') for s in units],
        ["r" + (s["symbol"][5] if len(s["symbol"]) > 5 else '0') for s in units],
        ["p" + str(s["position"][0]) for s in units],
        ["p" + str(s["position"][1]) for s in units],
    ]

    for _ in range(repeats):
        files["spoken"].write(spoken + "\n")
        files["signed"].write(signed + "\n")

        for i, factor_file in files["signed_factors"].items():
            factor_file.write(" ".join(factors[i]) + "\n")


def create_files(split_dir, spoken_d, signed_d):
    return {
        "spoken": open(split_dir / f"{spoken_d}.txt", "w", encoding="utf-8"),
        "signed": open(split_dir / f"{signed_d}.txt", "w", encoding="utf-8"),
        "signed_factors": {
            i: open(split_dir / f"{signed_d}_{i}.txt", "w", encoding="utf-8")
            for i in range(5)
        }
    }


# pylint: disable=too-many-locals
def create_parallel_data(data_dir: Path, output_dir: Path, clean_only=False):
    directions_obj = CLEAN_DIRECTIONS if clean_only else DIRECTIONS

    for direction, partitions in directions_obj.items():
        direction_output_dir = output_dir / direction
        direction_output_dir.mkdir(parents=True, exist_ok=True)

        train_dir = direction_output_dir / "train"
        train_dir.mkdir(parents=True, exist_ok=True)
        dev_dir = direction_output_dir / "dev"
        dev_dir.mkdir(parents=True, exist_ok=True)
        test_dir = direction_output_dir / "test"
        test_dir.mkdir(parents=True, exist_ok=True)

        spoken_d = "source" if direction == "spoken-to-signed" else "target"
        signed_d = "target" if direction == "spoken-to-signed" else "source"

        split_files = {
            "train": create_files(train_dir, spoken_d, signed_d),
            "dev": create_files(dev_dir, spoken_d, signed_d),
        }
        for partition, repeats in partitions.items():
            for split, files in split_files.items():
                split_path = data_dir / partition / f"{split}.csv"
                if not split_path.exists():
                    if split == "train":
                        raise FileNotFoundError(f"File {split_path} does not exist")
                    continue
                with open(split_path, 'r', encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in tqdm(reader):
                        process_row(row, files, spoken_d, repeats)

        test_files = create_files(test_dir, spoken_d, signed_d)
        test_path = data_dir / "test" / "all.csv"
        with open(test_path, 'r', encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in tqdm(reader):
                process_row(row, test_files, spoken_d, repeats=1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data-dir', type=str, help='Path to data directory')
    parser.add_argument('--output-dir', type=str, help='Path to output directory',
                        default="parallel")
    parser.add_argument('--clean-only', action='store_true', help='Use only cleaned data')
    args = parser.parse_args()

    data_dir = Path(args.data_dir)

    # create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    create_parallel_data(data_dir, output_dir, clean_only=args.clean_only)


if __name__ == "__main__":
    main()
