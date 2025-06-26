from diffusers import StableDiffusionPipeline

# 1. Load the model (this will download weights on first run)
pipe = StableDiffusionPipeline.from_pretrained(
    "runwayml/stable-diffusion-v1-5", torch_dtype="auto"
)

# 2. Generate & save an image
img = pipe("a fantasy castle in the clouds").images[0]
img.save("test_castle.png")
print("Saved test_castle.png")
