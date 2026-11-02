from textrl import OnlineTrainer, TextRLConfig, load_model, reward_fn
from textrl.data import from_list


@reward_fn
def length_target(prompts, completions, **_):
    target = 64
    return [-abs(len(c) - target) / target for c in completions]


def main() -> None:
    model, tok, _ = load_model(
        "Qwen/Qwen2.5-0.5B",
        peft={"type": "lora", "r": 16, "alpha": 32, "target_modules": "all-linear"},
        load_ref=False,
    )
    cfg = TextRLConfig(
        algo="grpo",
        output_dir="out/grpo-quickstart",
        num_generations=4,
        beta=0.04,
        learning_rate=5e-6,
        per_device_train_batch_size=2,
        max_steps=20,
        bf16=True,
        logging_steps=1,
    )
    prompts = [
        "Write a haiku about rain.",
        "Explain recursion in one sentence.",
        "Describe a sunset on Mars.",
        "Summarize photosynthesis briefly.",
    ] * 16
    trainer = OnlineTrainer(
        model=model,
        tokenizer=tok,
        reward=length_target,
        train_dataset=from_list(prompts),
        config=cfg,
    )
    trainer.train()


if __name__ == "__main__":
    main()
