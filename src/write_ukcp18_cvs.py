    # -*- coding: utf-8 -*-

import argparse
import json
import os
import uuid
import datetime

import arrow

import pyessv



# Define command line options.
_ARGS = argparse.ArgumentParser('Maps raw vocab files to normalized pyessv CV format.')
_ARGS.add_argument(
    '--source',
    help='Path from which raw vocab files will be read.',
    dest='source',
    type=str
    )

COLLECTION_NAME_TMPL = "UKCP UKCP18 CV collection: "

# Ensure we use fixed creation date.
_CREATE_DATE = datetime.datetime.now()

# CV authority.
_AUTHORITY = pyessv.create_authority(
    'UKCP',
    'UK Climate Projections',
    label='UKCP',
    url='https://tba.tba.com/tba',
    create_date=_CREATE_DATE
    )

# CV scope.
_SCOPE_UKCP18 = pyessv.create_scope(_AUTHORITY,
    'UKCP18',
    'Controlled Vocabularies (CVs) for use in UKCP18',
    label='UKCP18',
    url='https://github.com/ukcp-data/UKCP18_CVs',
    create_date=_CREATE_DATE
    )

# CV scope = GLOBAL.
_SCOPE_GLOBAL = pyessv.create_scope(_AUTHORITY,
    'GLOBAL',
    'Global controlled Vocabularies (CVs)',
    url='https://github.com/ukcp-data/UKCP18_CVs',
    create_date=_CREATE_DATE
    )

# Map of scopes to collections.
_SCOPE_COLLECTIONS = {
  _SCOPE_UKCP18: {
    'activity_id': {
        'data_factory': None
    },
    'admin_region': {
        'data_factory': None
    },
    'collection': {
        'data_factory': None
    },
    'coordinate': {
        'data_factory': lambda obj, name: obj[name]
    },
    'country': {
        'data_factory': None
    },
    'dataset_id': {
        'data_factory': None
    },
    'domain': {
        'data_factory': None
    },
    'ensemble_member': {
        'data_factory': None
    },
    'experiment_id': {
        'data_factory': lambda obj, name: obj[name]
    },
    'frequency': {
        'data_factory': None
    },
    'institution_id': {
        'data_factory': lambda obj, name: {'postal_address': obj[name]}
    },
    'license': {
        'data_factory': None
    },
    'marine_input_model': {
        'data_factory': None
    },
    'prob_data_type': {
        'data_factory': None
    },
    'project': {
        'data_factory': None
    },
    'projection': {
        'data_factory': None
    },
    'resolution': {
        'data_factory': None
    },
    'river_basin': {
        'data_factory': None
    },
    'scenario': {
        'data_factory': None
    },
    'source_id': {
        'data_factory': lambda obj, name: obj[name]
    },
    'source_type': {
        'data_factory': None
    },
    'variable': {
        'data_factory': lambda obj, name: obj[name]
    }
  },
  _SCOPE_GLOBAL: {
  }
}

# Path to file tracking unique identifiers.
_UID_FPATH = __file__.replace('.py', '.json')

# Map of node namespaces to unique identifiers.
#with open(_UID_FPATH, 'r') as fstream:
#    _UID_MAP = json.loads(fstream.read())
_UID_MAP = {}


def _main(args):
    """Main entry point.

    """
    if not os.path.isdir(args.source):
        raise ValueError('Vocab directory does not exist')

    # Create collections.
    for scope in _SCOPE_COLLECTIONS:
        for collection in _SCOPE_COLLECTIONS[scope]:
            cfg = _SCOPE_COLLECTIONS[scope][collection]
            _create_collection(args.source, scope, collection, cfg)

    # Update uid map for next time.
    _set_node_uid(_AUTHORITY)
#    with open(_UID_FPATH, 'w') as fstream:
#        fstream.write(json.dumps(_UID_MAP))

    # Add to archive & persist to file system.
    pyessv.archive(_AUTHORITY)


def _create_collection(source, scope, collection_id, config):
    """Creates collection from a JSON file.

    """
    defaults = {
            'cim_document_type': None,
            'cim_document_type_synonym': None,
            'data_factory': None,
            'is_virtual': False,
            'label': None,
            'ommitted': [],
            'term_regex': None
    }
    defaults.update(config)
    cfg = defaults

    # Create collection.
    collection = pyessv.create_collection(
        scope,
        collection_id,
        COLLECTION_NAME_TMPL.format(collection_id),
        label=cfg['label'] or collection_id.title().replace('_Id', '_ID').replace('_', ' '),
        create_date=_CREATE_DATE,
        term_regex=cfg['term_regex'] or pyessv.REGEX_CANONICAL_NAME,
        data = None if cfg['cim_document_type'] is None else {
            'cim_document_type': cfg['cim_document_type'],
            'cim_document_type_synonym': cfg['cim_document_type_synonym']
            }
        )

    # Load JSON data & create terms (if collection is not a virtual one).
    if cfg['is_virtual'] == False:
        cv_data = _get_cv(source, scope, collection_id)
        data_factory = cfg['data_factory']
        for term_name in [i for i in cv_data if i not in cfg['ommitted']]:
            term_data = data_factory(cv_data, term_name) if data_factory else None
            _create_term(collection, term_name, term_data)


def _create_term(collection, raw_name, data):
    """Creates & returns a new term.

    """
    try:
        description = data['description']
    except (TypeError, KeyError):
        description = None
#    else:
#        del data['description']

    try:
        label = data['label']
    except (TypeError, KeyError):
        label = raw_name
    else:
        del data['label']

    term = pyessv.create_term(
        collection,
        raw_name,
        description=description,
        label=label,
        create_date=_CREATE_DATE,
        data=data
        )


def _set_node_uid(node):
    """Creates & returns a new term.

    """
    if node.namespace in _UID_MAP:
        node.uid = uuid.UUID(_UID_MAP[node.namespace])
    else:
        _UID_MAP[node.namespace] = unicode(node.uid)

    try:
        iter(node)
    except TypeError:
        pass
    else:
        for node in node:
            _set_node_uid(node)


def _get_cv(source, scope, collection_id):
    """Returns raw CV data.

    """
    prefix = '{}_'.format(scope.canonical_name.upper())
    fname = '{}{}.json'.format(prefix, collection_id)
    fpath = os.path.join(source, fname)
    with open(fpath, 'r') as fstream:
        return json.loads(fstream.read())[collection_id]


# Entry point.
if __name__ == '__main__':
    _main(_ARGS.parse_args())
