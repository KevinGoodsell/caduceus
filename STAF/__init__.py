# Copyright 2012 Kevin Goodsell
#
# This software is licensed under the Eclipse Public License (EPL) V1.0.

'''
Interface to the STAF API.
'''

# Using __all__ makes pydoc work properly. Otherwise it looks at the modules the
# items actually come from and assumes they don't belong in the docs for
# __init__.
__all__ = [
    'REQ_SYNC', 'REQ_FIRE_AND_FORGET', 'REQ_QUEUE', 'REQ_RETAIN',
    'REQ_QUEUE_RETAIN', 'Handle', 'wrap_data', 'add_privacy_delimiters',
    'remove_privacy_delimiters', 'mask_private_data',
    'escape_privacy_delimiters', 'errors', 'strerror', 'STAFError',
    'STAFResultError', 'unmarshal', 'unmarshal_force', 'STAFUnmarshalError',
    'MapClassDefinition', 'MapClass', 'UNMARSHAL_RECURSIVE',
    'UNMARSHAL_NON_RECURSIVE', 'UNMARSHAL_NONE',
]

from ._staf import (
    REQ_SYNC,
    REQ_FIRE_AND_FORGET,
    REQ_QUEUE,
    REQ_RETAIN,
    REQ_QUEUE_RETAIN,
    Handle,
    wrap_data,
    add_privacy_delimiters,
    remove_privacy_delimiters,
    mask_private_data,
    escape_privacy_delimiters,
)

from ._errors import (
    errors,
    strerror,
    STAFError,
    STAFResultError,
)

from ._marshal import (
    unmarshal,
    unmarshal_force,
    STAFUnmarshalError,
    MapClassDefinition,
    MapClass,
    UNMARSHAL_RECURSIVE,
    UNMARSHAL_NON_RECURSIVE,
    UNMARSHAL_NONE,
)
