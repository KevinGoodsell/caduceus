'''
Interface to the STAF API.
'''

# Using __all__ makes pydoc work properly. Otherwise it looks at the modules the
# items actually come from and assumes they don't belong in the docs for
# __init__.
__all__ = [
    'Handle', 'wrap_data', 'add_privacy_delimiters',
    'remove_privacy_delimiters', 'mask_private_data',
    'escape_privacy_delimiters', 'errors', 'strerror', 'STAFError',
    'STAFResultError', 'unmarshal', 'STAFUnmarshalError', 'MapClassDefinition',
    'MapClass', 'unmarshal_recursive', 'unmarshal_non_recursive',
    'unmarshal_none',
]

from ._staf import (
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
    STAFUnmarshalError,
    MapClassDefinition,
    MapClass,
    unmarshal_recursive,
    unmarshal_non_recursive,
    unmarshal_none,
)
