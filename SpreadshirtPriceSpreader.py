import argparse
import json
import os

parser = argparse.ArgumentParser(
                    prog='SpreadshirtPriceSpreader',
                    description='Spreads the price margin so the win you get will be equal for all products.',
                    epilog='Spread that.')


parser.add_argument('price_csv', help='CSV file to read')
parser.add_argument('-p', '--preset', help='Load arguments from preset', default='none', const='_latest_preset_', nargs="?")
parser.add_argument('-n', '--new-preset', help='Save as preset', default='none', const='_new_preset_', nargs="?")
parser.add_argument('-s', '--spread', type=float, help='The win margin for each product.')
parser.add_argument('-m', '--max-percent', type=float, help='Maximum price increase percent.')
parser.add_argument('-o', '--output-file', help='Use different file for output. Defaults to saving changes to the input file')
parser.add_argument('-b', '--base-price-column-name', dest='base_col', help='Title of the base price column.', default='Base price')
parser.add_argument('-f', '--final-price-column-name', dest='final_col', help='Title of the final price column.', default='Final price')

class Options:
    spread:float | int = -1
    max_multiplier: float | int = -1
    input_file: str = ""
    output_file: str = ""
    base_col: str
    final_col: str
    def __init__(self, args):
        if args.preset != 'none':
            preset = self.get_preset(args.preset, args.price_csv)
            if not preset:
                print(f'Could not find such preset! {args.preset}')
            else:
                if "spread" in preset:
                    self.spread = float(preset["spread"])
                if "max_multiplier" in preset:
                    self.spread = float(preset["max_multiplier"])
                if "input_file" in preset:
                    self.input_file = preset["input_file"]
                if "output_file" in preset:
                    self.output_file = preset["output_file"]
                if "base_col" in preset:
                    self.base_col = preset["base_col"]
                if "final_col" in preset:
                    self.final_col = preset["final_col"]
        if args.spread:
            self.spread = args.spread
        if args.max_percent:
            self.max_multiplier = 1 + (args.max_percent*0.01)
        if args.base_col:
            self.base_col = args.base_col
        if args.final_col:
            self.final_col = args.final_col
        if args.price_csv:
            self.input_file = args.price_csv
        if args.output_file:
            self.output_file = args.output_file
        if args.new_preset != 'none':
            self.save_as_preset(args.new_preset, args.preset)
        if self.output_file == "":
            self.output_file = self.input_file

    def get_presets(self, filename):
        save = False
        presets = {}
        if not os.path.isfile(filename):
            filename = ""
        if os.path.isfile('presets.json'):
            with open('presets.json', 'r+') as f:
                presets = json.load(f)
        if "presets" not in presets:
            presets["presets"] = {}
        if "_locked_default_" not in presets["presets"]:
            presets["presets"]["_locked_default_"] = {
                "spread": 2.5,
                "max_multiplier": -1,
                "input_file": filename,
                "output_file": "",
                "base_col": 'Base price',
                "final_col": 'Final price',
            }
            presets["presets"]["default"] = presets["presets"]["_locked_default_"]
            save = True
        else:
            if filename != "":
                if presets["presets"]["_locked_default_"]["input_file"] == "" or presets["presets"]["default"]["input_file"] == "":
                    print(f'Updating missing filename from default preset...')
                    save = True
                    if presets["presets"]["_locked_default_"]["input_file"] == "":
                        presets["presets"]["_locked_default_"]["input_file"] = filename
                    if presets["presets"]["default"]["input_file"] == "":
                        presets["presets"]["default"]["input_file"] = filename

        if "latest_preset" not in presets:
            presets["latest_preset"] = "_locked_default_"
            save = True
        if save:
            with open('presets.json', 'w+') as f:
                json.dump(presets, f)
        return presets

    def save_as_preset(self, preset_name, input_preset_name):
        presets = self.get_presets(self.input_file)
        if preset_name == "_input_":
            if input_preset_name == "none":
                preset_name = "_new_preset_"
            else:
                if input_preset_name == "_latest_preset_":
                    preset_name = presets["latest_preset"]
                else:
                    preset_name = input_preset_name
        if preset_name == "_locked_default_":
            preset_name = "default"
        if preset_name == "_new_preset_":
            i = 1
            preset_name = "new_preset_" + str(i)
            while preset_name in presets["presets"]:
                i += 1
                preset_name = "new_preset_" + str(i)
            print(f'Saving new preset as {preset_name}')
        presets["presets"][preset_name] = {
            "spread": self.spread,
            "max_multiplier": self.max_multiplier,
            "input_file": self.input_file,
            "output_file": self.output_file,
            "base_col": self.base_col,
            "final_col": self.final_col,
        }
        presets["latest_preset"] = preset_name
        with open('presets.json', 'w+') as f:
            json.dump(presets, f)




    def get_preset(self, preset_name, filename):
        presets = self.get_presets(filename)
        if preset_name != "_latest_preset_" and preset_name in presets["presets"]:
            presets["latest_preset"] = preset_name
            with open('presets.json', 'w+') as f:
                json.dump(presets, f)
        if preset_name == "_latest_preset_":
            if presets["latest_preset"] in presets["presets"]:
                return presets["presets"][presets["latest_preset"]]
            else:
                print("Latest preset corrupted, using default")
                return presets["presets"]["default"]
        if preset_name in presets["presets"]:
            return presets["presets"][preset_name]
        return None






def get_delimiter(line):
    delimiter = ""
    best = 0
    for d in [";", ",", "\t"]:
        h = len(line.split(d))
        if h > best:
            delimiter = d
            best = h
    return delimiter



def main():
    args = parser.parse_args()
    options = Options(args)
    if not os.path.isfile(options.input_file):
        print(f'Error! Input file not found: {options.input_file}')
        return 0


    lines = []
    if options.spread < 0:
        if options.spread == -1:
            print(f'Please set spread with -s')
        else:
            print(f'Error, Spread not set correctly!')
        return 0

    with open(options.input_file, 'r') as f:
        lines = f.readlines()

    if len(lines) < 2:
        print(f'Could not parse the prices: \n{"".join(lines)}')
        return 0

    delimiter = get_delimiter(lines[0].strip())
    header = lines[0].strip().split(delimiter)
    base = -1
    final = -1
    for i in range(len(header)):
        if header[i].strip() == options.base_col:
            base = i
        if header[i].strip() == options.final_col:
            final = i
    if base == -1:
        print(f'Could not find base price column {options.base_col} from header')
    if final == -1:
        print(f'Could not find final price column {options.final_col} from header')
    if base == -1 or final == -1:
        print("Header: ", lines[0].strip())
        return 0

    items = 0
    changed = 0
    maxed_out = 0
    error = 0
    for l in range(1, len(lines)):
        line = lines[l].strip().split(delimiter)
        if len(line) > 0:
            if len(line) != len(header):
                print(f'Error! Malformed line in file: {options.input_file}, line: {l}, content: {lines[l].strip()}')
                print(f'Was expecting {len(header)} items, found {len(line)}.')
                error += 1
                continue
            base_price = float(line[base])
            final_price = float(line[final])
            new_price = base_price + options.spread
            if options.max_multiplier != -1:
                if new_price > base_price * options.max_multiplier:
                    new_price = base_price * options.max_multiplier
                    maxed_out += 1
            if new_price != final_price:
                changed += 1
            items += 1
            line[final] = f'{new_price:.2f}'
            lines[l] = delimiter.join(line) + "\n"
        pass
    print(f'Found {items} items, changed price for {changed}, ({maxed_out} maxed out), {error} errors')

    with open(options.output_file, 'w+') as f:
        f.writelines(lines)
    return 1

if __name__ == '__main__':
    main()