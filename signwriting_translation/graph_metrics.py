from collections import defaultdict

import matplotlib.pyplot as plt

MODELS_DIR = "/shares/volk.cl.uzh/amoryo/checkpoints/signwriting-translation/"
DIRECTION = "spoken-to-signed"
MODELS = [
    "no-factors",
    "target-factors",
    "target-factors-v2",
    "target-factors-v4",
    "target-factors-tuned"
]

if __name__ == "__main__":
    models_metrics = defaultdict(lambda: defaultdict(list))

    for model_name in MODELS:
        metrics_file = f"{MODELS_DIR}{DIRECTION}/{model_name}/model/metrics"
        with open(metrics_file, 'r', encoding="utf-8") as f:
            lines = f.readlines()
            for line in lines:
                for metric in line.strip().split("\t")[1:]:
                    name, value = metric.split("=")
                    try:
                        models_metrics[model_name][name].append(float(value))
                    except ValueError:
                        pass

    for metric in ['chrf', 'signwriting-similarity']:
        plt.figure(figsize=(10, 5))

        plt.grid(axis='y', linestyle='--', linewidth=0.5)
        for model_name, metrics in models_metrics.items():
            plt.plot(metrics[f"{metric}-val"], label=model_name)
        if metric == 'signwriting-similarity':
            plt.ylim(0.35, None)
        plt.legend(loc='lower right')
        plt.savefig(f"{metric}.png")
        plt.close()
