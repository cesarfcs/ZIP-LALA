"""Offer definitions for the Lalaleads advanced reporting tool.

This module defines the different prospecting offers available at Lalaleads and
their associated characteristics. Offers describe how many contacts are
targeted per cycle and which channels are ordinarily included. When a client
subscribes to an offer these values are used to populate the context slides
in generated reports and can also provide defaults within the Streamlit app.

The `OFFERS` dictionary maps an offer name to a dictionary containing:

* ``contacts_target`` – The nominal number of contacts to address per cycle.
  For the "Offre personnalisée" this is left as ``None`` to indicate it
  should be provided by the user.
* ``channels`` – A list of channels automatically included in the offer.
  At minimum this always includes "E-mail" and optionally "Téléphone";
  LinkedIn can be toggled on or off in the UI regardless of the offer.
* ``linkedin_optional`` – A boolean indicating whether LinkedIn is an
  optional channel for the offer. When ``True`` the Streamlit app will
  preselect LinkedIn by default but allow the user to deselect it.

You can import ``OFFERS`` from this module and look up values by offer name.
"""

from __future__ import annotations

OFFERS = {
    "Multi 2J": {
        "contacts_target": 600,
        "channels": ["Téléphone", "E-mail"],
        "linkedin_optional": True,
    },
    "Multi 3J": {
        "contacts_target": 900,
        "channels": ["Téléphone", "E-mail"],
        "linkedin_optional": True,
    },
    "Multi 4J": {
        "contacts_target": 1200,
        "channels": ["Téléphone", "E-mail"],
        "linkedin_optional": True,
    },
    "Multi 5J": {
        "contacts_target": 1500,
        "channels": ["Téléphone", "E-mail"],
        "linkedin_optional": True,
    },
    "Full Digital": {
        "contacts_target": 800,
        "channels": ["E-mail"],
        "linkedin_optional": False,
    },
    "Offre personnalisée": {
        # When the offer is customised the number of contacts per cycle
        # should be provided by the user through the Streamlit interface.
        "contacts_target": None,
        "channels": ["Téléphone", "E-mail"],
        "linkedin_optional": True,
    },
}

__all__ = ["OFFERS"]