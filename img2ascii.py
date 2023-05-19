from PIL import Image, ImageDraw, ImageOps, ImageColor
import math
from settings import *
import time

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

def compare_images(image1, image2, aggregate_method=sum):
    pixels1 = get_pixels(image1)
    pixels2 = get_pixels(image2)
    
    return compare_pixels(pixels1, pixels2, aggregate_method=aggregate_method)

def is_touple_or_list(var1):
    if type(var1) is tuple or type(var1) is list:
        return True
    
    return False

def compare_pixels(pixels1, pixels2, aggregate_method=sum, weights=[1,1,1,1]):
    pixels1_len = len(pixels1)
    pixels2_len = len(pixels2)
    if pixels1_len != pixels2_len:
        raise ValueError("mismatching pixle count")
    
    result = 0

    is_enumerable = None

    for i in range(0, pixels1_len):
        pixel1 = pixels1[i]
        pixel2 = pixels2[i]
        diffs = []
        if is_enumerable is None:
            is_enumerable = is_touple_or_list(pixel1)
        if is_enumerable:
            for n in range(len(pixel1)):
                diffs.append(abs(pixel1[n] - pixel2[n])*weights[n])
        else:
            diffs.append(abs(pixel1 - pixel2)*weights[0])

        result += aggregate_method(diffs)

    return result

def pixels_to_touple(pixels):
    result = []
    for pixel in pixels:
        result += list(pixel)

    return tuple(result)

def square_sum(values):
    values = [value * value for value in values]
    return sum(values)

def read_ints(file_name):
    with open(file_name, 'r') as f:
        ints = [int(line.rstrip()) for line in f]
        return ints

def read_int_lists(file_name):
    with open(file_name, 'r') as f:
        lists = [[int(value) for value in line.strip().split(",")] for line in f]
        return lists

def read_colors(file_name):
    with open(file_name, 'r') as f:
        colors = [ImageColor.getcolor(line.strip(), "RGB") for line in f]
        return colors

def get_proportions(str_value):
    x, y = [float(value) for value in str_value.split(":")]
    return x / y

src_image_name = get_setting_value("src")
if src_image_name is None:
    raise ValueError("src has to befined")

dst_image_name = get_setting_value("dst")
if dst_image_name is None:
    raise ValueError("dst has to befined")

start_time = time.time()

mode = "grayscale"
font_name = get_str_setting("font")#"ega_8x8.png"

font_image = Image.open(font_name)
font_image = font_image.convert("L")
character_size = get_resolution_setting("char-size", (8,8))
character_width, character_height = character_size
characters_per_row = int(font_image.width / character_width)

charset_name = get_str_setting("charset")
charset = []
if charset_name is not None:
    charset = read_ints(charset_name + ".charset")
else:
    character_count = int((font_image.height / character_height) * characters_per_row)
    charset = list(range(character_count))

charmap_name = get_str_setting("charmap")
charmap = None
if charmap_name is not None:
    charmap = read_ints(charmap_name + ".charmap")

output = "image"
output_mode_str = get_resolution_setting("output", "auto")

if output_mode_str == "text":
    output = "text"
elif output_mode_str == "auto":
    if dst_image_name.endswith(".txt"):
        output = "text"

output_size = get_resolution_setting("output-size", (80,40))
cols, rows = output_size
invert = get_bool_setting("invert")
adjust_brightness = get_bool_setting("adjust-brightness")
enable_lookup = get_bool_setting("lookup")
crop = get_str_setting("crop")
color_space = get_str_setting("color-space", "RGB")
upscale = get_int_setting("upscale", 1)
correction_str = get_str_setting("correction", "1:1")
correction = get_proportions(correction_str)

tile_size = get_resolution_setting("tile-size", (1,1))
tile_width, tile_height = tile_size
tile_resampler = get_resampling_setting("tile-resampler", Image.BICUBIC)
character_resampler = get_resampling_setting("tile-resampler", Image.BICUBIC)
aggregate_method_name = get_str_setting("aggregate", "sum")
weights = get_float_settings("weight", [1, 1, 1, 1])
aggregate_method = sum

if aggregate_method_name == "sqr_sum":
    aggregate_method = square_sum

colors = [(0,0,0),(255,255,255)]
colors_name = get_str_setting("colors")
if colors_name is not None:
    colors = read_colors(colors_name + ".colors")

color_combinations_str = get_str_setting("palette")
color_combinations = []
if color_combinations_str is not None:
    color_combinations = read_int_lists(color_combinations_str + ".palette")
else:
    for background_color_id, background_color in enumerate(colors):
       for foreground_color_id, foreground_color in enumerate(colors):
           if foreground_color_id == background_color_id:
               continue
           color_combinations.append((background_color_id, foreground_color_id))

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

src_image = Image.open(src_image_name)
src_image = src_image.convert("RGB")

if invert:
    src_image = ImageOps.invert(src_image)

dst_proportions = dst_width_corrected / dst_height_corrected
src_proportions = src_image.width / src_image.height

if dst_proportions != src_proportions:
    cropped_width = src_image.width
    cropped_height = src_image.height
    if crop == "inner":
        if dst_proportions < src_proportions:
            cropped_width = src_image.height * dst_proportions
        else:
            cropped_height = src_image.width / dst_proportions
    crop_left = int((src_image.width - cropped_width) / 2)
    crop_top = int((src_image.height - cropped_height) / 2)
    crop_right = crop_left + cropped_width
    crop_bottom = crop_top + cropped_height
    src_image = src_image.crop((crop_left, crop_top, crop_right, crop_bottom))

downscaled_src_image = src_image.resize((cols * tile_width, rows * tile_height), tile_resampler)

palette = []
brightnesses = []

for character_id in charset:
    x = character_id % characters_per_row
    y = math.floor(character_id / characters_per_row)
    character_image = font_image.crop((x * character_width, y * character_height, (x + 1) * character_width, (y + 1) * character_height))
    for background_color_id, foreground_color_id in color_combinations:
        colorized_character_image = paint_character(character_image, colors[background_color_id], colors[foreground_color_id])
        character_tile_image = colorized_character_image.resize(tile_size, character_resampler)
        
        if adjust_brightness:
            average_image = colorized_character_image.resize((1,1), character_resampler)
            average_image = average_image.convert("L")
            average = get_pixels(average_image)[0]
            brightnesses.append(average)
        
        character_tile_image = character_tile_image.convert(color_space)

        palette.append({
            "character_id": character_id,
            "character_image": colorized_character_image,
            #"tile_image": character_tile_image,
            "tile_pixels": get_pixels(character_tile_image),
            "background_color_id": background_color_id,
            "foreground_color_id": foreground_color_id
            })

if adjust_brightness:
    brightnesses.sort()

    min_brightness = min(brightnesses)
    max_brightness = max(brightnesses)

    assert max_brightness > min_brightness, "charset results in a single brightness"


    b = -1 * min_brightness
    a = (255 + b) / max_brightness
    
    if color_space == "L":
        for character in palette:
            character["tile_pixels"] = [pixel * a + b for pixel in character["tile_pixels"]]

# brightness_map = []

# for i in range(256):
#     matching_brightness = None
#     last_sign = None
#     last_diff = None
#     for brightness in brightnesses:
#         diff = brightness - i
#         diff_sign = sign(diff)
#         if last_diff is not None and matching_brightness is not None and last_sign is not None and last_sign != diff_sign:
#             if abs(last_diff) > abs(diff):
#                 matching_brightness = brightness
#                 break
#             break
#         matching_brightness = brightness
#         last_sign = diff_sign
#         last_diff = diff
    
#     brightness_map.append([matching_brightness])

#src_pixels = get_pixels(downscaled_src_image)

if output == "image":
    dst_image = Image.new(mode="RGB", size=(dst_width, dst_height))
    dst_image_draw = ImageDraw.Draw(dst_image)

dst_text = ""

lookup = {}
for row in range(rows):
    for col in range(cols):
        palette_match = []
        image_tile = downscaled_src_image.crop((col * tile_width, row * tile_height, (col + 1) * tile_width, (row + 1) * tile_height))
        image_tile = image_tile.convert(color_space)
        tile_pixels = get_pixels(image_tile)
        lookup_key = None
        character_match = None
        
        if enable_lookup:
            if color_space == "L":
                lookup_key = tuple(tile_pixels)
            else:
                lookup_key = pixels_to_touple(tile_pixels)
            character_match = lookup.get(lookup_key)

        if character_match is None:
            for character in palette:
                diff = compare_pixels(tile_pixels, character["tile_pixels"], aggregate_method=aggregate_method, weights=weights)
                palette_match.append({"diff": diff, "character": character})

            palette_match.sort(key=lambda match: match["diff"])
            character_match = palette_match[0]["character"]

        if enable_lookup:
            lookup[lookup_key] = character_match

        #possible_brightnesses = brightness_map[pixel]
        #brightness = possible_brightnesses[(pixel_count % len(possible_brightnesses)) - 1]
        #characters = character_brightness_map[brightness]
        #character = characters[(pixel_count % len(characters)) - 1]
        if output == "text":
            if charmap is None:
                dst_text += chr(character_match["character_id"])
            else:
                dst_text += chr(charmap[character_match["character_id"]])

        if output == "image":
            dst_image.paste(character_match["character_image"], (col * character_width, row * character_height))
        #pixel_count += 1
    
    dst_text += "\n"

#print(dst_text)

if output == "image":
    dst_image = dst_image.resize(dst_size_corrected, Image.NEAREST)
    dst_image.save(dst_image_name)

if output == "text":
    with open(dst_image_name, 'w', newline='\n', encoding="utf8") as f:
        f.write(dst_text)

print("Complete in %s s" % (time.time() - start_time))

#venv\Scripts\activate.bat
#python img2ascii.py --src=test.png --dst=output/test_output_30.png --charset=block --upscale=2 --crop=inner --color-space=HSV --lookup --aggregate=sqr_sum --correction=3:4
#python img2ascii.py --src=test.png --dst=output/test_output_33.txt --charset=ascii --upscale=2 --crop=inner --color-space=L --lookup --aggregate=sum --correction=3:4 --adjust-brightness --invert --charmap=utf8