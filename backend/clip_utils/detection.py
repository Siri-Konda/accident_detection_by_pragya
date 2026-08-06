import torch
import clip
from PIL import Image

device = "mps" if torch.mps.is_available() else "cpu"
model,processor = clip.load("ViT-B/16",device=device)


logit_scale = model.logit_scale.exp()


# text = torch.load("text_features.pt")
# labels = text["labels"]

#text_features = text["crash_features"].to(device)

texts = [
    "a crash/accident",
    "a normal road or steady traffic flow, no accidents",
    "blank or static noises screen",
    "smoke or fire"
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
        text_features = model.encode_text(text_tokens)
        image_features = image_features/image_features.norm(dim=-1, keepdim = True)
        text_features = text_features/text_features.norm(dim=-1, keepdim= True)

        logits = logit_scale * (image_features @ text_features.T)

        probability = logits.softmax(dim=-1).cpu().numpy()

        return probability


if __name__ == "__main__":
    pass
