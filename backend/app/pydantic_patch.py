"""
Monkey-patch to fix Pydantic v1.10 compatibility with Python 3.14
"""
import sys

# This must be imported before FastAPI
import pydantic.main
original_init_subclass = pydantic.main.ModelMetaclass.__init_subclass__

def patched_init_subclass(cls, **kwargs):
    """Fixed __init_subclass__ that handles missing type hints"""
    # Filter out fields without type hints before calling original
    if hasattr(cls, '__annotations__'):
        # Keep only fields that have type hints
        filtered_annotations = {}
        for name, annotation in cls.__annotations__.items():
            if annotation is not None:
                filtered_annotations[name] = annotation
        cls.__annotations__ = filtered_annotations
    
    return original_init_subclass(cls, **kwargs)

# Apply the monkey patch
pydantic.main.ModelMetaclass.__init_subclass__ = patched_init_subclass
