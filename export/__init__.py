import mimetypes

# Add YAML mimetype.
if not mimetypes.inited:
    mimetypes.init()
mimetypes.add_type('text/x-yaml', '.yaml')
