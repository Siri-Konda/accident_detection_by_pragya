import torch
import clip
from PIL import Image

device = "mps" if torch.mps.is_available() else "cpu"
model,processor = clip.load("ViT-B/16",device=device)

model = model.to(torch.float16)

model_visual = model.visual
logit_scale = model.logit_scale.exp()
del model
model = model_visual

text = torch.load("text_features.pt")
crash_labels = text["crash_labels"]
crash_features = text["crash_features"].to(device).to(torch.float16)
no_crash_labels = text["no_crash_labels"]
no_crash_features = text["no_crash_features"].to(device).to(torch.float16)

def detect(img_list):
    processed_images = [processor(img) for img in img_list]
    batch_tensor = torch.stack(processed_images).to(torch.float16).to(device)

    with torch.no_grad():
        image_features = model(batch_tensor)
        image_features = image_features/image_features.norm(dim=-1, keepdim = True)

        crash_logits = logit_scale * (image_features @ crash_features.T)
        no_crash_logits = logit_scale * (image_features @ no_crash_features.T)
        logits = torch.cat([crash_logits,no_crash_logits], dim=-1).squeeze(0)
        probability = logits.softmax(dim=-1).cpu().numpy()

        return probability


if __name__ == "__main__":
    img = Image.open("crash.jpeg")
    print(detect(img))