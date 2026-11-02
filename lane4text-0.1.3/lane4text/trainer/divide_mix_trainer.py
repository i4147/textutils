import numpy as np
import torch
from torch import nn
import torch.nn.functional as F
from torch.optim import AdamW
from torch.utils.data import DataLoader
import tqdm


class Trainer:
    def __init__(
        self, model1, model2, device=None, lr=2e-5, lambda_u=1.0, alpha=0.75, forget_rate=0.2, total_epochs=10
    ):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model1 = model1.to(self.device)
        self.model2 = model2.to(self.device)
        self.optimizer1 = AdamW(self.model1.parameters(), lr=lr)
        self.optimizer2 = AdamW(self.model2.parameters(), lr=lr)
        self.ce = nn.CrossEntropyLoss(reduction="none")
        self.lambda_u = lambda_u
        self.alpha = alpha
        self.forget_rate = forget_rate
        self.total_epochs = total_epochs

    def remember_rate(self, epoch):
        return 1.0 - self.forget_rate * min(1.0, epoch / self.total_epochs)

    def train_one_batch(self, batch, epoch):
        input_ids = batch["input_ids"].to(self.device)
        input_ids_aug = batch["input_ids_aug"].to(self.device)
        attention_mask = batch["attention_mask"].to(self.device)
        labels = batch["labels"].to(self.device)
        batch_size = input_ids.size(0)
        outputs1 = self.model1(
            input_ids=input_ids, attention_mask=attention_mask, return_dict=True, output_hidden_states=True
        )
        outputs1_aug = self.model1(
            input_ids=input_ids_aug, attention_mask=attention_mask, return_dict=True, output_hidden_states=True
        )
        outputs2 = self.model2(
            input_ids=input_ids, attention_mask=attention_mask, return_dict=True, output_hidden_states=True
        )
        outputs2_aug = self.model2(
            input_ids=input_ids_aug, attention_mask=attention_mask, return_dict=True, output_hidden_states=True
        )
        logits1 = outputs1.logits
        logits2 = outputs2.logits
        loss1_ce = self.ce(logits1, labels)
        loss2_ce = self.ce(logits2, labels)
        remember_rate = self.remember_rate(epoch)
        num_remember1 = int(remember_rate * batch_size)
        num_remember2 = int(remember_rate * batch_size)
        ind1_clean = torch.argsort(loss1_ce)[:num_remember2]
        ind2_clean = torch.argsort(loss2_ce)[:num_remember1]
        mask1_clean = torch.zeros(batch_size, dtype=torch.bool, device=self.device)
        mask1_clean[ind1_clean] = True
        mask2_clean = torch.zeros(batch_size, dtype=torch.bool, device=self.device)
        mask2_clean[ind2_clean] = True
        ind1_noisy = (~mask1_clean).nonzero(as_tuple=True)[0]
        ind2_noisy = (~mask2_clean).nonzero(as_tuple=True)[0]
        with torch.no_grad():
            cls1 = outputs1.hidden_states[-1][:, 0, :]
            cls2 = outputs2.hidden_states[-1][:, 0, :]
        with torch.no_grad():
            soft_labels1 = F.softmax(logits1[ind1_noisy], dim=-1)
            soft_labels2 = F.softmax(logits2[ind2_noisy], dim=-1)

        def mixup_labeled_unlabeled(cls_clean, labels_clean, cls_noisy, labels_noisy):
            n_clean = cls_clean.size(0)
            n_noisy = cls_noisy.size(0)
            if n_clean == 0 or n_noisy == 0:
                return cls_clean, labels_clean
            perm = torch.randperm(n_noisy)[:n_clean]
            lam = np.random.beta(self.alpha, self.alpha)
            x_mix = lam * cls_clean + (1 - lam) * cls_noisy[perm]
            y_mix = lam * labels_clean + (1 - lam) * labels_noisy[perm]
            return x_mix, y_mix

        onehot_labels1 = F.one_hot(labels[ind1_clean], num_classes=logits1.size(-1)).float()
        onehot_labels2 = F.one_hot(labels[ind2_clean], num_classes=logits2.size(-1)).float()
        cls1_mix, labels1_mix = mixup_labeled_unlabeled(
            cls1[ind1_clean], onehot_labels1, cls1[ind1_noisy], soft_labels1
        )
        cls2_mix, labels2_mix = mixup_labeled_unlabeled(
            cls2[ind2_clean], onehot_labels2, cls2[ind2_noisy], soft_labels2
        )
        pred1_mix = self.model1.classifier(cls1_mix)
        pred2_mix = self.model2.classifier(cls2_mix)
        loss1_clean = F.cross_entropy(logits1[ind1_clean], labels[ind1_clean])
        loss2_clean = F.cross_entropy(logits2[ind2_clean], labels[ind2_clean])
        loss1_mix = -(labels1_mix * F.log_softmax(pred1_mix, dim=-1)).sum(dim=-1).mean()
        loss2_mix = -(labels2_mix * F.log_softmax(pred2_mix, dim=-1)).sum(dim=-1).mean()
        logits1_aug = outputs1_aug.logits
        logits2_aug = outputs2_aug.logits
        consistency1 = F.mse_loss(F.softmax(logits1[ind1_clean], dim=-1), F.softmax(logits1_aug[ind1_clean], dim=-1))
        consistency2 = F.mse_loss(F.softmax(logits2[ind2_clean], dim=-1), F.softmax(logits2_aug[ind2_clean], dim=-1))
        loss1 = loss1_clean + loss1_mix + self.lambda_u * consistency1
        loss2 = loss2_clean + loss2_mix + self.lambda_u * consistency2
        self.optimizer1.zero_grad()
        self.optimizer2.zero_grad()
        loss1.backward()
        loss2.backward()
        self.optimizer1.step()
        self.optimizer2.step()
        return loss1.item(), loss2.item()

    def train(self, train_dataset, test_dataset=None, epochs=10, batch_size=16):
        train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
        test_loader = DataLoader(test_dataset, batch_size=batch_size) if test_dataset else None
        for epoch in range(epochs):
            self.model1.train()
            self.model2.train()
            total_loss1, total_loss2 = 0.0, 0.0
            for batch in tqdm.tqdm(train_loader, desc=f"Epoch {epoch + 1}"):
                loss1, loss2 = self.train_one_batch(batch, epoch)
                total_loss1 += loss1
                total_loss2 += loss2
            avg_loss1 = total_loss1 / len(train_loader)
            avg_loss2 = total_loss2 / len(train_loader)
            print(f"[Epoch {epoch + 1}] Loss1: {avg_loss1:.4f} | Loss2: {avg_loss2:.4f}")
            if test_loader:
                acc1, acc2 = self.evaluate(test_loader)
                print(f" Test Acc: Model1 {acc1:.2f}% | Model2 {acc2:.2f}%")

    @torch.no_grad()
    def evaluate(self, data_loader):
        self.model1.eval()
        self.model2.eval()
        correct1, correct2, total = 0, 0, 0
        for batch in tqdm.tqdm(data_loader, desc="Eval"):
            input_ids = batch["input_ids"].to(self.device)
            attention_mask = batch["attention_mask"].to(self.device)
            labels = batch["labels"].to(self.device)
            logits1 = self.model1(input_ids=input_ids, attention_mask=attention_mask, return_dict=True).logits
            logits2 = self.model2(input_ids=input_ids, attention_mask=attention_mask, return_dict=True).logits
            preds1 = logits1.argmax(dim=1)
            preds2 = logits2.argmax(dim=1)
            correct1 += (preds1 == labels).sum().item()
            correct2 += (preds2 == labels).sum().item()
            total += labels.size(0)
        acc1 = 100.0 * correct1 / max(1, total)
        acc2 = 100.0 * correct2 / max(1, total)
        return acc1, acc2
