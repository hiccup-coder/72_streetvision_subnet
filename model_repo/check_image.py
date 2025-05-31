
from huggingface_hub import HfApi, HfFolder, Repository
from transformers import AutoModelForImageClassification, AutoImageProcessor
from transformers import pipeline

def upload_model_to_huggingface():
    # Define the model repository and local directory
    repo_name = "rossijakob/street_roadvision"  # or "username/street_roadvision" for full path
    local_dir = "./roadwork"

    # Create a new repository on Hugging Face
    api = HfApi()
    api.create_repo(repo_id=repo_name, repo_type="model", exist_ok=True)

    # Upload the model files from the local directory
    from huggingface_hub import upload_folder
    upload_folder(
        repo_id=repo_name,
        folder_path=local_dir,
        repo_type="model"
    )

    print(f"Uploaded model to: https://huggingface.co/{repo_name}")


pipe = pipeline("image-classification", model="rossijakob/street_roadvision")

def classify_image(image_path):
    # Load the image
    from PIL import Image
    image = Image.open(image_path)

    # Perform classification
    results = pipe(image)

    # Print the results
    for result in results:
        print(f"Label: {result['label']}, Score: {result['score']}")

        
if __name__ == "__main__":
    # upload_model_to_huggingface()
    classify_image("./image.jpg")  # Replace with your image path
