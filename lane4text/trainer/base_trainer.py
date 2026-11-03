import math
from loss import PManager, select_loss
import torch
from torch import nn
import torch.nn.functional as F
from torch.optim import AdamW
from torch.utils.data import DataLoader
import tqdm
from transformers import MarianMTModel, MarianTokenizer


class Trainer:
    def __init__(
        self,
        model,
        device=None,
        lr=2e-5,
    ):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model = model.to(self.device)
        self.optimizer = AdamW(self.model.parameters(), lr=lr)
        self.ce = nn.CrossEntropyLoss(reduction="none")

    def train(self, train_dataset, test_dataset=None, epochs=3, batch_size=16, grad_clip=1.0):
        train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
        test_loader = DataLoader(test_dataset, batch_size=batch_size) if test_dataset else None
        m_loss = select_loss()
        for epoch in range(epochs):
            self.model.train()
            total_loss = 0.0
            for batch in tqdm.tqdm(train_loader, desc=f"Epoch {epoch + 1}"):
                input_ids = batch["input_ids"].to(self.device)
                attention_mask = batch["attention_mask"].to(self.device)
                labels = batch["labels"].to(self.device)
                self.optimizer.zero_grad()
                outputs = self.model(
                    input_ids=input_ids,
                    attention_mask=attention_mask,
                    output_hidden_states=True,
                    return_dict=True,
                )
                logits = outputs.logits
                loss = m_loss(logits, labels, epoch)
                loss.backward()
                self.optimizer.step()
                total_loss += loss.item()
            avg_loss = total_loss / max(1, len(train_loader))
            print(f"[Epoch {epoch + 1}] Train Loss: {avg_loss:.4f}")
            if test_loader is not None:
                acc = self.evaluate(test_loader)
                print(f"               Test Acc: {acc:.2f}%")

    @torch.no_grad()
    def evaluate(self, data_loader):
        self.model.eval()
        correct, total = 0, 0
        for batch in tqdm.tqdm(data_loader, desc="Eval"):
            input_ids = batch["input_ids"].to(self.device)
            attention_mask = batch["attention_mask"].to(self.device)
            labels = batch["labels"].to(self.device)
            outputs = self.model(input_ids=input_ids, attention_mask=attention_mask, return_dict=True)
            preds = outputs.logits.argmax(dim=1)
            correct += (preds == labels).sum().item()
            total += labels.size(0)
        return 100.0 * correct / max(1, total)
