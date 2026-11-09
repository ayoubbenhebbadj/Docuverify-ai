import type { Language } from './translations'

const FIELD_LABELS: Record<string, string> = {
  certificate_number: 'Numéro du certificat',
  exporter_name: 'Nom de l’exportateur',
  consignee_name: 'Nom du destinataire',
  producer_name: 'Nom du producteur',
  issuer_name: 'Nom de l’organisme émetteur',
  issuing_authority: 'Autorité émettrice',
  destination_country: 'Pays de destination',
  country_of_origin: 'Pays d’origine',
  goods_description: 'Description des marchandises',
  invoice_number: 'Numéro de facture',
  invoice_date: 'Date de facture',
  issue_date: 'Date d’émission',
  on_board_date: 'Date d’embarquement',
  inspection_date: 'Date d’inspection',
  treatment_date: 'Date de traitement',
  bill_of_lading_number: 'Numéro du connaissement',
  shipper_name: 'Nom de l’expéditeur',
  carrier_name: 'Nom du transporteur',
  packing_list_number: 'Numéro de la liste de colisage',
  package_count: 'Nombre de colis',
  package_types: 'Types de colis',
  total_gross_weight: 'Poids brut total',
  total_net_weight: 'Poids net total',
  line_item_gross_weights: 'Poids brut par article',
  currency: 'Devise',
  total_amount: 'Montant total',
  subtotal: 'Sous-total',
  freight_and_handling: 'Fret et manutention',
  insurance_fee: 'Frais d’assurance',
  tax_amount: 'Montant des taxes',
  line_item_amounts: 'Montants des articles',
  calculated_total: 'Total calculé',
  declared_total: 'Total déclaré',
  fumigant: 'Produit fumigant',
  conformity_status: 'Statut de conformité',
  booking_number: 'Numéro de réservation',
  goods: 'Marchandises',
  address: 'Adresse',
  port_of_loading: 'Port de chargement',
  port_of_discharge: 'Port de déchargement',
  vessel_name: 'Nom du navire',
  seal_number: 'Numéro du scellé',
  marks_and_numbers: 'Marques et numéros',
}

const TEXT: Record<string, string> = {
  'Invoice number': 'Numéro de facture',
  'Exporter / shipper': 'Exportateur / expéditeur',
  'Consignee': 'Destinataire',
  'Gross weight': 'Poids brut',
  'Net weight': 'Poids net',
  'Package count': 'Nombre de colis',
  'Invoice arithmetic': 'Calcul de la facture',
  'Values match.': 'Les valeurs concordent.',
  'Not enough documents contain this field to compare.': 'Le nombre de documents contenant ce champ est insuffisant pour effectuer une comparaison.',
  'Not enough usable names to compare.': 'Le nombre de noms exploitables est insuffisant pour effectuer une comparaison.',
  'Not enough readable gross weights to compare.': 'Le nombre de poids bruts lisibles est insuffisant pour effectuer une comparaison.',
  'Not enough readable net weights to compare.': 'Le nombre de poids nets lisibles est insuffisant pour effectuer une comparaison.',
  'Not enough package counts to compare.': 'Le nombre de quantités de colis lisibles est insuffisant pour effectuer une comparaison.',
  'Gross weights agree within 0.01 kg.': 'Les poids bruts concordent avec une tolérance de 0,01 kg.',
  'Gross weights differ between documents.': 'Les poids bruts diffèrent d’un document à l’autre.',
  'Net weights agree within 0.01 kg.': 'Les poids nets concordent avec une tolérance de 0,01 kg.',
  'Net weights differ between documents.': 'Les poids nets diffèrent d’un document à l’autre.',
  'Package counts agree.': 'Les nombres de colis concordent.',
  'Package counts differ between documents.': 'Les nombres de colis diffèrent d’un document à l’autre.',
  'A readable subtotal (or line-item amounts) and declared total are required.': 'Un sous-total lisible (ou les montants des articles) ainsi qu’un total déclaré sont nécessaires.',
  'The calculated total matches the declared total.': 'Le total calculé correspond au total déclaré.',
  'The calculated total does not match the declared total.': 'Le total calculé ne correspond pas au total déclaré.',
  'Some extracted values could not be matched to their provided evidence quotations in the source text.': 'Certaines valeurs extraites ne correspondent pas exactement aux citations justificatives fournies dans le texte source.',
  'The extracted fields object is missing or invalid.': 'Les champs extraits sont absents ou invalides.',
  'Value is an empty string.': 'La valeur est vide.',
  'Date must be a YYYY-MM-DD string.': 'La date doit respecter le format AAAA-MM-JJ.',
  'Invalid date; expected YYYY-MM-DD.': 'Date invalide ; le format attendu est AAAA-MM-JJ.',
  'Unsupported document type:': 'Type de document non pris en charge :',
  'The document could not be classified.': 'Le document n’a pas pu être identifié.',
  'No text could be extracted from this document.': 'Aucun texte n’a pu être extrait de ce document.',
}

const DOC_TYPES: Record<string, string> = {
  'Commercial invoice': 'Facture commerciale',
  'Packing list': 'Liste de colisage',
  'Bill of lading': 'Connaissement',
  'Certificate of origin': 'Certificat d’origine',
  'Certificate of quality': 'Certificat de qualité',
  'Certificate of conformity': 'Certificat de conformité',
  'Phytosanitary certificate': 'Certificat phytosanitaire',
  'Fumigation certificate': 'Certificat de fumigation',
}

export function fieldLabel(field: string, language: Language): string {
  if (language !== 'fr') return field.replace(/_/g, ' ').replace(/^./, (c) => c.toUpperCase())
  if (FIELD_LABELS[field]) return FIELD_LABELS[field]
  return field
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (letter) => letter.toUpperCase())
}

export function translateResultText(value: string, language: Language): string {
  if (language !== 'fr' || !value) return value
  const exact = TEXT[value]
  if (exact) return exact

  // Translate document names embedded in backend-generated comparison details.
  let translated = value
  for (const [english, french] of Object.entries(DOC_TYPES)) {
    translated = translated.replace(new RegExp(english.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'gi'), french)
  }

  // Backend warnings that append a dynamic document type.
  if (translated.startsWith('Unsupported document type:')) {
    return translated.replace('Unsupported document type:', 'Type de document non pris en charge :')
  }

  // Common backend-generated dynamic messages.
  translated = translated
    .replace(/^Not enough usable names to compare\.$/i, 'Le nombre de noms exploitables est insuffisant pour effectuer une comparaison.')
    .replace(/^Not enough documents contain this field to compare\.$/i, TEXT['Not enough documents contain this field to compare.'])
    .replace(/^Not enough readable gross weights to compare\.$/i, TEXT['Not enough readable gross weights to compare.'])
    .replace(/^Not enough readable net weights to compare\.$/i, TEXT['Not enough readable net weights to compare.'])
    .replace(/^Not enough package counts to compare\.$/i, TEXT['Not enough package counts to compare.'])
    .replace(/^Documents disagree:/i, 'Les documents présentent des divergences :')
    .replace(/^Differs from the majority of documents:/i, 'Diffère de la majorité des documents :')
    .replace(/Values match\./gi, 'Les valeurs concordent.')
    .replace(/address, not a company name - check the extraction\./gi, 'une adresse a été extraite au lieu d’une raison sociale : vérifiez l’extraction.')
    .replace(/gross weight was not found in the document and was excluded from comparison\./gi, 'le poids brut est absent du document et a été exclu de la comparaison.')
    .replace(/Gross weight/gi, 'poids brut')
    .replace(/Net weight/gi, 'poids net')
    .replace(/Invoice number/gi, 'numéro de facture')
    .replace(/Exporter \/ shipper/gi, 'exportateur / expéditeur')
    .replace(/Consignee/gi, 'destinataire')
    .replace(/Package count/gi, 'nombre de colis')
  return translated
}
