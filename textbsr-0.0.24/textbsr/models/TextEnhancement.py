import numpy as np
import cv2
import torch
import torchvision.transforms as transforms
import torch.nn as nn
import torch.nn.functional as F
from cnstd import CnStd
import warnings

warnings.filterwarnings("ignore")


class TextRestoration(object):
    def __init__(self, ModelName="RRDB", TextModelPath="../checkpoints/bsrgan_text.pth", device="cuda"):
        self.device = device
        self.ModelName = ModelName
        self.modelText = RRDBNet(scale=4)
        self.modelText.load_state_dict(torch.load(TextModelPath)["params_ema"], strict=True)
        self.modelText.eval()
        for k, v in self.modelText.named_parameters():
            v.requires_grad = False
        self.modelText = self.modelText.to(self.device)
        torch.cuda.empty_cache()
        self.std = CnStd(
            model_name="db_resnet34", rotated_bbox=False, box_score_thresh=0.3, min_box_size=10, context=device
        )
        self.insize = 32

    def handle_texts(self, img, bg=None, sf=4, is_aligned=False):
        ExistText = 0
        height, width = img.shape[:2]
        box_infos = self.std.detect(img)
        rect = img.copy()
        full_mask = np.zeros(bg.shape, dtype=np.float32)
        full_img = np.zeros(bg.shape, dtype=np.float32)
        orig_texts, enhanced_texts, text_masks, texts = [], [], [], []
        if not is_aligned:
            for i, box_info in enumerate(box_infos["detected_texts"]):
                box = box_info["box"]
                box = box_info["box"].astype(np.int)
                w, h = box[1][0] - box[0][0], box[3][1] - box[0][1]
                score = box_info["score"]
                if w < 10 or h < 10:
                    continue
                pad_wl, pad_hl = 0, 0
                pad_wl = int(w * 0.04)
                pad_hl = int(h * 0.1)
                x0 = int(max(0, box[0][1] - pad_hl))
                x1 = int(min(box[3][1] + pad_hl, height))
                y0 = int(max(box[0][0] - pad_wl, 0))
                y1 = int(min(box[1][0] + pad_wl, width))
                cropped_img = img[x0:x1, y0:y1]
                nh, nw, _ = cropped_img.shape
                cropped_img = img[x0:x1, y0:y1]
                if nh > nw:
                    up_s = self.insize / nw
                    ds = int(up_s * nh)
                    in_img = cv2.resize(cropped_img, (self.insize, ds))
                else:
                    up_s = self.insize / nh
                    ds = int(up_s * nw)
                    in_img = cv2.resize(cropped_img, (ds, self.insize))
                LQ = transforms.ToTensor()(in_img)
                LQ = transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))(LQ)
                LQ = LQ.unsqueeze(0)
                SQ = self.modelText(LQ.to(self.device))
                SQ = SQ * 0.5 + 0.5
                SQ = SQ.squeeze(0).permute(1, 2, 0).flip(2)
                SQ = np.clip(SQ.float().cpu().numpy(), 0, 1) * 255.0
                orig_texts.append(in_img[:, :, ::-1])
                enhanced_texts.append(SQ)
                SQ = cv2.resize(SQ, (nw * sf, nh * sf), cv2.INTER_AREA)
                oh, ow, _ = SQ.shape
                x0 = int(x0 * sf)
                y0 = int(y0 * sf)
                padsM = pads = int(pad_hl)
                full_img[x0 + pads : x0 + oh - pads, y0 + pads : y0 + ow - pads] = (
                    full_img[x0 + pads : x0 + oh - pads, y0 + pads : y0 + ow - pads]
                    + SQ[pads : oh - pads, pads : ow - pads, ::-1]
                )
                full_mask[x0 + padsM : x0 + oh - padsM, y0 + padsM : y0 + ow - padsM] += np.ones(
                    full_mask[x0 + padsM : x0 + oh - padsM, y0 + padsM : y0 + ow - padsM].shape, dtype=np.float32
                )
            index = full_mask > 0
            full_img[index] = full_img[index] / full_mask[index]
            full_mask = np.clip(full_mask, 0, 1)
            kernel = np.ones((7, 7), dtype=np.uint8)
            full_mask_dilate = cv2.erode(full_mask, kernel, 1)
            full_mask_blur = cv2.GaussianBlur(full_mask_dilate, (3, 3), 0)
            full_mask_blur = cv2.GaussianBlur(full_mask_blur, (3, 3), 0)
            img = cv2.convertScaleAbs(bg * (1 - full_mask_blur) + full_img * full_mask_blur)
        else:
            if height > width:
                up_s = self.insize / width
                ds = int(up_s * height)
                in_img = cv2.resize(img, (self.insize, ds))
            else:
                up_s = self.insize / height
                ds = int(up_s * width)
                in_img = cv2.resize(img, (ds, self.insize))
            LQ = transforms.ToTensor()(in_img)
            LQ = transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))(LQ)
            LQ = LQ.unsqueeze(0)
            SQ = self.modelText(LQ.to(self.device))
            SQ = SQ * 0.5 + 0.5
            SQ = SQ.squeeze(0).permute(1, 2, 0).flip(2)
            SQ = np.clip(SQ.float().cpu().numpy(), 0, 1) * 255.0
            orig_texts.append(in_img[:, :, ::-1])
            enhanced_texts.append(SQ)
        return img, orig_texts, enhanced_texts


def make_layer(basic_block, num_basic_block, **kwarg):
    layers = []
    for _ in range(num_basic_block):
        layers.append(basic_block(**kwarg))
    return nn.Sequential(*layers)


def pixel_unshuffle(x, scale):
    b, c, hh, hw = x.size()
    out_channel = c * (scale**2)
    assert hh % scale == 0 and hw % scale == 0
    h = hh // scale
    w = hw // scale
    x_view = x.view(b, c, h, scale, w, scale)
    return x_view.permute(0, 1, 3, 5, 2, 4).reshape(b, out_channel, h, w)


class ResidualDenseBlock(nn.Module):
    def __init__(self, num_feat=64, num_grow_ch=32):
        super(ResidualDenseBlock, self).__init__()
        self.conv1 = nn.Conv2d(num_feat, num_grow_ch, 3, 1, 1)
        self.conv2 = nn.Conv2d(num_feat + num_grow_ch, num_grow_ch, 3, 1, 1)
        self.conv3 = nn.Conv2d(num_feat + 2 * num_grow_ch, num_grow_ch, 3, 1, 1)
        self.conv4 = nn.Conv2d(num_feat + 3 * num_grow_ch, num_grow_ch, 3, 1, 1)
        self.conv5 = nn.Conv2d(num_feat + 4 * num_grow_ch, num_feat, 3, 1, 1)
        self.lrelu = nn.LeakyReLU(negative_slope=0.2, inplace=True)

    def forward(self, x):
        x1 = self.lrelu(self.conv1(x))
        x2 = self.lrelu(self.conv2(torch.cat((x, x1), 1)))
        x3 = self.lrelu(self.conv3(torch.cat((x, x1, x2), 1)))
        x4 = self.lrelu(self.conv4(torch.cat((x, x1, x2, x3), 1)))
        x5 = self.conv5(torch.cat((x, x1, x2, x3, x4), 1))
        return x5 * 0.2 + x


class RRDB(nn.Module):
    def __init__(self, num_feat, num_grow_ch=32):
        super(RRDB, self).__init__()
        self.rdb1 = ResidualDenseBlock(num_feat, num_grow_ch)
        self.rdb2 = ResidualDenseBlock(num_feat, num_grow_ch)
        self.rdb3 = ResidualDenseBlock(num_feat, num_grow_ch)

    def forward(self, x):
        out = self.rdb1(x)
        out = self.rdb2(out)
        out = self.rdb3(out)
        return out * 0.2 + x


class RRDBNet(nn.Module):
    def __init__(self, num_in_ch=3, num_out_ch=3, scale=4, num_feat=64, num_block=23, num_grow_ch=32):
        super(RRDBNet, self).__init__()
        self.scale = scale
        if scale == 2:
            num_in_ch = num_in_ch * 4
        elif scale == 1:
            num_in_ch = num_in_ch * 16
        self.conv_first = nn.Conv2d(num_in_ch, num_feat, 3, 1, 1)
        self.body = make_layer(RRDB, num_block, num_feat=num_feat, num_grow_ch=num_grow_ch)
        self.conv_body = nn.Conv2d(num_feat, num_feat, 3, 1, 1)
        self.conv_up1 = nn.Conv2d(num_feat, num_feat, 3, 1, 1)
        self.conv_up2 = nn.Conv2d(num_feat, num_feat, 3, 1, 1)
        self.conv_hr = nn.Conv2d(num_feat, num_feat, 3, 1, 1)
        self.conv_last = nn.Conv2d(num_feat, num_out_ch, 3, 1, 1)
        self.lrelu = nn.LeakyReLU(negative_slope=0.2, inplace=True)

    def forward(self, x):
        if self.scale == 2:
            feat = pixel_unshuffle(x, scale=2)
        elif self.scale == 1:
            feat = pixel_unshuffle(x, scale=4)
        else:
            feat = x
        feat = self.conv_first(feat)
        body_feat = self.conv_body(self.body(feat))
        feat = feat + body_feat
        feat = self.lrelu(self.conv_up1(F.interpolate(feat, scale_factor=2, mode="nearest")))
        feat = self.lrelu(self.conv_up2(F.interpolate(feat, scale_factor=2, mode="nearest")))
        out = self.conv_last(self.lrelu(self.conv_hr(feat)))
        return out


if __name__ == "__main__":
    print("Test Text Crop and Alignment")
