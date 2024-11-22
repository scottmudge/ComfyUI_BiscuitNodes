from .image import *

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']

NODE_CLASS_MAPPINGS = {
    'LoadImagePrompted': LoadImagePrompted,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    'LoadImagePrompted': 'Load Image Prompted',
}

print("\033[34mBiscuit Nodes: \033[92mLoaded\033[0m")
