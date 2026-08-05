import torch
import clip
from PIL import Image

device = "mps" if torch.mps.is_available() else "cpu"
model,processor = clip.load("ViT-B/16",device=device)


logit_scale = model.logit_scale.exp()


text = torch.load("text_features.pt")
labels = text["labels"]

text_features = text["text_features"].to(device)

texts = [
    "a crash/about to crash",
    "a normal road or steady traffic flow, no accidents"
]

text_tokens  = clip.tokenize(texts).to(device)

def detect(img_list):
    processed_images = [processor(img) for img in img_list]
    batch_tensor = torch.stack(processed_images).to(device)
    # img1 = processor(Image.open("crash.jpeg"))
    # img2 = processor(Image.open("bike.jpg"))

    # img = torch.stack([img1,img2]).to(device)

    with torch.no_grad():
        image_features = model.encode_image(batch_tensor)
        image_features = image_features/image_features.norm(dim=-1, keepdim = True)

        logits = logit_scale * (image_features @ text_features.T)

        probability = logits.softmax(dim=-1).cpu().numpy()

        return probability


if __name__ == "__main__":
    img = Image.open("bike.jpg")
    print(detect(img))
