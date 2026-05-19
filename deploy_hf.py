"""Upload the app to the Hugging Face Space.

Run `hf auth login` (paste your HF token) once before running this.
"""
from huggingface_hub import upload_file

REPO = "karimsuba/algeriadish"

FILES = {
    "app.py":          "app.py",
    "requirements.txt": "requirements.txt",
    "models/resnet50_algerian_dishes.pth": "models/resnet50_algerian_dishes.pth",
}

for local, remote in FILES.items():
    print(f"uploading {local} -> {remote}")
    upload_file(
        path_or_fileobj=local,
        path_in_repo=remote,
        repo_id=REPO,
        repo_type="space",
    )

print(f"\ndone -> https://huggingface.co/spaces/{REPO}")
