# Configuration file for the Sphinx documentation builder

import os
import sys

# Add project root to Python path
sys.path.insert(0, os.path.abspath('..'))

# Project information
project = 'UK Business Lead Generator'
copyright = '2023, Your Name'
author = 'Your Name'
release = '1.0.0'

# Extensions
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'sphinx.ext.githubpages',
    'sphinx.ext.intersphinx',
    'sphinx_rtd_theme',
]

# Add mappings for intersphinx
intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'pyside6': ('https://doc.qt.io/qtforpython-6/', None),
}

# HTML theme settings
html_theme = 'sphinx_rtd_theme'
html_theme_options = {
    'navigation_depth': 4,
    'titles_only': False,
    'logo_only': False,
}

# Other settings
templates_path = ['_templates']
html_static_path = ['_static']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# Napoleon settings
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = True
napoleon_include_special_with_doc = True
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_preprocess_types = True

# AutoDoc settings
autodoc_member_order = 'bysource'
autodoc_default_flags = ['members', 'undoc-members', 'show-inheritance']

# Source code encoding
source_encoding = 'utf-8'

# The master toctree document
master_doc = 'index'

# Language settings
language = 'en'
today_fmt = '%B %d, %Y'

# Output file settings
html_file_suffix = '.html'
source_suffix = '.rst'