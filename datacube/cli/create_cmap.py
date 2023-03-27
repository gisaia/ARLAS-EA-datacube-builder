#!/usr/bin/python3

from matplotlib._cm import datad
import json

angular_cmaps = {}
for name, spec in datad.items():
    if 'red' in spec:
        pass
    elif 'listed' in spec:
        pass
    else:
        cmap = "linear-gradient(to right"
        print(name)
        for color in spec:
            if len(color) == 3:
                cmap += f', rgb({int(color[0] * 255)},' + \
                    f' {int(color[1] * 255)}, {int(color[2] * 255)})'
            if len(color) == 2:
                alpha, rgb = color
                r = (rgb[0] * alpha + (1.0 - alpha)) * 255
                g = (rgb[1] * alpha + (1.0 - alpha)) * 255
                b = (rgb[2] * alpha + (1.0 - alpha)) * 255
                cmap += f', rgb({int(r)}, {int(g)}, {int(b)})'
        angular_cmaps[name] = cmap + ')'

with open('dc3_builder-cmaps.json', 'w') as fp:
    json.dump(angular_cmaps, fp, indent=2)
