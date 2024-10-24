#%%
import torch
import matplotlib.pyplot as plt

tensor = torch.tensor
t = torch.tensor([1, 2, 3])

#%%
raw_data = [
    [1,2,3],
    [4,5,6],
    [4,5,6],
    [7,8,9]]
t = tensor(raw_data)

# %%
t + 5
# %%
plt.imshow(t)

#%%

arr = torch.tensor([0, 1, 1])
plt.plot(arr)

#%%
plt.imshow(t * arr)

#%%

t = torch.tensor([
    [1,2,3],
    [4,5,6],
    [4,5,6],
    [7,8,9]])

print(t)
arr = torch.tensor([0, 1, 1])

m = t * arr
print()
print(m)
m.sum(1)

#%%

# 1.problem: sind mehr als ein input neuron aktiv
# 2.problem: sind mehr als zwei input neuron aktiv

arr = torch.tensor([0, 1, 1])

mat = torch.tensor([[0, 5, 0,],
                    [0, 0, 0,]])

pred = (mat @ arr)
pred

#%%

