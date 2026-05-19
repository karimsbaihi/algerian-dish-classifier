"""Gradio app — Algerian Dish Classifier.

Loads the trained ResNet-50 checkpoint and serves a photo -> dish prediction UI.
Run locally:  python app.py
Deploy:       this file + requirements.txt + the .pth go in a Hugging Face Space.
"""
import gradio as gr
import torch
import torch.nn as nn
from torchvision import models, transforms

MODEL_PATH = "resnet50_algerian_dishes.pth"

ckpt = torch.load(MODEL_PATH, map_location="cpu", weights_only=False)
classes = ckpt["classes"]
img_size = ckpt.get("img_size", 224)

model = models.resnet50(weights=None)
model.fc = nn.Linear(model.fc.in_features, len(classes))
model.load_state_dict(ckpt["state_dict"])
model.eval()

preprocess = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(img_size),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
])


def predict(image):
    if image is None:
        return {}
    x = preprocess(image.convert("RGB")).unsqueeze(0)
    with torch.no_grad():
        probs = torch.softmax(model(x), dim=1)[0]
    return {classes[i]: float(probs[i]) for i in range(len(classes))}


demo = gr.Interface(
    fn=predict,
    inputs=gr.Image(type="pil", label="Upload a dish photo"),
    outputs=gr.Label(num_top_classes=3, label="Prediction"),
    title="Algerian Dish Classifier",
    description=(
        "Upload a photo of an Algerian dish. The model recognises 15 dishes: "
        + ", ".join(classes) + "."
    ),
)

if __name__ == "__main__":
    demo.launch()
