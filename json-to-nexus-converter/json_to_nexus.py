'''
    File name: json_to_nexus.py
    Author: Sherjeel Shabih
    Email: shabihsherjeel@gmail.com
    Date created: 28/10/2021
'''

import json
import h5py
import click
import os

# Prefix to query in the same directory as the Python file. This allows you to run it from anywhere
prefix = os.path.dirname(__file__) + '/'

@click.command()
@click.option('--input', default=prefix + 'input.json', help='The path to the input JSON file.')
@click.option('--translation', default=prefix + 'translation.json', help='The path to the translation map JSON file.')
@click.option('--output', default=prefix + 'output.nxs', help='The path to the output Nexus file generated.')
def run_convert_routine(input, translation, output):
    # Read input file and make a dict out of it
    with open(input, 'r') as f:
        data = json.load(f)

    with open(translation, 'r') as f:
        translation_dict = json.load(f)

    f = h5py.File(str(output), 'w')
    f.attrs['default'] = 'entry'

    nxentry = f.create_group('entry')
    nxentry.attrs["NX_class"] = 'NXentry'
    nxentry.attrs['default'] = 'data'

    nxdata = nxentry.create_group('data')
    nxdata.attrs["NX_class"] = 'NXdata'
    nxdata.attrs['signal'] = 'counts'
    nxdata.attrs['axes'] = 'two_theta'
    nxdata.attrs['two_theta_indices'] = [0,]


    def create_groups_for_path(group, path):
        try:
            return group.create_group(path[0:path.rindex('/')])
        except ValueError as err:
            if str(err) == 'Unable to create group (name already exists)':
                return group[path[0:path.rindex('/')]]
            else:
                raise


    def recursive_dict_to_h5py(d, group, parent=''):
        for k, v in d.items():
            path = parent + '/' + str(k)
            if path in translation_dict:
                path = translation_dict[path]['path']
            if isinstance(v, dict):
                recursive_dict_to_h5py(v, group, path)
            else:
                g = create_groups_for_path(group, path)
                attr_name = path[path.rindex('/')+1:]
                g.attrs[str(attr_name)] = v

    recursive_dict_to_h5py(data, nxentry, '/entry')


if __name__ == '__main__':
    run_convert_routine()