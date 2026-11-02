from copy import deepcopy
import math
import pandas as pd
import torch
from torch import nn
import torch.nn.functional as F
from torch.optim import AdamW
from torch.optim.lr_scheduler import CosineAnnealingLR
from torch.utils.data import DataLoader
import tqdm
from lane4text.loss import PManager, select_loss


class Trainer:
    def __init__(
        self,
        model,
        save_model_path="best_model.pth",
        save_train_csv_path="train_result.csv",
        save_test_csv_path="test_result.csv",
        max_acc=0.0,
        device=None,
        lr=2e-5,
        ema_decay=0.999,
        epochs=3,
    ):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.student = model.to(self.device)
        self.save_model_path = save_model_path
        self.max_acc = max_acc
        self.save_train_csv_path = save_train_csv_path
        self.save_test_csv_path = save_test_csv_path
        self.teacher = deepcopy(model).to(self.device)
        self.teacher.eval()
        for p in self.teacher.parameters():
            p.requires_grad = False
        self.optimizer = AdamW(self.student.parameters(), lr=lr)
        self.scheduler = CosineAnnealingLR(self.optimizer, T_max=epochs)
        self.ce = nn.CrossEntropyLoss(reduction="none")
        self.ema_decay = ema_decay

    def update_teacher(self):
        with torch.no_grad():
            for s_param, t_param in zip(self.student.parameters(), self.teacher.parameters()):
                t_param.data.mul_(self.ema_decay).add_(s_param.data * (1 - self.ema_decay))

    def train(self, train_dataset, test_dataset=None, epochs=3, batch_size=16, alpha=0.7, loss_type="catoni", T=2.0):
        train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
        test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False) if test_dataset else None
        m_loss = select_loss(loss_type)
        for epoch in range(epochs):
            self.student.train()
            total_loss = 0.0
            total_ce_loss = 0.0
            total_kd_loss = 0.0
            for batch in tqdm.tqdm(train_loader, desc=f"Epoch {epoch + 1}"):
                input_ids = batch["input_ids"].to(self.device)
                attention_mask = batch["attention_mask"].to(self.device)
                labels = batch["labels"].to(self.device)
                self.optimizer.zero_grad()
                student_outputs = self.student(
                    input_ids=input_ids, attention_mask=attention_mask, output_hidden_states=True, return_dict=True
                )
                student_logits = student_outputs.logits
                with torch.no_grad():
                    teacher_outputs = self.teacher(
                        input_ids=input_ids, attention_mask=attention_mask, output_hidden_states=True, return_dict=True
                    )
                    teacher_logits = teacher_outputs.logits
                ce_loss = m_loss(student_logits, labels).mean()
                kd_loss = F.kl_div(
                    F.log_softmax(student_logits / T, dim=1),
                    F.softmax(teacher_logits / T, dim=1),
                    reduction="batchmean",
                ) * (T * T)
                loss = ce_loss + kd_loss * alpha
                loss.backward()
                torch.nn.utils.clip_grad_norm_(self.student.parameters(), max_norm=1.0)
                self.optimizer.step()
                self.update_teacher()
                total_loss += loss.item()
                total_ce_loss += ce_loss.item()
                total_kd_loss += kd_loss.item()
            self.scheduler.step()
            avg_loss = total_loss / max(1, len(train_loader))
            avg_ce_loss = total_ce_loss / max(1, len(train_loader))
            avg_kd_loss = total_kd_loss / max(1, len(train_loader))
            print(
                f"[Epoch {epoch + 1}] "
                f"Train Loss: {avg_loss:.4f} | "
                f"CE Loss: {avg_ce_loss:.4f} | "
                f"KD Loss: {avg_kd_loss:.4f} | "
                f"LR: {self.scheduler.get_last_lr()[0]:.6f}"
            )
            if test_loader is not None:
                acc = self.evaluate(test_loader)
                print(f"               Test Acc: {acc:.2f}%")
                if acc > self.max_acc:
                    self.max_acc = acc
                    torch.save(self.student.state_dict(), self.save_model_path)
                    print(f"Saved model with acc: {acc:.2f}%")

    @torch.no_grad()
    def evaluate(self, data_loader):
        self.student.eval()
        correct, total = 0, 0
        for batch in tqdm.tqdm(data_loader, desc="Eval"):
            input_ids = batch["input_ids"].to(self.device)
            attention_mask = batch["attention_mask"].to(self.device)
            labels = batch["labels"].to(self.device)
            outputs = self.student(input_ids=input_ids, attention_mask=attention_mask, return_dict=True)
            preds = outputs.logits.argmax(dim=1)
            correct += (preds == labels).sum().item()
            total += labels.size(0)
        return 100.0 * correct / max(1, total)
