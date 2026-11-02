import torch.optim


class SolverLBFGS:
    def __init__(self, objective, image, lr=1.0):
        self.objective = objective
        self.image = image
        self.lr = lr
        self.retries = 0
        self.last_result = (float("+inf"), None)
        self.last_image = None
        self.reset_optimizer()

    def reset_optimizer(self):
        self.optimizer = torch.optim.LBFGS([self.image], lr=self.lr, max_iter=2, max_eval=4, history_size=10)
        self.iteration = 0

    def update_lr(self, factor=None):
        if factor is not None:
            self.lr *= factor
        for group in self.optimizer.param_groups:
            group["lr"] = self.lr * min(self.iteration / 40.0, 1.0) ** 2

    def call_objective(self):
        self.iteration += 1
        self.update_lr()
        self.optimizer.zero_grad()
        self.image.data.clamp_(0.0, 1.0)
        with torch.enable_grad():
            loss, scores = self.objective(self.image)
        cur_result = self.image.grad.data.abs().mean()
        if cur_result <= self.last_result[0] * 8.0:
            self.next_result = loss, scores
            if cur_result < self.last_result[0] * 2.0:
                self.last_image = self.image.data.cpu().clone()
                self.last_result = (cur_result.item(), loss)
            return loss * 1.0
        self.image.data[:] = self.last_image.to(self.image.device)
        self.image.data[:] += torch.empty_like(self.image.data).normal_(std=1e-3)
        if cur_result < self.last_result[0] * 24.0:
            self.image.grad.data.mul_(self.last_result[0] / cur_result)
            self.update_lr(factor=0.95)
            self.next_result = loss, scores
            return loss * 2.0
        self.update_lr(factor=0.8)
        raise ValueError

    def step(self):
        while True:
            try:
                self.optimizer.step(self.call_objective)
                break
            except ValueError:
                self.reset_optimizer()
                self.retries += 1
        loss, score = self.next_result
        return loss, score


class SolverSGD:
    def __init__(self, objective, image, opt_class="Adam", lr=1.0):
        self.objective = objective
        self.image = image
        self.lr = lr
        self.retries = 0
        opt_class = getattr(torch.optim, opt_class)
        self.optimizer = opt_class([image], lr=lr)
        self.iteration = 1

    def step(self):
        for group in self.optimizer.param_groups:
            group["lr"] = self.lr * min(self.iteration / 10.0, 1.0) ** 2
        self.iteration += 1
        self.optimizer.zero_grad()
        self.image.data.clamp_(0.0, 1.0)
        assert self.image.requires_grad == True
        with torch.enable_grad():
            loss, scores = self.objective(self.image)
        assert self.image.grad is not None, "Objective did not produce image gradients."
        assert not torch.isnan(self.image.grad).any(), f"Gradient is NaN, loss {loss}."
        self.optimizer.step()
        assert not torch.isnan(self.image).any(), f"Image is NaN for loss {loss}."
        return loss, scores


class MultiCriticObjective:
    def __init__(self, encoder, critics, alpha=None):
        self.encoder = encoder
        self.critics = critics
        self.alpha = alpha

    def __call__(self, image):
        layers = [c.get_layers() for c in self.critics]
        feats = dict(self.encoder.extract_all(image, layers))
        for critic in self.critics:
            critic.on_start()
        scores = []
        for critic in self.critics:
            total = 0.0
            for loss in critic.evaluate(feats):
                total += loss
            scores.append(total)
        loss = (sum(scores) / len(scores)).mean()
        loss.backward()
        for critic in self.critics:
            critic.on_finish()
        if self.alpha is not None:
            image.grad.data.mul_(self.alpha)
        return loss.item(), scores


class SequentialCriticObjective:
    def __init__(self, encoder, critics, alpha=None):
        self.encoder = encoder
        self.critics = critics
        self.alpha = alpha

    def __call__(self, image):
        scores = []
        for critic in self.critics:
            critic.on_start()
            origin_feats = dict(self.encoder.extract_all(image, critic.get_layers(), as_checkpoints=True))
            detach_feats = {k: f.detach().requires_grad_(True) for k, f in origin_feats.items()}
            total = 0.0
            for i, loss in enumerate(critic.evaluate(detach_feats)):
                assert not torch.isnan(loss), "Loss diverged to NaN."
                loss.backward()
                total += loss.item()
                del loss
            scores.append(total)
            critic.on_finish()
            tensors, grads = [], []
            for original, optimized in zip(origin_feats.values(), detach_feats.values()):
                if optimized.grad is not None:
                    tensors.append(original)
                    grads.append(optimized.grad)
            torch.autograd.backward(tensors, grads)
            del tensors
            del grads
            del origin_feats
            del detach_feats
        if self.alpha is not None:
            image.grad.data.mul_(self.alpha)
        return sum(scores) / len(scores), scores
