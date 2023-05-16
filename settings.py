from PIL import Image
import sys

def get_setting_values(setting_name, settings = sys.argv, prefix = "--", suffix = "="):
    affixed_setting_name = prefix + setting_name + suffix
    prefix_len = len(affixed_setting_name)
    results = [x[prefix_len:] for x in settings if x.startswith(affixed_setting_name)]
    return results

def get_setting_value(setting_name, settings = sys.argv, prefix = "--", suffix = "="):
    values = get_setting_values(setting_name=setting_name, settings=settings, prefix=prefix, suffix=suffix)
    values_len = len(values)
    if values_len == 0:
        return None
    assert values_len < 2, "expected 1 or 0 settings with name " + setting_name 
    return values[0]

def get_int_setting(setting_name, default = None, settings = sys.argv, prefix = "--", suffix = "="):
    value = get_setting_value(setting_name=setting_name, settings=settings, prefix=prefix, suffix=suffix)
    if value is None:
        return default
    
    return int(value)

def get_bool_setting(setting_name, settings = sys.argv, prefix = "--"):
    values = get_setting_values(setting_name=setting_name, settings=settings, prefix=prefix, suffix="")
    for value in values:
        if len(value) == 0:
            return True
        
    return False

def get_resampling_setting(setting_name, default = None, settings = sys.argv, prefix = "--", suffix = "="):
    value = get_setting_value(setting_name=setting_name, settings=settings, prefix=prefix, suffix=suffix)
    if value is None:
        return default
    
    value = value.lower()

    match value:
        case 'bilinear':
            return Image.BILINEAR
        case 'bicubic':
            return Image.BICUBIC
        case 'lanczos':
            return Image.LANCZOS
        case 'nearest':
            return Image.NEAREST
    
    raise ValueError("Invalid resampling method " + value)