import os
from collections import defaultdict

import matplotlib.pyplot as plt

MODELS_DIR = "/shares/iict-sp2.ebling.cl.uzh/amoryo/checkpoints/signwriting-translation/"
DIRECTION = "spoken-to-signed"
MODELS = [
    "no-factors-gpt",
    "target-factors-gpt",
    "target-factors-gpt-tuned",
    "target-factors-gpt-12",
]

if __name__ == "__main__":
    models_metrics = defaultdict(lambda: defaultdict(list))

    for model_name in MODELS:
        model_path = f"{MODELS_DIR}{DIRECTION}/{model_name}"
        if not os.path.exists(f"{model_path}/model/metrics"):
            continue
        metrics_file = f"{model_path}/model/metrics"
        with open(metrics_file, 'r', encoding="utf-8") as f:
            lines = f.readlines()
            for line in lines:
                for metric in line.strip().split("\t")[1:]:
                    name, value = metric.split("=")
                    try:
                        models_metrics[model_name][name].append(float(value))
                    except ValueError:
                        pass

    print(next(iter(models_metrics.values())).keys())

    for metric in ['chrf-val', 'signwriting-similarity-val', 'signwriting-clip-val',
                   'perplexity-train', 'perplexity-val', 'decode-walltime-val', 'max-gpu-memory']:
        plt.figure(figsize=(10, 5))

        plt.grid(axis='y', linestyle='--', linewidth=0.5)
        for model_name, metrics in models_metrics.items():
            plt.plot(metrics[metric], label=model_name)
        if metric == 'signwriting-similarity-val':
            plt.ylim(0.35, None)
        plt.legend(loc='lower right')
        plt.savefig(f"{metric}.png")
        plt.close()
