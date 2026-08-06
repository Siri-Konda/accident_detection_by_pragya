import torch
import clip
import numpy as np
from PIL import Image


device = "cuda" if torch.cuda.is_available() else "cpu"
model, preprocess = clip.load("ViT-B/16", device=device)


# ACCIDENT_PROMPTS = [
#     # "vehicle accident collision",
#     # "a fallen bike on road",
#     # "a photo of two vehicles colliding",
#     # "a fallen man on road"
#     "CCTV footage of a motorcycle crash or accident",
#     "a crashed motorcycle lying sideways on the road",
#     "a person lying fallen on the road next to a bike",
#     "a collision with two vehicles crashing into each other"
# ]

# NORMAL_PROMPTS = [
#     # "Normal Traffic flow",
#     # "normal road, traffic",
#     # "no accidents"
#     "CCTV footage of normal traffic flowing smoothly",
#     "a person riding a motorcycle upright along the road",
#     "a motorcycle traveling normally on an asphalt street",
#     "an urban road with normal vehicle traffic",
    
#     # Daytime Specific
#     "a daytime CCTV view of motorcycles driving safely on the street",
    
#     # Nighttime Specific
#     "a nighttime CCTV view of motorcycles driving with headlights"

# ]

ACCIDENT_PROMPTS = [
    "a cctv footage of a crash or accident in some part of footage",
    "a fallen bike in some part of the footage"
]

NORMAL_PROMPTS = [
    "a cctv footage of road with vehicles moving without accidents"
]

BLANK_PROMPTS = [
    "camera video loss with static noise or blank screen"
]

FIRE_PROMPTS = [
    "a severe fire and thick smoke on the road"
]


ALL_PROMPTS = ACCIDENT_PROMPTS + NORMAL_PROMPTS + BLANK_PROMPTS + FIRE_PROMPTS


text_tokens = clip.tokenize(ALL_PROMPTS).to(device)

def detect(images):
    """
    Takes a list of PIL images and returns probabilities for [accident, normal, blank, fire]
    """
    
    image_input = torch.stack([preprocess(img) for img in images]).to(device)
    
    with torch.no_grad():
        
        logits_per_image, _ = model(image_input, text_tokens)
        
        
        probs = logits_per_image.softmax(dim=-1).cpu().numpy()
        
    final_probs = []
    
    for img_probs in probs:
        
        idx = 0
        
        acc_prob = sum(img_probs[idx : idx + len(ACCIDENT_PROMPTS)])
        idx += len(ACCIDENT_PROMPTS)
        
        norm_prob = sum(img_probs[idx : idx + len(NORMAL_PROMPTS)])
        idx += len(NORMAL_PROMPTS)
        
        blank_prob = sum(img_probs[idx : idx + len(BLANK_PROMPTS)])
        idx += len(BLANK_PROMPTS)
        
        fire_prob = sum(img_probs[idx : idx + len(FIRE_PROMPTS)])
        
        
        
        final_probs.append([acc_prob, norm_prob, blank_prob, fire_prob])
        
    return np.array(final_probs)