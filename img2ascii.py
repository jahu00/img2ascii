from PIL import Image, ImageDraw
import sys
import math

#print(f"Arguments count: {len(sys.argv)}")
#for i, arg in enumerate(sys.argv):
#    print(f"Argument {i:>6}: {arg}")

def sign(number):
    if math.isnan(number):
        return float('nan')
    if (number == 0):
        return 0
    if (number > 0):
        return 1

    return -1

def get_pixels(image):
    return list(image.getdata())

def paint_character(character_image, background_color, foreground_color):
    result = Image.new("RGB", (character_image.width, character_image.height))
    src_pixels = get_pixels(character_image)
    dst_pixels = []
    for pixel in src_pixels:
        if pixel == 0:
            dst_pixels.append(background_color)
            continue

        dst_pixels.append(foreground_color)

    result.putdata(dst_pixels)
    return result

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
    

src_image_name = sys.argv[1]
dst_image_name = sys.argv[2]
mode = "grayscale"
font_name = "ega_8x8.png"
charset = list(range(32, 128))
cols = 80
#rows = 25
rows = 40
character_width = 8
#character_height = 16
character_height = 8
invert = get_bool_setting("invert")
adjust_brightness = get_bool_setting("adjust-brightness")
#crop = get_bool_setting("--adjust-brightness")
upscale = get_int_setting("upscale", 1)
correction = 3 / 4

foreground_colors = [(0,0,0),(85,85,85),(170,170,170),(255,255,255)]
background_colors = [(0,0,0),(170,170,170)]
froeground_color_map = [0,8,7,15]
background_color_map = [0,7]

dst_width = cols * character_width
dst_height = rows * character_height

dst_size = (dst_width, dst_height)

dst_width_corrected = int(dst_width * upscale)
dst_height_corrected = int(dst_height * upscale)

if correction < 1:
    dst_height_corrected = int(dst_height_corrected / correction)

if correction > 1:
    dst_width_corrected = int(dst_width_corrected * correction)

dst_size_corrected = (dst_width_corrected, dst_height_corrected)

font_image = Image.open(font_name)
font_image = font_image.convert("L")
characters_per_row = font_image.width / character_width

src_image = Image.open(src_image_name)

downscaled_src_image = src_image.resize((cols, rows)).convert("L")

if mode == "grayscale":
    character_brightness_map = {}

    for character_id in charset:
        x = character_id % characters_per_row
        y = math.floor(character_id / characters_per_row)
        character_image = font_image.crop((x * character_width, y * character_height, (x + 1) * character_width, (y + 1) * character_height))
        for background_color_id, background_color in enumerate(background_colors):
            for foreground_color_id, foreground_color in enumerate(foreground_colors):
                if foreground_color == background_color:
                    continue

                colorized_character_image = paint_character(character_image, background_color, foreground_color)
                colorized_character_image = colorized_character_image.convert("L")
                average_image = colorized_character_image.resize((1, 1), Image.BILINEAR)
                average = get_pixels(average_image)[0]
                average = round(average, 0)

                if background_color_id == 1 and foreground_color_id == 0:
                    colorized_character_image.save("dump/" + str(character_id) + "-" + str(average) + ".png")

                if average not in character_brightness_map:
                    character_brightness_map[average] = []

                character_brightness_map[average].append({"character_id": character_id, "character_image": colorized_character_image, "background_color_id": background_color_id, "foreground_color_id": foreground_color_id})

    brightnesses = list(character_brightness_map.keys())
    brightnesses.sort()

    min_brightness = min(brightnesses)
    max_brightness = max(brightnesses)

    assert max_brightness > min_brightness, "charset results in a single brightness"

    if adjust_brightness:
        b = -1 * min_brightness
        a = (255 + b) / max_brightness
        new_character_brightness_map = {}
        for brightness in brightnesses:
            new_brightness = int(brightness) * a + b
            new_character_brightness_map[new_brightness] = character_brightness_map[brightness]
        
        character_brightness_map = new_character_brightness_map
        brightnesses = list(character_brightness_map.keys())



    brightness_map = []

    for i in range(256):
        matching_brightness = None
        last_sign = None
        last_diff = None
        for brightness in brightnesses:
            diff = brightness - i
            diff_sign = sign(diff)
            if last_diff is not None and matching_brightness is not None and last_sign is not None and last_sign != diff_sign:
                if abs(last_diff) > abs(diff):
                    matching_brightness = brightness
                    break
                break
            matching_brightness = brightness
            last_sign = diff_sign
            last_diff = diff
        
        brightness_map.append([matching_brightness])

    src_pixels = get_pixels(downscaled_src_image)

    dst_image = Image.new(mode="L", size=(dst_width, dst_height))
    dst_image_draw = ImageDraw.Draw(dst_image)
    dst_text = ""

    pixel_count = 0
    for row in range(rows):
        for col in range(cols):
            pixel = src_pixels[pixel_count]
            if invert:
                pixel = 255 - pixel

            possible_brightnesses = brightness_map[pixel]
            brightness = possible_brightnesses[(pixel_count % len(possible_brightnesses)) - 1]
            characters = character_brightness_map[brightness]
            character = characters[(pixel_count % len(characters)) - 1]
            dst_text += chr(character["character_id"])
            dst_image.paste(character["character_image"], (col * character_width, row * character_height))
            pixel_count += 1
        
        dst_text += "\n"

    #print(dst_text)

    dst_image = dst_image.resize(dst_size_corrected, Image.NEAREST)

    dst_image.save(dst_image_name)

    #venv\Scripts\activate.bat
    #python img2ascii.py test.png test_output.png