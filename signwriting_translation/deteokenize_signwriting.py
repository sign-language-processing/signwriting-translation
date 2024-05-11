from signwriting.tokenizer import SignWritingTokenizer

tokenizer = SignWritingTokenizer()


def print_prediction(file_path: str):
    with open(file_path, 'r', encoding="utf-8") as f:
        lines = f.readlines()
        for line in lines:
            print(tokenizer.tokens_to_text(line.strip().split(" ")))


def print_factored_prediction(factors_file_template: str):
    files_rows = []
    for i in range(5):
        factors_file_path = factors_file_template.format(i)
        with open(factors_file_path, 'r', encoding="utf-8") as f:
            lines = f.readlines()
            files_rows.append([line.strip().split(" ") for line in lines])

    rows_factors = list(zip(*files_rows))
    for row in rows_factors:
        unfactored = list(zip(*row))
        symbols = [" ".join(f).replace("M c0 r0", "M") for f in unfactored]

        print(tokenizer.tokens_to_text((" ".join(symbols)).split(" ")))


print_prediction("/home/amoryo/sign-language/signwriting-translation/parallel/spoken-to-signed/test/target.txt")
print_factored_prediction(
    # pylint: disable=line-too-long
    "/shares/volk.cl.uzh/amoryo/checkpoints/signwriting-translation/spoken-to-signed/target-factors/model/decode.output.{}.00332")
