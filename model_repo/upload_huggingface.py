
from huggingface_hub import snapshot_download

download_path = snapshot_download(
    repo_id="natix-network-org/roadwork",
    local_dir="./dataset",  # Your custom path
    local_dir_use_symlinks=False  # Optional: avoids symlinks, creates real files
)

# Ensure the directory exists   
print(f"Model downloaded to {download_path}")