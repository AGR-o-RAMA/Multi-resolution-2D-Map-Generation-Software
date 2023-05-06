import yaml
import Metashape


def convert_objects(a_dict):
    for k, v in a_dict.items():
        if not isinstance(v, dict):
            if isinstance(v, str):
                if v and 'Metashape' in v and not ('path' in k) and not ('project' in k) and not ('name' in k):
                    a_dict[k] = eval(v)
            elif isinstance(v, list):

                a_dict[k] =  [eval(item) for item in v if("Metashape" in item)]
        else:
            convert_objects(v)

def read_yaml(yml_path):
    with open(yml_path,'r') as ymlfile:
        cfg = yaml.load(ymlfile, Loader=yaml.SafeLoader)

    convert_objects(cfg)

    return cfg
