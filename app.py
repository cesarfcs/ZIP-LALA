"""
Streamlit application for Lalaleads advanced reporting.

This app allows account managers to upload a CRM export (CSV) and analyse
key prospecting metrics across telephone and email channels. It provides
interactive filters on campaign, job title, sector, company size and
location, as well as a date range filter. Metrics are visualised via
simple charts and tables so that users can quickly understand their
performance and conversion rates.

The app also supports the selection of an offer and the associated
channels for context, although these selections are purely informative
and do not alter the computed metrics. If desired the computed
statistics could later be exported into a PowerPoint via a separate
module.
"""

from __future__ import annotations

import datetime as dt
from typing import List, Optional

import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

from offers import OFFERS
from kpis_advanced import compute_metrics, compute_call_distribution, apply_filters


def _load_csv(uploaded_file) -> pd.DataFrame:
    """Safely load a CSV file from a Streamlit file uploader.

    Returns an empty DataFrame on failure.
    """
    try:
        return pd.read_csv(uploaded_file)
    except Exception:
        return pd.DataFrame()


def _draw_call_summary_chart(metrics: dict) -> None:
    """Draw a bar chart summarising call statistics.

    The chart compares total calls, connected calls, pitch calls and
    telephone RDV to give a quick visual overview of call outcomes.
    """
    labels = ["Appels total", "Appels connectés", "Pitchs", "RDV téléphone"]
    values = [
        metrics["calls_total"],
        metrics["calls_connected"],
        metrics["calls_pitched"],
        metrics["rdv_phone"],
    ]
    fig, ax = plt.subplots(figsize=(6, 3))
    ax.bar(labels, values)
    ax.set_title("Résumé des appels")
    ax.set_xlabel("Statistiques")
    ax.set_ylabel("Nombre de contacts")
    for i, v in enumerate(values):
        ax.text(i, v + max(values) * 0.02, str(v), ha="center", va="bottom")
    st.pyplot(fig)


def _draw_call_tag_pie(call_dist: pd.DataFrame) -> None:
    """Draw a pie chart representing the distribution of call tags.

    Args:
        call_dist: DataFrame containing columns ``tag`` and ``count``.
    """
    if call_dist.empty:
        st.info("Aucune donnée d'appel pour tracer le graphique de distribution des tags.")
        return
    labels = call_dist["tag"].tolist()
    counts = call_dist["count"].tolist()
    fig, ax = plt.subplots(figsize=(4, 4))
    ax.pie(counts, labels=labels, autopct=lambda p: f"{p:.1f}%")
    ax.set_title("Répartition des tags d'appels")
    st.pyplot(fig)


def _draw_email_summary_chart(metrics: dict) -> None:
    """Draw a bar chart summarising email statistics.

    The chart compares contacted, opened and replied counts for the
    e‑mail channel.
    """
    labels = ["Contacts emailés", "Ouvertures", "Réponses"]
    values = [
        metrics["contacts_email"],
        metrics["contacts_opened"],
        metrics["contacts_replied"],
    ]
    fig, ax = plt.subplots(figsize=(6, 3))
    ax.bar(labels, values)
    ax.set_title("Résumé des e-mails")
    ax.set_xlabel("Statistiques")
    ax.set_ylabel("Nombre de contacts")
    for i, v in enumerate(values):
        ax.text(i, v + max(values) * 0.02, str(v), ha="center", va="bottom")
    st.pyplot(fig)


def _draw_rdv_chart(metrics: dict) -> None:
    """Draw a bar chart comparing RDV counts by channel.
    """
    labels = ["RDV téléphone", "RDV e-mail", "RDV total"]
    values = [metrics["rdv_phone"], metrics["rdv_email"], metrics["rdv_total"]]
    fig, ax = plt.subplots(figsize=(6, 3))
    ax.bar(labels, values)
    ax.set_title("Rendez-vous obtenus")
    ax.set_xlabel("Canal")
    ax.set_ylabel("Nombre de RDV")
    for i, v in enumerate(values):
        ax.text(i, v + max(values) * 0.02 if max(values) else 0.02, str(v), ha="center", va="bottom")
    st.pyplot(fig)


def main() -> None:
    st.set_page_config(page_title="Lalaleads – Reporting avancé", layout="wide")
    st.title("Lalaleads – Reporting avancé")
    st.markdown(
        "Chargez un export HubSpot/Lemlist/Aircall, appliquez des filtres et consultez vos KPI en temps réel."
    )

    # Configuration contextuelle (optional)
    with st.expander("Contexte de mission (facultatif)"):
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            client_name = st.text_input("Nom du client", value="Client Exemple")
            offer_name = st.selectbox("Offre souscrite", list(OFFERS.keys()))
        with col2:
            offer_target_default = OFFERS[offer_name]["contacts_target"]
            if offer_name == "Offre personnalisée":
                custom_target = st.number_input(
                    "Contacts par cycle (offre personnalisée)", min_value=100, step=50, value=1600
                )
                contacts_target = int(custom_target)
            else:
                contacts_target = offer_target_default or 0
            report_type = st.selectbox("Type de rapport", ["Hebdomadaire", "Mensuel"])
        with col3:
            report_cycle = st.text_input("Semaine/Cycle", value="Semaine 1")
            channels_default = OFFERS[offer_name]["channels"][:]
            if OFFERS[offer_name]["linkedin_optional"]:
                channels_default = channels_default + ["LinkedIn"]
            channels = st.multiselect(
                "Canaux sélectionnés",
                ["Téléphone", "E-mail", "LinkedIn"],
                default=channels_default,
            )
        # Display context summary (for user awareness)
        st.write(
            f"**{client_name}** – Offre : {offer_name} – Objectifs : {contacts_target} contacts par cycle – Canaux : {', '.join(channels)}"
        )

    # CSV input
    uploaded_file = st.file_uploader("Importer l'export CSV", type=["csv"])
    if uploaded_file is None:
        st.info("Veuillez importer un fichier CSV pour commencer l'analyse.")
        return
    df = _load_csv(uploaded_file)
    if df.empty:
        st.error("Le fichier importé ne peut pas être lu ou est vide.")
        return

    # Date range filter
    st.subheader("Filtres de données")
    today = dt.date.today()
    default_start = today.replace(day=1)
    default_end = today
    start_date, end_date = st.date_input(
        "Période d'analyse (début et fin)",
        value=(default_start, default_end),
        max_value=today,
    )

    # Segmentation filters: compute unique values
    segmentation_cols = {
        "Campagne": "Campagnes",
        "Intitulé du poste": "Intitulés de poste",
        "Secteur": "Secteurs",
        "Taille d'entreprise": "Tailles d'entreprise",
        "Localisation": "Localisations",
    }
    filters = {}
    for col, label in segmentation_cols.items():
        if col in df.columns:
            values = sorted(df[col].dropna().unique())
            if values:
                filters[col] = st.multiselect(label, values)

    # Apply filters
    filtered_df = apply_filters(
        df,
        campaigns=filters.get("Campagne"),
        titles=filters.get("Intitulé du poste"),
        sectors=filters.get("Secteur"),
        sizes=filters.get("Taille d'entreprise"),
        locations=filters.get("Localisation"),
        start_date=pd.to_datetime(start_date) if start_date else None,
        end_date=pd.to_datetime(end_date) if end_date else None,
    )

    # Display how many rows remain after filtering
    st.write(f"**{len(filtered_df)}** contacts après filtrage.")

    # Compute metrics
    metrics = compute_metrics(filtered_df)
    call_dist = compute_call_distribution(filtered_df)

    # Show KPI summary cards
    st.subheader("KPI principaux")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Appels total", metrics["calls_total"])
    k2.metric("Appels connectés", metrics["calls_connected"], f"{metrics['connection_rate']*100:.1f}%")
    k3.metric("Pitchs", metrics["calls_pitched"], f"{metrics['pitch_rate']*100:.1f}%")
    k4.metric("RDV téléphone", metrics["rdv_phone"], f"{metrics['phone_conv_rate']*100:.1f}%")
    k5, k6, k7, k8 = st.columns(4)
    k5.metric("Contacts email", metrics["contacts_email"])
    k6.metric("Ouvertures", metrics["contacts_opened"], f"{metrics['open_rate']*100:.1f}%")
    k7.metric("Réponses", metrics["contacts_replied"], f"{metrics['reply_rate']*100:.1f}%")
    k8.metric("RDV e-mail", metrics["rdv_email"], f"{metrics['email_conv_rate']*100:.1f}%")
    k9, k10 = st.columns(2)
    k9.metric("RDV total", metrics["rdv_total"], f"{metrics['overall_conv_rate']*100:.1f}%")

    # Charts
    st.subheader("Visualisations")
    _draw_call_summary_chart(metrics)
    _draw_call_tag_pie(call_dist)
    _draw_email_summary_chart(metrics)
    _draw_rdv_chart(metrics)

    # Tabular views
    st.subheader("Détails des tags d'appels")
    if call_dist.empty:
        st.write("Pas de données d'appel disponibles.")
    else:
        # Show DataFrame with percentage rates
        tmp = call_dist.copy()
        tmp["rate (%)"] = (tmp["rate"] * 100).round(1)
        tmp = tmp.rename(columns={"tag": "Tag", "count": "Nombre de contacts"})
        st.dataframe(tmp[["Tag", "Nombre de contacts", "rate (%)"]])

    st.subheader("Export filtré (aperçu)")
    st.dataframe(filtered_df.head(50))

    # Optionally allow download of filtered data
    csv_data = filtered_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Télécharger les données filtrées (CSV)",
        csv_data,
        file_name="export_filtre.csv",
        mime="text/csv",
    )


if __name__ == "__main__":
    main()