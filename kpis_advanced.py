"""Compute advanced KPIs from a HubSpot/Lemlist/Aircall export.

This module provides functions to compute key metrics required by the
Lalaleads reporting tool. It focuses on three areas:

1. **Telephone metrics** including counts of calls, connected calls,
   pitched calls and rendez‑vous (RDV) obtained via calls, based on the
   presence of an Aircall timestamp and the contents of the "Last used
   Aircall tags" column.
2. **Email metrics** including counts of recipients, opens, replies and
   RDV obtained via e‑mail, based on the Lemlist lead status and the
   phase of the cycle of life.
3. **Rates** to provide conversion figures such as connection rate,
   pitch rate and RDV rates for each channel.

The functions are designed to operate on a ``pandas.DataFrame`` with
columns matching the exported CRM fields. They do not modify the
original DataFrame. Missing columns are tolerated, although metrics
requiring those columns will evaluate to zero.

In addition, a helper function returns a distribution table of call tags
with counts and relative rates to aid in reporting.
"""

from __future__ import annotations

import re
from typing import Dict, Iterable, List, Tuple, Optional

import numpy as np
import pandas as pd

# Define the sets of tags used for various metrics. These sets reflect
# business definitions communicated by the product owner.
CALL_TAGS_ALL: set[str] = {
    "Meeting",
    "Pitch",
    "Sans Suite",
    "Standard",
    "No answer",
    "Numéro Faux",
}

CALL_TAGS_CONNECTED: set[str] = {
    "Meeting",
    "Pitch",
    "Sans Suite",
    "Standard",
}

CALL_TAGS_PITCHED: set[str] = {
    "Meeting",
    "Pitch",
}

CALL_TAGS_RDV: set[str] = {
    "Meeting",
}


def _split_tags(tag_value: Optional[str]) -> List[str]:
    """Split a raw tag string into a list of individual tags.

    Tags exported from HubSpot/Aircall may contain multiple values
    separated by commas, semicolons or pipe characters. This helper
    normalises the input by splitting on common delimiters and stripping
    whitespace from each part. It returns an empty list for missing
    values.

    Args:
        tag_value: Raw tag string from the export; may be None or
            contain multiple tags.

    Returns:
        A list of individual tag strings (upper/lowercase preserved).
    """
    if tag_value is None or (isinstance(tag_value, float) and np.isnan(tag_value)):
        return []
    # Ensure we are working with a string
    value_str = str(tag_value)
    # Split on common delimiters: comma, semicolon, pipe
    parts = re.split(r"[;,|]+", value_str)
    return [p.strip() for p in parts if p.strip()]


def compute_metrics(df: pd.DataFrame) -> Dict[str, float]:
    """Compute a dictionary of advanced KPIs from a CRM export.

    The DataFrame is expected to include the following columns when
    available:

    * ``Last Aircall call timestamp`` – timestamp of the last call,
      used to determine whether a contact has been called.
    * ``Last used Aircall tags`` – string of Aircall tags applied to the
      last call.
    * ``lemlist lead status`` – status of the contact in the Lemlist
      sequence (e.g. "Email sent", "Email opened", "Email replied").
    * ``Phase du cycle de vie`` – CRM lifecycle phase (e.g.
      "RDV - Bon contact").

    Missing columns are handled gracefully; metrics depending on those
    columns will return zero.

    Args:
        df: DataFrame containing CRM export rows.

    Returns:
        A dictionary of computed metrics.
    """
    # Create a working copy to avoid modifying the caller's DataFrame
    data = df.copy()

    # Ensure expected columns exist to prevent KeyError; use NaN when absent
    for col in [
        "Last Aircall call timestamp",
        "Last used Aircall tags",
        "lemlist lead status",
        "Phase du cycle de vie",
    ]:
        if col not in data.columns:
            data[col] = np.nan

    # Normalise boolean presence: call timestamp exists
    called_mask = data["Last Aircall call timestamp"].notna()
    calls_total = int(called_mask.sum())

    # Split tags once for all rows; store list in a new Series for reuse
    tags_series = data["Last used Aircall tags"].apply(_split_tags)

    # Determine whether each row is connected, pitched or RDV based on tags
    def has_any_tag(tags: Iterable[str], target_set: set[str]) -> bool:
        return any(tag in target_set for tag in tags)

    connected_mask = tags_series.apply(lambda tags: has_any_tag(tags, CALL_TAGS_CONNECTED)) & called_mask
    pitched_mask = tags_series.apply(lambda tags: has_any_tag(tags, CALL_TAGS_PITCHED)) & called_mask
    rdv_phone_mask = tags_series.apply(lambda tags: has_any_tag(tags, CALL_TAGS_RDV)) & called_mask

    calls_connected = int(connected_mask.sum())
    calls_pitched = int(pitched_mask.sum())
    rdv_phone = int(rdv_phone_mask.sum())

    # Compute call rates; avoid divide-by-zero errors
    connection_rate = calls_connected / calls_total if calls_total else 0.0
    pitch_rate = calls_pitched / calls_connected if calls_connected else 0.0
    rdv_phone_rate = rdv_phone / calls_total if calls_total else 0.0

    # Email metrics
    # Determine if a contact has been emailed (non-empty status)
    mailed_mask = data["lemlist lead status"].fillna("") != ""
    contacts_email = int(mailed_mask.sum())

    contacts_opened = int((data["lemlist lead status"] == "Email opened").sum())
    contacts_replied = int((data["lemlist lead status"] == "Email replied").sum())

    open_rate = contacts_opened / contacts_email if contacts_email else 0.0
    reply_rate = contacts_replied / contacts_email if contacts_email else 0.0

    # RDV via email: must have replied and be in lifecycle RDV, and not already have a Meeting tag
    rdv_email_mask = (
        (data["Phase du cycle de vie"] == "RDV - Bon contact")
        & (data["lemlist lead status"] == "Email replied")
        & (~rdv_phone_mask)  # exclude contacts who already have a phone RDV
    )
    rdv_email = int(rdv_email_mask.sum())

    rdv_total = rdv_phone + rdv_email

    # Conversion rates per channel
    email_conv_rate = rdv_email / contacts_email if contacts_email else 0.0
    phone_conv_rate = rdv_phone / calls_total if calls_total else 0.0
    overall_conv_rate = rdv_total / max(contacts_email + calls_total - (rdv_email_mask & called_mask).sum(), 1)
    # The denominator for overall conversion is the number of unique contacts
    # who were addressed by at least one channel. We approximate this by
    # summing the two counts and subtracting those who overlap (emailed and
    # called). A fallback of 1 prevents division by zero.

    metrics = {
        "calls_total": calls_total,
        "calls_connected": calls_connected,
        "calls_pitched": calls_pitched,
        "rdv_phone": rdv_phone,
        "connection_rate": connection_rate,
        "pitch_rate": pitch_rate,
        "rdv_phone_rate": rdv_phone_rate,
        "contacts_email": contacts_email,
        "contacts_opened": contacts_opened,
        "contacts_replied": contacts_replied,
        "open_rate": open_rate,
        "reply_rate": reply_rate,
        "rdv_email": rdv_email,
        "rdv_total": rdv_total,
        "email_conv_rate": email_conv_rate,
        "phone_conv_rate": phone_conv_rate,
        "overall_conv_rate": overall_conv_rate,
    }
    return metrics


def compute_call_distribution(df: pd.DataFrame) -> pd.DataFrame:
    """Return a DataFrame summarising call tag distribution and rates.

    The returned DataFrame contains one row per Aircall tag observed in
    the input. It includes counts of contacts whose last call has that
    tag as well as derived rates relative to the total number of calls.

    Args:
        df: DataFrame containing CRM export rows.

    Returns:
        A DataFrame with columns ``tag``, ``count`` and ``rate``.
    """
    if df.empty:
        return pd.DataFrame(columns=["tag", "count", "rate"])

    data = df.copy()
    total_calls = int(data["Last Aircall call timestamp"].notna().sum())
    if total_calls == 0:
        return pd.DataFrame(columns=["tag", "count", "rate"])

    # Flatten tags and count each occurrence per contact (one contact may
    # have multiple tags but we count each contact once per tag)
    tag_counts: Dict[str, int] = {}
    for tags in data["Last used Aircall tags"].apply(_split_tags):
        unique_tags = set(tags)
        for tag in unique_tags:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1

    # Build DataFrame
    tag_list = []
    count_list = []
    rate_list = []
    for tag, count in sorted(tag_counts.items(), key=lambda item: (-item[1], item[0])):
        tag_list.append(tag)
        count_list.append(count)
        rate_list.append(count / total_calls)
    return pd.DataFrame({"tag": tag_list, "count": count_list, "rate": rate_list})


def apply_filters(
    df: pd.DataFrame,
    *,
    campaigns: Optional[List[str]] = None,
    titles: Optional[List[str]] = None,
    sectors: Optional[List[str]] = None,
    sizes: Optional[List[str]] = None,
    locations: Optional[List[str]] = None,
    start_date: Optional[pd.Timestamp] = None,
    end_date: Optional[pd.Timestamp] = None,
) -> pd.DataFrame:
    """Filter the CRM export by various attributes and a date range.

    This helper allows the Streamlit interface to subset the data based on
    user selections for segmentation dimensions (campaigns, job titles,
    sectors, company sizes, locations) and a date interval for the
    analysis. Columns that are missing are ignored when filtering.

    Args:
        df: The full CRM export.
        campaigns: Optional list of campaign names to include.
        titles: Optional list of job titles to include.
        sectors: Optional list of sectors to include.
        sizes: Optional list of company sizes to include.
        locations: Optional list of geographic locations to include.
        start_date: Optional start date for filtering calls and emails.
        end_date: Optional end date for filtering calls and emails.

    Returns:
        A filtered DataFrame.
    """
    data = df.copy()
    # Date filtering based on call timestamp and last activity date
    # Convert to datetime; invalid parsing yields NaT
    for col in ["Last Aircall call timestamp", "Date de la dernière activité"]:
        if col in data.columns:
            data[col] = pd.to_datetime(data[col], errors="coerce")
    if start_date is not None:
        if "Last Aircall call timestamp" in data.columns:
            mask_call = data["Last Aircall call timestamp"].notna() & (data["Last Aircall call timestamp"] >= start_date)
        else:
            mask_call = pd.Series([False] * len(data))
        if "Date de la dernière activité" in data.columns:
            mask_email = data["Date de la dernière activité"].notna() & (data["Date de la dernière activité"] >= start_date)
        else:
            mask_email = pd.Series([False] * len(data))
        # Keep rows where either event occurred after start
        data = data[mask_call | mask_email | ((mask_call | mask_email).sum() == 0)]
    if end_date is not None:
        if "Last Aircall call timestamp" in data.columns:
            mask_call = data["Last Aircall call timestamp"].notna() & (data["Last Aircall call timestamp"] <= end_date)
        else:
            mask_call = pd.Series([False] * len(data))
        if "Date de la dernière activité" in data.columns:
            mask_email = data["Date de la dernière activité"].notna() & (data["Date de la dernière activité"] <= end_date)
        else:
            mask_email = pd.Series([False] * len(data))
        data = data[mask_call | mask_email | ((mask_call | mask_email).sum() == 0)]

    # Apply categorical filters if provided and the column exists
    def filter_if_possible(df_: pd.DataFrame, column: str, values: Optional[List[str]]) -> pd.DataFrame:
        if values:
            if column in df_.columns:
                return df_[df_[column].fillna("").isin(values)]
        return df_

    data = filter_if_possible(data, "Campagne", campaigns)
    data = filter_if_possible(data, "Intitulé du poste", titles)
    data = filter_if_possible(data, "Secteur", sectors)
    data = filter_if_possible(data, "Taille d'entreprise", sizes)
    data = filter_if_possible(data, "Localisation", locations)
    return data


__all__ = [
    "compute_metrics",
    "compute_call_distribution",
    "apply_filters",
]