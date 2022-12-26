from json import load, dump


# Loads data from a json file
def load_from_json(path) -> list:
    with open(f'{path}', 'r') as f:
        return load(f)


# Writes data to a json file
def write_to_json(path: str, data):
    with open(f'{path}', 'w') as f:
        dump(data, f)