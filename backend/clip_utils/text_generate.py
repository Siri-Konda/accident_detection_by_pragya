import torch
import clip

device = "mps" if torch.mps.is_available() else "cpu"
model, _ = clip.load("ViT-B/16",device=device)

crash_labels ={
    "A crash, Accident",
}

no_crash_labels = {
    "Normal Traffic, Highway"
}
crash_tokens = clip.tokenize(crash_labels).to(device)
no_crash_tokens = clip.tokenize(no_crash_labels).to(device)

with torch.no_grad():
    crash_features = model.encode_text(crash_tokens)
    no_crash_features = model.encode_text(no_crash_tokens)
    crash_features = crash_features/crash_features.norm(dim=-1, keepdim =True)
    no_crash_features = no_crash_features/no_crash_features.norm(dim=-1, keepdim =True)

torch.save({
    "crash_labels" : crash_labels,
    "crash_features" : crash_features.cpu(),
    "no_crash_labels" : no_crash_labels,
    "no_crash_features" : no_crash_features.cpu()
}, "text_features.pt")

print("Saved vectors to text_features.pt")
