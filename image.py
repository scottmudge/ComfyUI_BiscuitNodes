import torch

import hashlib
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageOps
import numpy as np
from .imagepicker import get_selected_image

NodeMemMap = {}

def create_new_memmap_entry():
    return {
        'last_seed': -1,
        'last_path': None
    }

def get_node_from_memmap(unique_id: str):
    if unique_id not in NodeMemMap:
        NodeMemMap[unique_id] = create_new_memmap_entry()
    return NodeMemMap[unique_id]

class LoadImagePrompted:
    @classmethod
    def INPUT_TYPES(s):
        return {
        "required": {
            "seed": ("INT", {
            "default": 0,
            "min": -1125899906842624,
            "max": 1125899906842624
            }),
        },
        "hidden": {
            "unique_id": "UNIQUE_ID",
      },
    }

    CATEGORY = "image"

    RETURN_TYPES = ("IMAGE", "MASK")
    FUNCTION = "load_image"
    
    @staticmethod
    def get_node_data(unique_id):
        if unique_id is None:
            return get_node_from_memmap('unknown')
        return get_node_from_memmap(str(unique_id))
    
    def load_image(self, seed, unique_id=None):
        node_data = LoadImagePrompted.get_node_data(unique_id=unique_id)
        image = None
        if seed != node_data['last_seed'] or node_data['last_path'] is None:
            # image = crossfiledialog.open_file("Select Image", filter={'Image files:': ['*.png', '*.jpg', '*.jpeg', '*.bmp', '*.gif', '*.tiff', '*.webp', '*.tga']})
            image = get_selected_image(filter=['*.png', '*.jpg', '*.jpeg', '*.bmp', '*.gif', '*.tiff', '*.webp', '*.tga'])
        else:
            image = node_data['last_path']
        if image is None:
            return (None, None)
        node_data['last_path'] = image
        node_data['last_seed'] = seed
        # print(f"load_image(): unique_id: {unique_id}, last image_path: {image}, seed: {seed}")
        image_path = LoadImagePrompted._resolve_path(image)

        i = Image.open(image_path)
        i = ImageOps.exif_transpose(i)
        image = i.convert("RGB")
        image = np.array(image).astype(np.float32) / 255.0
        image_width = image.shape[1]
        image_height = image.shape[0]
        image = torch.from_numpy(image)[None,]
        if 'A' in i.getbands():
            mask = np.array(i.getchannel('A')).astype(np.float32) / 255.0
            mask = 1. - torch.from_numpy(mask)
        else:
            mask = torch.zeros((image_height, image_width), dtype=torch.float32, device="cpu")
        return (image, mask)

    def _resolve_path(image) -> Path:
        if image is None:
            return None
        return Path(image)

    @classmethod
    def IS_CHANGED(s, seed, unique_id=None):
        node_data = LoadImagePrompted.get_node_data(unique_id=unique_id)
        image_path = LoadImagePrompted._resolve_path(node_data['last_path'])
        if image_path is None:
            return float("NaN")
        m = hashlib.sha256()
        with open(image_path, 'rb') as f:
            m.update(f.read())
        hex_digest = m.digest().hex()
        # print(f"IS_CHANGED: unique_id: {unique_id}, last image_path: {image_path}, hex_digest: {hex_digest}")
        return hex_digest

    @classmethod
    def VALIDATE_INPUTS(s, seed, unique_id=None):
        node_data = LoadImagePrompted.get_node_data(unique_id=unique_id)
        # If image is an output of another node, it will be None during validation
        if node_data['last_path'] is None:
            return True

        image_path = LoadImagePrompted._resolve_path(node_data['last_path'])
        if not image_path.exists():
            return "Invalid image path: {}".format(image_path)

        return True
