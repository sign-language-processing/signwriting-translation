#!/bin/bash

#SBATCH --job-name=prepare-data
#SBATCH --time=24:00:00
#SBATCH --mem=32G
#SBATCH --output=prepare_data.out

#SBATCH --ntasks=1

set -e # exit on error
set -x # echo commands

module load anaconda3
source activate sockeye


# Download the SignBank repository if not exists
SIGNBANK_DIR="/home/amoryo/sign-language/signbank-annotation/signbank-plus"
[ ! -d "$SIGNBANK_DIR" ] && \
git clone https://github.com/sign-language-processing/signbank-plus.git "$SIGNBANK_DIR"

# Process data for machine translation if not exists
[ ! -d "$SIGNBANK_DIR/data/parallel/cleaned" ] && \
python "$SIGNBANK_DIR/signbank_plus/prep_nmt.py"

## Train a tokenizer
#python spoken_language_tokenizer.py \
#  --files $SIGNBANK_DIR/data/parallel/cleaned/train.target $SIGNBANK_DIR/data/parallel/more/train.target  \
#  --output="tokenizer.json"

# Prepare the parallel corpus (with source/target-factors)
python create_parallel_data.py \
  --data-dir="$SIGNBANK_DIR/data/parallel/" \
  --output-dir="../parallel"

# Prepare the clean parallel corpus (with source/target-factors)
python create_parallel_data.py \
  --data-dir="$SIGNBANK_DIR/data/parallel/" \
  --output-dir="../parallel-clean" \
  --clean-only

