import os
from huggingface_hub import InferenceClient

# Simple convnext inference via HF Inference API
client = InferenceClient(
    provider="hf-inference",
    api_key=os.environ.get("HUGGINGFACE_TOKEN")
)

if __name__ == "__main__":
    # Replace with a real image path
    image_path = "sample_frame.jpg"
    if not os.path.exists(image_path):
        print(f"Image not found: {image_path}")
    else:
        result = client.image_classification(
            image_path,
            model="facebook/convnextv2-base-22k-224"
        )
        print(result)
