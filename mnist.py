
#%%
from torchvision.datasets import MNIST
import torchvision.transforms as transforms

# Load dataset and transform images to tensors
dataset = MNIST(root='./data', train=True, download=True, transform=transforms.ToTensor())

# Get the images (trainX) and labels (trainY) as tensors
trainX = dataset.data.unsqueeze(1).float() / 255.0  # Normalize to [0, 1] and add channel dimension
trainY = dataset.targets
# %%
trainX.shape
# %%

trainX[0,0,0,0]
