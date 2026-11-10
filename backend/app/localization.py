"""French localization for DocuVerify AI backend.

Provides professional French translations for international trade, import/export
documentation, and administrative verification.
"""
from __future__ import annotations

import os
from typing import Literal

Language = Literal["en", "fr"]

# Default to French as requested
DEFAULT_LANGUAGE: Language = "fr"

# In-memory language state (set per-request via middleware/header)
_current_lang: Language = DEFAULT_LANGUAGE


def get_language() -> Language:
    return _current_lang


def set_language(lang: Language) -> None:
    global _current_lang
    if lang in ("en", "fr"):
        _current_lang = lang


# French document type names (professional trade terminology)
DOC_TYPES: dict[str, dict[str, str]] = {
    "commercial_invoice": {"en": "Commercial Invoice", "fr": "Facture commerciale"},
    "packing_list": {"en": "Packing List", "fr": "Liste de colisage"},
    "bill_of_lading": {"en": "Bill of Lading", "fr": "Connaissement"},
    "certificate_of_origin": {"en": "Certificate of Origin", "fr": "Certificat d'origine"},
    "certificate_of_quality": {"en": "Certificate of Quality", "fr": "Certificat de qualité"},
    "certificate_of_conformity": {"en": "Certificate of Conformity", "fr": "Certificat de conformité"},
    "phytosanitary_certificate": {"en": "Phytosanitary Certificate", "fr": "Certificat phytosanitaire"},
    "fumigation_certificate": {"en": "Fumigation Certificate", "fr": "Certificat de fumigation"},
    "unknown": {"en": "Unrecognized pages", "fr": "Pages non identifiées"},
}

# Status labels
STATUSES: dict[str, dict[str, str]] = {
    "passed": {"en": "Passed", "fr": "Conforme"},
    "complete": {"en": "Complete", "fr": "Complet"},
    "needs_review": {"en": "Needs review", "fr": "À vérifier"},
    "mismatch": {"en": "Mismatch", "fr": "Discordance"},
    "needs_ocr": {"en": "Needs OCR", "fr": "ROC requis"},
    "missing": {"en": "Missing", "fr": "Manquant"},
    "detected": {"en": "Detected", "fr": "Détecté"},
}

# Cross-document validation check names
CROSS_DOC_CHECKS: dict[str, dict[str, str]] = {
    "Invoice number": {"en": "Invoice number", "fr": "Numéro de facture"},
    "Exporter / shipper": {"en": "Exporter / shipper", "fr": "Exportateur / expéditeur"},
    "Consignee": {"en": "Consignee", "fr": "Destinataire"},
    "Gross weight": {"en": "Gross weight", "fr": "Poids brut"},
    "Net weight": {"en": "Net weight", "fr": "Poids net"},
    "Package count": {"en": "Package count", "fr": "Nombre de colis"},
    "Invoice arithmetic": {"en": "Invoice arithmetic", "fr": "Calcul de la facture"},
}

# Cross-document validation messages
CROSS_DOC_MESSAGES: dict[str, dict[str, str]] = {
    "Values match.": {"en": "Values match.", "fr": "Les valeurs concordent."},
    "Not enough documents contain this field to compare.": {
        "en": "Not enough documents contain this field to compare.",
        "fr": "Le nombre de documents contenant ce champ est insuffisant pour effectuer une comparaison."
    },
    "Not enough usable names to compare.": {
        "en": "Not enough usable names to compare.",
        "fr": "Le nombre de noms exploitables est insuffisant pour effectuer une comparaison."
    },
    "Not enough readable gross weights to compare.": {
        "en": "Not enough readable gross weights to compare.",
        "fr": "Le nombre de poids bruts lisibles est insuffisant pour effectuer une comparaison."
    },
    "Not enough readable net weights to compare.": {
        "en": "Not enough readable net weights to compare.",
        "fr": "Le nombre de poids nets lisibles est insuffisant pour effectuer une comparaison."
    },
    "Not enough package counts to compare.": {
        "en": "Not enough package counts to compare.",
        "fr": "Le nombre de quantités de colis lisibles est insuffisant pour effectuer une comparaison."
    },
    "Gross weights agree within 0.01 kg.": {
        "en": "Gross weights agree within 0.01 kg.",
        "fr": "Les poids bruts concordent avec une tolérance de 0,01 kg."
    },
    "Gross weights differ between documents.": {
        "en": "Gross weights differ between documents.",
        "fr": "Les poids bruts diffèrent d'un document à l'autre."
    },
    "Net weights agree within 0.01 kg.": {
        "en": "Net weights agree within 0.01 kg.",
        "fr": "Les poids nets concordent avec une tolérance de 0,01 kg."
    },
    "Net weights differ between documents.": {
        "en": "Net weights differ between documents.",
        "fr": "Les poids nets diffèrent d'un document à l'autre."
    },
    "Package counts agree.": {
        "en": "Package counts agree.",
        "fr": "Les nombres de colis concordent."
    },
    "Package counts differ between documents.": {
        "en": "Package counts differ between documents.",
        "fr": "Les nombres de colis diffèrent d'un document à l'autre."
    },
    "A readable subtotal (or line-item amounts) and declared total are required.": {
        "en": "A readable subtotal (or line-item amounts) and declared total are required.",
        "fr": "Un sous-total lisible (ou les montants des articles) ainsi qu'un total déclaré sont nécessaires."
    },
    "The calculated total matches the declared total.": {
        "en": "The calculated total matches the declared total.",
        "fr": "Le total calculé correspond au total déclaré."
    },
    "The calculated total does not match the declared total.": {
        "en": "The calculated total does not match the declared total.",
        "fr": "Le total calculé ne correspond pas au total déclaré."
    },
}

# OCR and extraction messages
OCR_MESSAGES: dict[str, dict[str, str]] = {
    "OCR was attempted but no readable text was recognized. The scan may be too faint, blurred or low resolution.": {
        "en": "OCR was attempted but no readable text was recognized. The scan may be too faint, blurred or low resolution.",
        "fr": "La ROC a été tentée mais aucun texte lisible n'a été reconnu. Le scan peut être trop faible, flou ou de faible résolution."
    },
    "No selectable text was found. OCR support is required for this document.": {
        "en": "No selectable text was found. OCR support is required for this document.",
        "fr": "Aucun texte sélectionnable n'a été trouvé. La prise en charge ROC est requise pour ce document."
    },
    "The PDF has no selectable text and OCR could not run: ": {
        "en": "The PDF has no selectable text and OCR could not run: ",
        "fr": "Le PDF n'a pas de texte sélectionnable et la ROC n'a pas pu s'exécuter : "
    },
}

# Validation messages
VALIDATION_MESSAGES: dict[str, dict[str, str]] = {
    "One or more required fields are missing.": {
        "en": "One or more required fields are missing.",
        "fr": "Un ou plusieurs champs obligatoires sont manquants."
    },
    "One or more fields failed format validation.": {
        "en": "One or more fields failed format validation.",
        "fr": "Un ou plusieurs champs ont échoué à la validation de format."
    },
    "Some extracted values could not be matched to their provided evidence quotations in the source text.": {
        "en": "Some extracted values could not be matched to their provided evidence quotations in the source text.",
        "fr": "Certaines valeurs extraites ne correspondent pas exactement aux citations justificatives fournies dans le texte source."
    },
    "The extracted fields object is missing or invalid.": {
        "en": "The extracted fields object is missing or invalid.",
        "fr": "Les champs extraits sont absents ou invalides."
    },
    "Value is an empty string.": {
        "en": "Value is an empty string.",
        "fr": "La valeur est vide."
    },
    "Date must be a YYYY-MM-DD string.": {
        "en": "Date must be a YYYY-MM-DD string.",
        "fr": "La date doit respecter le format AAAA-MM-JJ."
    },
    "Invalid date; expected YYYY-MM-DD.": {
        "en": "Invalid date; expected YYYY-MM-DD.",
        "fr": "Date invalide ; le format attendu est AAAA-MM-JJ."
    },
    "Expected a non-negative numeric amount.": {
        "en": "Expected a non-negative numeric amount.",
        "fr": "Un montant numérique non négatif est attendu."
    },
    "Expected a three-letter currency code.": {
        "en": "Expected a three-letter currency code.",
        "fr": "Un code devise à trois lettres est attendu."
    },
    "Weight must include a recognizable unit.": {
        "en": "Weight must include a recognizable unit.",
        "fr": "Le poids doit inclure une unité reconnaissable."
    },
    "Expected a package count or package description.": {
        "en": "Expected a package count or package description.",
        "fr": "Un nombre de colis ou une description de colis est attendu."
    },
    "Numeric package count must be a positive integer.": {
        "en": "Numeric package count must be a positive integer.",
        "fr": "Le nombre de colis numérique doit être un entier positif."
    },
    "Package description is empty.": {
        "en": "Package description is empty.",
        "fr": "La description du colis est vide."
    },
    "Expected a non-empty identifier string.": {
        "en": "Expected a non-empty identifier string.",
        "fr": "Une chaîne d'identifiant non vide est attendue."
    },
}

# Document validation warnings
VALIDATION_WARNINGS: dict[str, dict[str, str]] = {
    "Vision OCR was used on PDF page(s): {pages}. Verify extracted values against the original scan.": {
        "en": "Vision OCR was used on PDF page(s): {pages}. Verify extracted values against the original scan.",
        "fr": "La ROC vision a été utilisée sur la/les page(s) PDF : {pages}. Vérifiez les valeurs extraites par rapport au scan original."
    },
    "OCR/vision transcription requires manual review on PDF page(s): {pages}. Verify extracted information against the original scan.": {
        "en": "OCR/vision transcription requires manual review on PDF page(s): {pages}. Verify extracted information against the original scan.",
        "fr": "La transcription ROC/vision nécessite une vérification manuelle sur la/les page(s) PDF : {pages}. Vérifiez les informations extraites par rapport au scan original."
    },
    "AI extraction failed: {error}. Review the original PDF and retry extraction.": {
        "en": "AI extraction failed: {error}. Review the original PDF and retry extraction.",
        "fr": "L'extraction IA a échoué : {error}. Vérifiez le PDF original et relancez l'extraction."
    },
}

# Package-level messages
PACKAGE_MESSAGES: dict[str, dict[str, str]] = {
    "No selectable text was found in this PDF ({pages} page{pages_plural}).": {
        "en": "No selectable text was found in this PDF ({pages} page{pages_plural}).",
        "fr": "Aucun texte sélectionnable n'a été détecté dans ce PDF ({pages} page{pages_plural})."
    },
    "OCR was attempted but no readable text was recognized. The scan may be too faint, blurred or low resolution. No documents were classified or checked. Try a clearer or higher-resolution scan, or ask the exporter for a text-based PDF.": {
        "en": "OCR was attempted but no readable text was recognized. The scan may be too faint, blurred or low resolution. No documents were classified or checked. Try a clearer or higher-resolution scan, or ask the exporter for a text-based PDF.",
        "fr": "La ROC a été tentée mais aucun texte lisible n'a été reconnu. Le scan peut être trop faible, flou ou de faible résolution. Aucun document n'a pu être classifié ou contrôlé. Essayez un scan plus net ou de meilleure résolution, ou demandez un PDF électronique à l'exportateur."
    },
}

# Steps generation
STEPS_MESSAGES: dict[str, dict[str, str]] = {
    "Request the missing documents from the exporter: {docs}.": {
        "en": "Request the missing documents from the exporter: {docs}.",
        "fr": "Réclamer les documents manquants auprès de l'exportateur : {docs}."
    },
    "Check pages {pages}: the system could not identify them.": {
        "en": "Check pages {pages}: the system could not identify them.",
        "fr": "Examiner les pages {pages} : le système n'a pas pu déterminer leur nature."
    },
    "Check the flagged fields in the {doc} (pages {pages}).": {
        "en": "Check the flagged fields in the {doc} (pages {pages}).",
        "fr": "Vérifier les champs signalés pour le document « {doc} » (pages {pages})."
    },
    "Resolve the \"{check}\" mismatch between documents.": {
        "en": "Resolve the \"{check}\" mismatch between documents.",
        "fr": "Résoudre l'écart « {check} » entre les documents."
    },
    "Review \"{check}\": {msg}": {
        "en": "Review \"{check}\": {msg}",
        "fr": "Examiner le contrôle « {check} » : {msg}"
    },
}

# Report messages
REPORT_MESSAGES: dict[str, dict[str, str]] = {
    "Overall status:": {"en": "Overall status:", "fr": "Statut global :"},
    "Missing documents:": {"en": "Missing documents:", "fr": "Documents manquants :"},
    "Documents requiring review:": {"en": "Documents requiring review:", "fr": "Documents à examiner :"},
    "Cross-document mismatches:": {"en": "Cross-document mismatches:", "fr": "Discordances détectées :"},
    "Recommended next steps": {"en": "Recommended next steps", "fr": "Prochaines étapes recommandées"},
    "No action needed based on the returned data.": {
        "en": "No action needed based on the returned data.",
        "fr": "Aucune action requise d'après les données retournées."
    },
    "None": {"en": "None", "fr": "Aucun"},
}

# Legal disclaimer
LEGAL_DISCLAIMER: dict[str, str] = {
    "en": "This report is generated by an automated system for internal review. It is not digitally signed, legally certified, or proof that the documents are authentic.",
    "fr": "Ce rapport est généré par un système automatisé pour usage interne. Il n'est ni signé électroniquement, ni certifié juridiquement, et ne constitue pas une attestation légale d'authenticité.",
}

# Common values
COMMON: dict[str, dict[str, str]] = {
    "notFound": {"en": "Not found", "fr": "Non trouvé"},
    "yes": {"en": "Yes", "fr": "Oui"},
    "no": {"en": "No", "fr": "Non"},
}

# Field labels (for extracted document fields)
FIELD_LABELS: dict[str, dict[str, str]] = {
    "certificate_number": {"en": "Certificate number", "fr": "Numéro du certificat"},
    "exporter_name": {"en": "Exporter name", "fr": "Nom de l'exportateur"},
    "consignee_name": {"en": "Consignee name", "fr": "Nom du destinataire"},
    "producer_name": {"en": "Producer name", "fr": "Nom du producteur"},
    "issuer_name": {"en": "Issuer name", "fr": "Nom de l'organisme émetteur"},
    "issuing_authority": {"en": "Issuing authority", "fr": "Autorité émettrice"},
    "destination_country": {"en": "Destination country", "fr": "Pays de destination"},
    "country_of_origin": {"en": "Country of origin", "fr": "Pays d'origine"},
    "goods_description": {"en": "Goods description", "fr": "Description des marchandises"},
    "invoice_number": {"en": "Invoice number", "fr": "Numéro de facture"},
    "invoice_date": {"en": "Invoice date", "fr": "Date de facture"},
    "issue_date": {"en": "Issue date", "fr": "Date d'émission"},
    "on_board_date": {"en": "On-board date", "fr": "Date d'embarquement"},
    "inspection_date": {"en": "Inspection date", "fr": "Date d'inspection"},
    "treatment_date": {"en": "Treatment date", "fr": "Date de traitement"},
    "bill_of_lading_number": {"en": "Bill of lading number", "fr": "Numéro du connaissement"},
    "shipper_name": {"en": "Shipper name", "fr": "Nom de l'expéditeur"},
    "carrier_name": {"en": "Carrier name", "fr": "Nom du transporteur"},
    "packing_list_number": {"en": "Packing list number", "fr": "Numéro de la liste de colisage"},
    "package_count": {"en": "Package count", "fr": "Nombre de colis"},
    "package_types": {"en": "Package types", "fr": "Types de colis"},
    "total_gross_weight": {"en": "Total gross weight", "fr": "Poids brut total"},
    "total_net_weight": {"en": "Total net weight", "fr": "Poids net total"},
    "line_item_gross_weights": {"en": "Line item gross weights", "fr": "Poids brut par article"},
    "currency": {"en": "Currency", "fr": "Devise"},
    "total_amount": {"en": "Total amount", "fr": "Montant total"},
    "subtotal": {"en": "Subtotal", "fr": "Sous-total"},
    "freight_and_handling": {"en": "Freight and handling", "fr": "Fret et manutention"},
    "insurance_fee": {"en": "Insurance fee", "fr": "Frais d'assurance"},
    "tax_amount": {"en": "Tax amount", "fr": "Montant des taxes"},
    "line_item_amounts": {"en": "Line item amounts", "fr": "Montants des articles"},
    "calculated_total": {"en": "Calculated total", "fr": "Total calculé"},
    "declared_total": {"en": "Declared total", "fr": "Total déclaré"},
    "fumigant": {"en": "Fumigant", "fr": "Produit fumigant"},
    "conformity_status": {"en": "Conformity status", "fr": "Statut de conformité"},
    "booking_number": {"en": "Booking number", "fr": "Numéro de réservation"},
    "goods": {"en": "Goods", "fr": "Marchandises"},
    "address": {"en": "Address", "fr": "Adresse"},
    "port_of_loading": {"en": "Port of loading", "fr": "Port de chargement"},
    "port_of_discharge": {"en": "Port of discharge", "fr": "Port de déchargement"},
    "vessel_name": {"en": "Vessel name", "fr": "Nom du navire"},
    "seal_number": {"en": "Seal number", "fr": "Numéro du scellé"},
    "marks_and_numbers": {"en": "Marks and numbers", "fr": "Marques et numéros"},
}


def _(key: str, category: str = "general", **kwargs) -> str:
    """Translate a message key to the current language.

    Categories: general, doc_types, statuses, cross_doc_checks, cross_doc_messages,
    ocr_messages, validation_messages, validation_warnings, package_messages,
    steps_messages, report_messages, legal_disclaimer, common, field_labels
    """
    lang = get_language()

    # Map category to the appropriate dictionary
    catalogs = {
        "doc_types": DOC_TYPES,
        "statuses": STATUSES,
        "cross_doc_checks": CROSS_DOC_CHECKS,
        "cross_doc_messages": CROSS_DOC_MESSAGES,
        "ocr_messages": OCR_MESSAGES,
        "validation_messages": VALIDATION_MESSAGES,
        "validation_warnings": VALIDATION_WARNINGS,
        "package_messages": PACKAGE_MESSAGES,
        "steps_messages": STEPS_MESSAGES,
        "report_messages": REPORT_MESSAGES,
        "common": COMMON,
        "field_labels": FIELD_LABELS,
    }

    catalog = catalogs.get(category, {})
    if key in catalog:
        return catalog[key].get(lang, catalog[key].get("en", key))

    # Check legal disclaimer separately
    if category == "legal_disclaimer":
        return LEGAL_DISCLAIMER.get(lang, LEGAL_DISCLAIMER["en"])

    # Fallback: return key with basic formatting
    return key.format(**kwargs) if kwargs else key


def doc_label(doc_type: str) -> str:
    """Get localized document type label."""
    return _(doc_type, "doc_types")


def status_label(status: str) -> str:
    """Get localized status label."""
    return _(status, "statuses")


def field_label(field: str) -> str:
    """Get localized field label."""
    return _(field, "field_labels")


def cross_doc_check_label(check: str) -> str:
    """Get localized cross-doc check name."""
    return _(check, "cross_doc_checks")


def cross_doc_message(message: str) -> str:
    """Get localized cross-doc message."""
    return _(message, "cross_doc_messages")


def validation_message(message: str) -> str:
    """Get localized validation message."""
    return _(message, "validation_messages")


def validation_warning(template: str, **kwargs) -> str:
    """Get localized validation warning with formatting."""
    translated = _(template, "validation_warnings")
    return translated.format(**kwargs)


def package_message(template: str, **kwargs) -> str:
    """Get localized package message with formatting."""
    translated = _(template, "package_messages")
    return translated.format(**kwargs)


def step_message(template: str, **kwargs) -> str:
    """Get localized step message with formatting."""
    translated = _(template, "steps_messages")
    return translated.format(**kwargs)


def report_message(template: str) -> str:
    """Get localized report message."""
    return _(template, "report_messages")


def legal_disclaimer() -> str:
    """Get localized legal disclaimer."""
    return _("disclaimer", "legal_disclaimer")


def common_value(key: str) -> str:
    """Get localized common value (yes/no/notFound)."""
    return _(key, "common")


def t(key: str, category: str = "general", **kwargs) -> str:
    """General translation function with formatting support.

    ``category`` selects the translation catalog (e.g. "cross_doc_messages").
    """
    lang = get_language()
    catalogs = {
        "doc_types": DOC_TYPES,
        "statuses": STATUSES,
        "cross_doc_checks": CROSS_DOC_CHECKS,
        "cross_doc_messages": CROSS_DOC_MESSAGES,
        "ocr_messages": OCR_MESSAGES,
        "validation_messages": VALIDATION_MESSAGES,
        "validation_warnings": VALIDATION_WARNINGS,
        "package_messages": PACKAGE_MESSAGES,
        "steps_messages": STEPS_MESSAGES,
        "report_messages": REPORT_MESSAGES,
        "common": COMMON,
        "field_labels": FIELD_LABELS,
    }
    if category in catalogs and key in catalogs[category]:
        return catalogs[category][key].get(lang, catalogs[category][key].get("en", key)).format(**kwargs)
    # Fallback: search all catalogs
    all_catalogs = {
        **DOC_TYPES, **STATUSES, **CROSS_DOC_CHECKS, **CROSS_DOC_MESSAGES,
        **OCR_MESSAGES, **VALIDATION_MESSAGES, **VALIDATION_WARNINGS,
        **PACKAGE_MESSAGES, **STEPS_MESSAGES, **REPORT_MESSAGES,
        **COMMON, **FIELD_LABELS,
    }
    if key in all_catalogs:
        return all_catalogs[key].get(lang, all_catalogs[key].get("en", key)).format(**kwargs)
    # Fallback to LEGAL_DISCLAIMER
    if key == "legal_disclaimer":
        return LEGAL_DISCLAIMER.get(lang, LEGAL_DISCLAIMER["en"])
    return key.format(**kwargs) if kwargs else key