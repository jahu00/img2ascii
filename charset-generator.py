from settings import *

file_name = get_setting_value("dst")
if file_name is None:
    print("Generates a charset file")
    print("Example: python charset-generator.py --dst=ascii.charset --start=32 --end=128")
    print("\n")
    print("--dst - name of the target file")
    print("--start - inclusive start of the charset (default 0)")
    print("--start - exclusive end of the charset (default 256)")
    exit()
start = get_int_setting("start", 0)
end = get_int_setting("end", 256)
charset = list(range(start, end))
charset = [str(i) for i in charset]

with open(file_name, 'w', newline='\n') as f:
    f.write("\n".join(charset))