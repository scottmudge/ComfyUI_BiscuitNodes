# ComfyUI_BiscuitNodes

Just some custom nodes I made to make it easier to load images on a local deployment, without having to make duplicates via the traditional 'upload' method.

## Image Path Picker


## Installation
Just git clone into your custom_nodes folder.

## Usage Example
![usage](./usage.jpg)

## PIL.Image
```python
def PILToImage(
    images: PilImage
) -> Image
```
```python
def PILToMask(
    images: PilImage
) -> Image
```
```python
def ImageToPIL(
    images: Image
) -> PilImage
```