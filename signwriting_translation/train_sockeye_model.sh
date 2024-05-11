#!/bin/bash

#SBATCH --job-name=train-sockeye
#SBATCH --time=48:00:00
#SBATCH --mem=16G
#SBATCH --output=train-%j.out

#SBATCH --ntasks=1
#SBATCH --gres gpu:1
#SBATCH --constraint=GPUMEM80GB

set -e # exit on error
set -x # echo commands

module load anaconda3
source activate sockeye


# Parse command line arguments
for arg in "$@"; do
  # if stripped arg is empty or (space, new line), skip
  [ -z "${arg// }" ] && continue

  # Split the argument into name and value parts
  key="${arg%%=*}"    # Extract everything before '='
  value="${arg#*=}"   # Extract everything after '='

  # Remove leading '--' from the key name
  key="${key##--}"

  # Declare variable dynamically and assign value
  declare "$key"="$value"
done


mkdir -p $model_dir

# e.g., "signwriting-similarity", "chrf" (default)
optimized_metric=${optimized_metric:-"chrf"}

# Flags for source and target factors
use_source_factors=${use_source_factors:-"false"}
use_target_factors=${use_target_factors:-"false"}

# Clone sockeye if doesn't exist
#[ ! -d sockeye ] && git clone https://github.com/sign-language-processing/sockeye.git
#pip install ./sockeye
#
## Install SignWriting evaluation package for optimized metric
#pip install git+https://github.com/sign-language-processing/signwriting
#pip install git+https://github.com/sign-language-processing/signwriting-evaluation
#pip install tensorboard

function find_source_files() {
    local directory=$1
    find "$directory" -type f -name 'source_[1-9]*.txt' -printf "$directory/%f\n" | sort | tr '\n' ' '
}

function find_target_files() {
    local directory=$1
    find "$directory" -type f -name 'target_[1-9]*.txt' -printf "$directory/%f\n" | sort | tr '\n' ' '
}


function translation_files() {
    local name=$1
    local type=$2    # e.g., "source" or "target"
    local split=$3   # e.g., "train", "dev", or "test"
    local use_factors=$4  # Pass 'true' or 'false' to use factors

    # Determine the file finder function based on the type
    local find_function="find_${type}_files"

    if [[ "$use_factors" == "true" ]]; then
        echo "--${name} ${split}/${type}_0.txt --${name}-factors $($find_function "$split")"
    else
        echo "--${name} ${split}/${type}.txt"
    fi
}

function find_vocabulary_factors_files() {
    local directory=$1
    local type_short=$2
    find "$directory" -type f -name "vocab.${type_short}.[1-9]*.json" -printf "$directory/%f\n" | sort | tr '\n' ' '
}

function vocabulary_files() {
    local base_model_dir=$1
    local type=$2    # e.g., "src" or "trg"
    local type_short=$3    # e.g., "src" or "trg"
    local use_factors=$4  # Pass 'true' or 'false' to use factors

    if [ -z "$base_model_dir" ]; then
        return
    fi

    echo "--${type}-vocab $base_model_dir/model/vocab.${type_short}.0.json "

    if [[ "$use_factors" == "true" ]]; then
        echo "--${type}-factor-vocabs $(find_vocabulary_factors_files $base_model_dir/model $type_short)"
    fi
}

# max seq len based on factor usage
max_seq_len=2048
[ "$use_source_factors" == "true" ] && max_seq_len=512
[ "$use_target_factors" == "true" ] && max_seq_len=512

# Prepare data
TRAIN_DATA_DIR="$model_dir/train_data"
[ ! -f "$TRAIN_DATA_DIR/data.version" ] && \
python -m sockeye.prepare_data \
  --max-seq-len $max_seq_len:$max_seq_len \
  $(vocabulary_files "$base_model_dir" "source" "src" $use_source_factors) \
  $(translation_files "source" "source" "$data_dir/train" $use_source_factors) \
  $(vocabulary_files "$base_model_dir" "target" "trg" $use_target_factors) \
  $(translation_files "target" "target" "$data_dir/train" $use_target_factors) \
  --output $TRAIN_DATA_DIR \

cp tokenizer.json $model_dir/tokenizer.json

MODEL_DIR="$model_dir/model"
rm -rf $MODEL_DIR

# batch size refers to number of target tokens, has to be larger than max tokens set in prepare_data
batch_size=$((max_seq_len * 2 + 1))
extra_arguments=""
# params is set --params $base_model_dir/model/params.best if $base_model_dir is set
if [ -n "$base_model_dir" ]; then
  extra_arguments="${extra_arguments} --params $base_model_dir/model/params.best"
fi

# From https://aclanthology.org/2023.findings-eacl.127.pdf
# target-factors-weight 0.2
# weight-tying-type "trg_softmax"
# learning-rate-reduce-factor 0.7
# label-smoothing 0.2
# embed-dropout 0.5
# transformer-dropout is double than the default, but less than 0.5 from the paper
python -m sockeye.train \
  -d $TRAIN_DATA_DIR \
  --weight-tying-type "trg_softmax" \
  --max-seq-len $max_seq_len:$max_seq_len \
  --batch-size $batch_size \
  --source-factors-combine sum \
  --target-factors-combine sum \
  --target-factors-weight 0.2 \
  $(translation_files "validation-source" "source" "$data_dir/test" $use_source_factors) \
  $(translation_files "validation-target" "target" "$data_dir/test" $use_target_factors) \
  --optimized-metric "$optimized_metric" \
  --learning-rate-warmup 1000 \
  --learning-rate-reduce-factor 0.7 \
  --decode-and-evaluate 1000 \
  --checkpoint-interval 1000 \
  --max-num-checkpoint-not-improved 50 \
  --embed-dropout 0.5 \
  --transformer-dropout-prepost 0.2 \
  --transformer-dropout-act 0.2 \
  --transformer-dropout-attention 0.2 \
  --label-smoothing 0.2 \
  --label-smoothing-impl torch \
  --no-bucketing \
  $extra_arguments \
  --output $MODEL_DIR
