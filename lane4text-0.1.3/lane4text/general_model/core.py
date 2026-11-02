import os
import re
from typing import Any, Dict, List, Optional, Union
from datasets import Dataset
import pandas as pd
from peft import LoraConfig, PeftModel, get_peft_model, prepare_model_for_kbit_training
import torch
from tqdm import tqdm
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    DataCollatorForLanguageModeling,
    Trainer,
    TrainingArguments,
)


class QwenFinetuneTool:
    def __init__(
        self,
        train_data: str | pd.DataFrame,
        test_data: str | pd.DataFrame,
        model_path: str,
        lora_save_path: str,
        result_save_path: str,
        instruction_template: str = "请根据给定信息回答问题",
        input_template: str = "输入信息：{input}",
        output_template: str = "### 输出：{output}",
        test_output_prefix: str = "### 输出：",
        lora_r: int = 16,
        lora_target_modules: list[str] = ["q_proj", "k_proj", "v_proj"],
        lora_alpha: int = 32,
        lora_dropout: float = 0.05,
        max_seq_length: int = 512,
        trust_remote_code: bool = True,
    ):
        self.train_data = train_data
        self.test_data = test_data
        self.model_path = model_path
        self.lora_save_path = lora_save_path
        self.result_save_path = result_save_path
        self.instruction_template = instruction_template
        self.input_template = input_template
        self.output_template = output_template
        self.test_output_prefix = test_output_prefix
        self.max_seq_length = max_seq_length
        self.trust_remote_code = trust_remote_code
        self.lora_config = LoraConfig(
            r=lora_r,
            target_modules=lora_target_modules,
            lora_alpha=lora_alpha,
            lora_dropout=lora_dropout,
            bias="none",
            task_type="CAUSAL_LM",
        )
        self.tokenizer = self._init_tokenizer()
        self.model = None

    def _init_tokenizer(self) -> AutoTokenizer:
        tokenizer = AutoTokenizer.from_pretrained(
            self.model_path, padding_side="left", trust_remote_code=self.trust_remote_code
        )
        tokenizer.pad_token = tokenizer.eos_token
        return tokenizer

    def _init_base_model(self) -> AutoModelForCausalLM:
        bit_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True,
        )
        model = AutoModelForCausalLM.from_pretrained(
            self.model_path, quantization_config=bit_config, device_map="auto", trust_remote_code=self.trust_remote_code
        )
        return model

    def _init_lora_model(self) -> AutoModelForCausalLM:
        model = self._init_base_model()
        model = prepare_model_for_kbit_training(model)
        model = get_peft_model(model, self.lora_config)
        print(f"LoRA模型初始化完成，可训练参数：")
        model.print_trainable_parameters()
        return model

    def _get_template_placeholders(self, template: str) -> list[str]:
        return re.findall(r"\{(\w+)\}", template)

    def _format_train_example(self, example: dict[str, str]) -> str:
        input_placeholders = self._get_template_placeholders(self.input_template)
        output_placeholders = self._get_template_placeholders(self.output_template)
        all_placeholders = list(set(input_placeholders + output_placeholders))
        template_kwargs = {key: example.get(key, "").strip() for key in all_placeholders}
        instruction = self.instruction_template
        input_text = self.input_template.format(**template_kwargs)
        output_text = self.output_template.format(**template_kwargs)
        return f"### 指令：{instruction}\n ### 输入：{input_text}\n {output_text}"

    def _format_train_batch(self, examples: dict[str, Any]) -> dict[str, torch.Tensor]:
        results = []
        for i in range(len(examples[next(iter(examples.keys()))])):
            single_example = {k: examples[k][i] for k in examples}
            results.append(self._format_train_example(single_example))
        tokenized = self.tokenizer(
            results, return_tensors="pt", padding="max_length", max_length=self.max_seq_length, truncation=True
        )
        tokenized["labels"] = tokenized["input_ids"].clone()
        return tokenized

    def train(self, train_args_dict: Optional[dict[str, Any]] = None) -> None:
        data = self._load_data(self.train_data, data_type="训练")
        ds = Dataset.from_pandas(data)
        print(f"训练数据加载完成，共{len(ds)}条样本")
        train_tokenized = ds.map(self._format_train_batch, batched=True, remove_columns=ds.column_names)
        self.model = self._init_lora_model()
        default_train_args = {
            "output_dir": os.path.dirname(self.lora_save_path),
            "eval_strategy": "no",
            "per_device_train_batch_size": 8,
            "gradient_accumulation_steps": 4,
            "learning_rate": 2e-4,
            "num_train_epochs": 3,
            "lr_scheduler_type": "cosine",
            "warmup_ratio": 0.05,
            "logging_steps": 10,
            "save_steps": 100,
            "bf16": True,
            "optim": "paged_adamw_8bit",
            "report_to": "none",
            "gradient_checkpointing": True,
        }
        if train_args_dict:
            default_train_args.update(train_args_dict)
        train_args = TrainingArguments(**default_train_args)
        data_collator = DataCollatorForLanguageModeling(tokenizer=self.tokenizer, mlm=False)
        trainer = Trainer(model=self.model, args=train_args, data_collator=data_collator, train_dataset=train_tokenized)
        print("开始训练...")
        trainer.train()
        os.makedirs(os.path.dirname(self.lora_save_path), exist_ok=True)
        self.model.save_pretrained(self.lora_save_path)
        print(f"LoRA模型已保存至：{self.lora_save_path}")

    def _format_test_example(self, example: dict[str, str]) -> str:
        input_placeholders = self._get_template_placeholders(self.input_template)
        template_kwargs = {key: example.get(key, "").strip() for key in input_placeholders}
        instruction = self.instruction_template
        input_text = self.input_template.format(**template_kwargs)
        return f"### 指令：{instruction}\n ### 输入：{input_text}\n {self.test_output_prefix}"

    def inference(self, batch_size: int = 8, max_new_tokens: int = 100) -> pd.DataFrame:
        if self.model is None:
            base_model = self._init_base_model()
            self.model = PeftModel.from_pretrained(base_model, self.lora_save_path)
            self.model.eval()
            print(f"已加载LoRA模型：{self.lora_save_path}")
        data_test = self._load_data(self.test_data, data_type="测试")
        print(f"测试数据加载完成，共{len(data_test)}条样本")
        results = []
        total_batch = (len(data_test) + batch_size - 1) // batch_size
        with torch.no_grad():
            for idx in tqdm(range(total_batch), desc="推理进度"):
                start = batch_size * idx
                end = min(batch_size * (idx + 1), len(data_test))
                sample_data = data_test.iloc[start:end]
                prompts = []
                for _, row in sample_data.iterrows():
                    single_example = row.to_dict()
                    prompts.append(self._format_test_example(single_example))
                tokenized = self.tokenizer(
                    prompts, return_tensors="pt", truncation=True, padding="max_length", max_length=self.max_seq_length
                )
                tokenized = {k: v.to(self.model.device) for k, v in tokenized.items()}
                output = self.model.generate(
                    **tokenized,
                    max_new_tokens=max_new_tokens,
                    top_k=50,
                    top_p=0.9,
                    pad_token_id=self.tokenizer.pad_token_id,
                    eos_token_id=self.tokenizer.eos_token_id,
                )
                decode_pred = self.tokenizer.batch_decode(output.cpu(), skip_special_tokens=True)
                for text in decode_pred:
                    if self.test_output_prefix in text:
                        res = text.split(self.test_output_prefix)[1].strip()
                    else:
                        res = text.strip()
                    results.append(res)
        data_test["result"] = results
        os.makedirs(os.path.dirname(self.result_save_path), exist_ok=True)
        data_test.to_csv(self.result_save_path, index=False, encoding="utf-8")
        print(f"推理结果已保存至：{self.result_save_path}")
        return data_test

    def _load_data(self, data: str | pd.DataFrame, data_type: str = "训练") -> pd.DataFrame:
        if isinstance(data, pd.DataFrame):
            if data.empty:
                msg = f"{data_type}数据为空，请检查输入的DataFrame"
                raise ValueError(msg)
            return data.copy()
        elif isinstance(data, str):
            if not os.path.exists(data):
                msg = f"{data_type}数据文件不存在：{data}"
                raise FileNotFoundError(msg)
            if data.endswith(".json"):
                return pd.read_json(data)
            elif data.endswith(".csv"):
                return pd.read_csv(data)
            else:
                msg = f"不支持的{data_type}数据格式：{data}（仅支持json/csv）"
                raise ValueError(msg)
        else:
            msg = f"{data_type}数据类型错误（需为str路径或pd.DataFrame，实际为{type(data)}）"
            raise TypeError(msg)
