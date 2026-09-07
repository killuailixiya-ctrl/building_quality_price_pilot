from pathlib import Path
import torch
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image
from torchvision import transforms

ROOT = Path(r"D:\Codex\building_01")
model_path = Path(r"G:\huanghaojun_buliding\08街景主观感知\model_results_20250924_104638_质量_EfficientNet_300_200\best_model_质量.pth")
image_path = Path(r"G:\huanghaojun_buliding\社区照片\img\1000392\1000392_00.jpg")

transform = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485,0.456,0.406], std=[0.229,0.224,0.225]),
])

model = torch.load(model_path, map_location="cpu", weights_only=False)
model.eval()
image = Image.open(image_path).convert("RGB")
input_tensor = transform(image).unsqueeze(0)

features = {}
gradients = {}
def forward_hook(module, inp, out):
    features["value"] = out
def backward_hook(module, grad_in, grad_out):
    gradients["value"] = grad_out[0]

target_layer = model.features[-1]
handle_f = target_layer.register_forward_hook(forward_hook)
handle_b = target_layer.register_full_backward_hook(backward_hook)

output = model(input_tensor)
model.zero_grad()
output.backward()

activations = features["value"].detach()
grads = gradients["value"].detach()
weights = grads.mean(dim=(2,3), keepdim=True)
cam = torch.relu((weights * activations).sum(dim=1, keepdim=True))
cam = torch.nn.functional.interpolate(cam, size=image.size[::-1], mode="bilinear", align_corners=False)
cam = cam.squeeze().numpy()
cam = (cam - cam.min()) / (cam.max() - cam.min() + 1e-8)

fig, axes = plt.subplots(1, 2, figsize=(12,5))
axes[0].imshow(image); axes[0].set_title("Original"); axes[0].axis("off")
axes[1].imshow(image); axes[1].imshow(cam, cmap="jet", alpha=0.45); axes[1].set_title("Grad-CAM"); axes[1].axis("off")
plt.tight_layout()
out = ROOT / "reports/gradcam_example.png"
plt.savefig(out, dpi=200, bbox_inches="tight")
plt.close()
print("saved", out)
handle_f.remove(); handle_b.remove()
