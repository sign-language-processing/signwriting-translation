# SignWriting Translation

This project trains and serves models to translate SignWriting into spoken language text and vice versa.

## Usage

```bash
pip install git+https://github.com/sign-language-processing/signwriting-translation
```

To translate:

```bash
signwriting_to_text --spoken-language="en" --signed-language="ase" --input="M525x535S2e748483x510S10011501x466S2e704510x500S10019476x475"
text_to_signwriting --spoken-language="en" --signed-language="ase" --input="Sign Language"
```

### Examples

(These examples are taken from the DSGS Vokabeltrainer)

|             |                                                                    00004                                                                     |                                                                    00007                                                                     |                                                                    00015                                                                     |
|:-----------:|:--------------------------------------------------------------------------------------------------------------------------------------------:|:--------------------------------------------------------------------------------------------------------------------------------------------:|:--------------------------------------------------------------------------------------------------------------------------------------------:|
| SignWriting | <img src="https://github.com/sign-language-processing/signwriting-transcription/blob/main/assets/examples/00004.png?raw=true" width="50px">  | <img src="https://github.com/sign-language-processing/signwriting-transcription/blob/main/assets/examples/00007.png?raw=true" width="50px">  | <img src="https://github.com/sign-language-processing/signwriting-transcription/blob/main/assets/examples/00015.png?raw=true" width="50px">  |
|    Video    | <img src="https://github.com/sign-language-processing/signwriting-transcription/blob/main/assets/examples/00004.gif?raw=true" width="150px"> | <img src="https://github.com/sign-language-processing/signwriting-transcription/blob/main/assets/examples/00007.gif?raw=true" width="150px"> | <img src="https://github.com/sign-language-processing/signwriting-transcription/blob/main/assets/examples/00015.gif?raw=true" width="150px"> |

## Data

We use the SignBank+ Dataset from [signbank-plus](https://github.com/sign-language-processing/signbank-plus).

