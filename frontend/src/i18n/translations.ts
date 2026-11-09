export type Language = 'en' | 'fr'

export interface TranslationDictionary {
  nav: {
    overview: string
    overviewDesc: string
    newAnalysis: string
    newAnalysisDesc: string
    results: string
    resultsDesc: string
    brand: string
    closeMenu: string
    openMenu: string
    switchLanguage: string
  }
  overview: {
    title: string
    subtitle: string
    newAnalysisBtn: string
    processHeader: string
    steps: string[]
    needsReviewNote: string
    backendConnection: string
    checking: string
    connectedTo: string
    cannotReach: string
    latestAnalysis: string
    noAnalysisYet: string
    docsSummary: (found: number, missing: number) => string
    openResults: string
  }
  newAnalysis: {
    title: string
    subtitle: string
    tip: string
    dropTitle: string
    dropSub: string
    pdfOnly: string
    replace: string
    remove: string
    analyzeBtn: string
    analyzingBtn: string
    retryBtn: string
    selectPdfHint: string
    selectedFiles: (count: number) => string
    addMore: string
    clearAll: string
    validation: {
      notPdf: string
      empty: string
      tooLarge: (size: string) => string
      packageTooLarge: (size: string) => string
    }
  }
  processing: {
    mainTitle: string
    subTitle: string
    elapsed: string
    currentPhase: string
    simulatedPace: string
    stages: {
      reading: { title: string; desc: string }
      ocr: { title: string; desc: string }
      classification: { title: string; desc: string }
      extraction: { title: string; desc: string }
      validation: { title: string; desc: string }
      results: { title: string; desc: string }
    }
    toggles: {
      radar: string
      radarDesc: string
      liveLogs: string
      liveLogsDesc: string
      tips: string
      tipsDesc: string
    }
    logs: {
      init: string
      reading: string
      ocrDetect: string
      classifying: string
      extractingFields: string
      crossValidating: string
      finalizing: string
    }
    tipsList: Array<{ title: string; text: string }>
    nextTip: string
    prevTip: string
    activeMotionBadge: string
    fastScanLabel: string
  }
  results: {
    title: string
    subtitle: (count: number) => string
    printReport: string
    analyzeAnother: string
    noResultsTitle: string
    noResultsText: string
    startNewLink: string
    ocrNeedsTitle: (pages: number) => string
    ocrNeedsBody: (msg: string) => string
    overallStatus: string
    bannerPassed: string
    bannerReview: string
    bannerUnknown: (status: string) => string
    ocrUsedHeader: string
    ocrPagesInfo: (pages: string, conf?: number | null) => string
    ocrCheckScans: (pages: string) => string
    ocrConfidenceGood: string
    ocrProblems: string
    stats: {
      pagesProcessed: string
      docsDetected: string
      requiredMissing: string
      ofRequired: (total: number) => string
      crossPassed: string
      ofTotal: (total: number) => string
      mismatchesReview: string
      crossDoc: string
    }
    requiredDocs: {
      title: string
      notFound: string
      viewFields: string
      unidentifiedPages: string
    }
    extractedDocs: {
      title: string
      empty: string
      pages: string
      classifiedWith: (conf: number) => string
      missingFields: string
      invalidFields: string
      unsupportedEvidence: string
      unsupportedNote: string
      warnings: string
    }
    crossDoc: {
      title: string
      empty: string
      colCheck: string
      colStatus: string
      colValues: string
      colMessage: string
      none: string
    }
    report: {
      title: string
      overall: string
      missing: string
      requiringReview: string
      mismatches: string
      nextSteps: string
      noAction: string
      legalDisclaimer: string
      none: string
    }
    stepsGeneration: {
      missingDocs: (docs: string) => string
      unclassified: (pages: string) => string
      reviewDoc: (doc: string, pages: string) => string
      mismatchCheck: (check: string) => string
      reviewCheck: (check: string, msg: string) => string
    }
  }
  docTypes: Record<string, string>
  statuses: Record<string, string>
  common: {
    notFound: string
    yes: string
    no: string
  }
}

export const translations: Record<Language, TranslationDictionary> = {
  en: {
    nav: {
      overview: 'Overview',
      overviewDesc: 'How verification works and backend status.',
      newAnalysis: 'New Analysis',
      newAnalysisDesc: 'Add shipment PDFs as they arrive and scan them together.',
      results: 'Analysis Results',
      resultsDesc: 'Review the report for the most recent analysis.',
      brand: 'DocuVerify AI',
      closeMenu: 'Close menu',
      openMenu: 'Open menu',
      switchLanguage: 'Switch language',
    },
    overview: {
      title: 'Shipment document verification',
      subtitle: "Add the exporter's PDFs as they arrive, scan the selected files together, and review what is found, missing, or inconsistent.",
      newAnalysisBtn: 'New analysis',
      processHeader: 'What happens to your PDF',
      steps: [
        'Extracts the text of every PDF page',
        'Classifies each page by document type',
        'Groups pages that belong to the same document',
        'Extracts structured fields from each document',
        'Checks required fields and whether quoted evidence appears in the source text',
        'Cross-checks values between documents',
        'Reports missing documents, unsupported evidence, warnings and mismatches',
      ],
      needsReviewNote: '“Needs review” means the package needs a person’s attention. It does not mean fraud has been found.',
      backendConnection: 'Backend connection',
      checking: 'Checking…',
      connectedTo: 'Connected to',
      cannotReach: 'Cannot reach',
      latestAnalysis: 'Latest analysis',
      noAnalysisYet: 'No analysis yet in this session.',
      docsSummary: (found, missing) => `${found} documents found, ${missing} missing.`,
      openResults: 'Open results',
    },
    newAnalysis: {
      title: 'New analysis',
      subtitle: 'Add shipment files as they arrive, then analyze the files currently selected.',
      tip: 'Upload PDF, DOCX, DOC, JPG, JPEG or PNG files. You can add more files after a scan and analyze the complete selection again. Maximum 10 MB per file and 30 MB total.',
      dropTitle: 'Choose files',
      dropSub: 'or drag them here',
      pdfOnly: 'PDF, DOCX, DOC, JPG, JPEG and PNG · multiple selection supported',
      replace: 'Replace',
      remove: 'Remove file',
      analyzeBtn: 'Scan documents',
      analyzingBtn: 'Scanning…',
      retryBtn: 'Retry scan',
      selectPdfHint: 'Select at least one supported file to enable analysis.',
      selectedFiles: (count) => `${count} file${count === 1 ? '' : 's'} selected`,
      addMore: 'Add more files',
      clearAll: 'Clear all',
      validation: {
        notPdf: 'Unsupported file format. Choose PDF, DOCX, DOC, JPG, JPEG or PNG.',
        empty: 'This file is empty.',
        tooLarge: (size) => `This file is ${size}. The per-file limit is 10 MB.`,
        packageTooLarge: (size) => `The selected files total ${size}. The package limit is 30 MB.`,
      },
    },
    processing: {
      mainTitle: 'Analyzing your shipment package',
      subTitle: 'Please keep this window open while AI extracts, classifies, and verifies documents.',
      elapsed: 'Elapsed time',
      currentPhase: 'Current step',
      simulatedPace: 'Pipeline active',
      stages: {
        reading: {
          title: 'Reading & Parsing PDF',
          desc: 'Extracting digital vector text and isolating individual shipment pages...',
        },
        ocr: {
          title: 'Extracting Text (OCR Engine)',
          desc: 'Applying vision contrast filters and optical recognition to scanned pages...',
        },
        classification: {
          title: 'Classifying Document Types',
          desc: 'Categorizing pages (Invoice, BOL, Packing List, Certificates)...',
        },
        extraction: {
          title: 'Extracting Fields & Evidence',
          desc: 'Harvesting numbers, dates, parties, weights, and verbatim evidence quotes...',
        },
        validation: {
          title: 'Cross-Document Integrity Check',
          desc: 'Comparing values across documents to catch discrepancies and seal mismatches...',
        },
        results: {
          title: 'Compiling Verification Results',
          desc: 'Building final compliance report and risk assessment...',
        },
      },
      toggles: {
        radar: 'Radar Scanner View',
        radarDesc: 'Animated page inspection motion',
        liveLogs: 'Live Diagnostic Logs',
        liveLogsDesc: 'Real-time pipeline milestone telemetry',
        tips: 'Customs & Audit Tips',
        tipsDesc: 'Compliance insights while you wait',
      },
      logs: {
        init: 'Package received into memory buffer. Initializing verification pipeline...',
        reading: 'Analyzing page headers and layout boundaries...',
        ocrDetect: 'OCR preprocessing applied to low-density pages. Text tokens recognized.',
        classifying: 'Multi-document classifier identified key shipping instruments.',
        extractingFields: 'Extracting structured schemas and anchoring verbatim proof quotations.',
        crossValidating: 'Evaluating consistency between commercial invoice, packing list, and bill of lading...',
        finalizing: 'Assembling cross-document discrepancy table and audit recommendations.',
      },
      tipsList: [
        {
          title: 'Gross vs. Net Weight Rule',
          text: 'The Gross Weight on the Bill of Lading must strictly match or exceed the Total Gross Weight on the Packing List.',
        },
        {
          title: 'Consignee Name Consistency',
          text: 'Discrepancies in company suffixes (e.g., Ltd. vs Inc.) frequently trigger customs clearance holds at ports.',
        },
        {
          title: 'Origin Certificate Issuance',
          text: 'Certificates of origin must bear unambiguous chamber stamps matching the exporter country declaration.',
        },
        {
          title: 'Invoice Line Item Arithmetic',
          text: 'Our AI checks individual item lines against stated subtotal, freight additions, and currency ISO codes.',
        },
      ],
      nextTip: 'Next tip',
      prevTip: 'Previous',
      activeMotionBadge: 'Interactive processing mode',
      fastScanLabel: 'Scanning page stream',
    },
    results: {
      title: 'Analysis results',
      subtitle: (count) => `${count} pages analyzed`,
      printReport: 'Print report',
      analyzeAnother: 'Analyze another PDF',
      noResultsTitle: 'No results yet',
      noResultsText: 'Upload one or more shipment PDFs to see the analysis report here.',
      startNewLink: 'Start a new analysis',
      ocrNeedsTitle: (pages) => `No selectable text was found in this PDF (${pages} page${pages === 1 ? '' : 's'}).`,
      ocrNeedsBody: (msg) => `${msg} No documents were classified or checked. Try a clearer or higher-resolution scan, or ask the exporter for a text-based PDF.`,
      overallStatus: 'Overall status',
      bannerPassed: 'All eight documents were found and no issues were reported.',
      bannerReview: 'This package needs review. That means a person should look at the items below. It does not mean fraud has been found.',
      bannerUnknown: (status) => `The backend reported an unrecognized status (“${status}”). Treat this package as needing review.`,
      ocrUsedHeader: 'Scanned pages were read with OCR',
      ocrPagesInfo: (pages, conf) => `Pages ${pages}${typeof conf === 'number' ? ` · average confidence ${Math.round(conf)}%` : ''}.`,
      ocrCheckScans: (pages) => `Check these against the original scan: ${pages}.`,
      ocrConfidenceGood: 'OCR confidence was good on every page.',
      ocrProblems: 'OCR problems',
      stats: {
        pagesProcessed: 'Pages processed',
        docsDetected: 'Documents detected',
        requiredMissing: 'Required missing',
        ofRequired: (total) => `of ${total} required`,
        crossPassed: 'Cross-checks passed',
        ofTotal: (total) => `of ${total}`,
        mismatchesReview: 'Mismatches / review',
        crossDoc: 'cross-document',
      },
      requiredDocs: {
        title: 'Required documents',
        notFound: 'Not found in this PDF',
        viewFields: 'View fields',
        unidentifiedPages: 'Unidentified pages',
      },
      extractedDocs: {
        title: 'Extracted documents',
        empty: 'No documents were detected.',
        pages: 'Pages',
        classifiedWith: (conf) => `Classified with ${Math.round(conf * 100)}% confidence`,
        missingFields: 'Missing required fields',
        invalidFields: 'Invalid fields',
        unsupportedEvidence: 'Unsupported evidence',
        unsupportedNote: 'The AI’s quoted proof for these values was not found in the PDF text. This is a flag to check them, not proof they are wrong.',
        warnings: 'Warnings',
      },
      crossDoc: {
        title: 'Cross-document validation',
        empty: 'The backend returned no cross-document checks.',
        colCheck: 'Check',
        colStatus: 'Status',
        colValues: 'Values compared',
        colMessage: 'Message',
        none: 'None',
      },
      report: {
        title: 'Package report',
        overall: 'Overall status:',
        missing: 'Missing documents:',
        requiringReview: 'Documents requiring review:',
        mismatches: 'Cross-document mismatches:',
        nextSteps: 'Recommended next steps',
        noAction: 'No action needed based on the returned data.',
        legalDisclaimer: 'This report is generated by an automated system for internal review. It is not digitally signed, legally certified, or proof that the documents are authentic.',
        none: 'None',
      },
      stepsGeneration: {
        missingDocs: (docs) => `Request the missing documents from the exporter: ${docs}.`,
        unclassified: (pages) => `Check pages ${pages}: the system could not identify them.`,
        reviewDoc: (doc, pages) => `Check the flagged fields in the ${doc.toLowerCase()} (pages ${pages}).`,
        mismatchCheck: (check) => `Resolve the “${check}” mismatch between documents.`,
        reviewCheck: (check, msg) => `Review “${check}”: ${msg}`,
      },
    },
    docTypes: {
      commercial_invoice: 'Commercial invoice',
      packing_list: 'Packing list',
      bill_of_lading: 'Bill of lading',
      certificate_of_origin: 'Certificate of origin',
      certificate_of_quality: 'Certificate of quality',
      certificate_of_conformity: 'Certificate of conformity',
      phytosanitary_certificate: 'Phytosanitary certificate',
      fumigation_certificate: 'Fumigation certificate',
      unknown: 'Unrecognized pages',
    },
    statuses: {
      passed: 'Passed',
      complete: 'Complete',
      needs_review: 'Needs review',
      mismatch: 'Mismatch',
      needs_ocr: 'Needs OCR',
      missing: 'Missing',
      detected: 'Detected',
    },
    common: {
      notFound: 'Not found',
      yes: 'Yes',
      no: 'No',
    },
  },
  fr: {
    nav: {
      overview: 'Aperçu',
      overviewDesc: 'Fonctionnement de la vérification et état du serveur.',
      newAnalysis: 'Nouvelle analyse',
      newAnalysisDesc: 'Ajoutez les PDF au fur et à mesure de leur réception et analysez-les ensemble.',
      results: 'Résultats d’analyse',
      resultsDesc: 'Consultez le rapport complet de la dernière analyse.',
      brand: 'DocuVerify AI',
      closeMenu: 'Fermer le menu',
      openMenu: 'Ouvrir le menu',
      switchLanguage: 'Changer de langue',
    },
    overview: {
      title: 'Vérification des documents d’expédition',
      subtitle: 'Ajoutez les PDF de l’exportateur au fur et à mesure de leur réception, analysez-les ensemble et consultez les documents manquants ou incohérents.',
      newAnalysisBtn: 'Nouvelle analyse',
      processHeader: 'Ce qui se passe avec votre PDF',
      steps: [
        'Extrait le texte de chaque page du PDF',
        'Classifie chaque page selon son type de document',
        'Regroupe les pages appartenant au même document',
        'Extrait les données structurées de chaque document',
        'Vérifie les champs obligatoires et la conformité des preuves citées dans le texte',
        'Effectue la validation croisée des valeurs entre les documents',
        'Génère le rapport des documents manquants, preuves non étayées, alertes et discordances',
      ],
      needsReviewNote: '« À vérifier » signifie que le dossier requiert une attention humaine. Cela n’indique pas nécessairement qu’une fraude a été détectée.',
      backendConnection: 'Connexion au serveur',
      checking: 'Vérification…',
      connectedTo: 'Connecté à',
      cannotReach: 'Impossible de joindre',
      latestAnalysis: 'Dernière analyse',
      noAnalysisYet: 'Aucune analyse effectuée dans cette session.',
      docsSummary: (found, missing) => `${found} document(s) détecté(s), ${missing} manquant(s).`,
      openResults: 'Ouvrir les résultats',
    },
    newAnalysis: {
      title: 'Nouvelle analyse',
      subtitle: 'Ajoutez les fichiers d’expédition au fur et à mesure de leur réception, puis analysez tous les fichiers sélectionnés.',
      tip: 'Formats acceptés : PDF, DOCX, DOC, JPG, JPEG et PNG. Vous pouvez ajouter des fichiers après une analyse, puis relancer l’analyse de l’ensemble. Limite : 10 Mo par fichier et 30 Mo au total.',
      dropTitle: 'Choisir des fichiers',
      dropSub: 'ou glissez-les ici',
      pdfOnly: 'PDF, DOCX, DOC, JPG, JPEG et PNG · sélection multiple',
      replace: 'Remplacer',
      remove: 'Supprimer le fichier',
      analyzeBtn: 'Analyser les documents',
      analyzingBtn: 'Analyse en cours…',
      retryBtn: 'Réessayer l’analyse',
      selectPdfHint: 'Sélectionnez au moins un fichier accepté pour lancer l’analyse.',
      selectedFiles: (count) => `${count} fichier(s) sélectionné(s)`,
      addMore: 'Ajouter d’autres fichiers',
      clearAll: 'Tout supprimer',
      validation: {
        notPdf: 'Format non pris en charge. Choisissez un fichier PDF, DOCX, DOC, JPG, JPEG ou PNG.',
        empty: 'Ce fichier est vide.',
        tooLarge: (size) => `Ce fichier fait ${size}. La limite par fichier est de 10 Mo.`,
        packageTooLarge: (size) => `La taille totale est de ${size}. La limite du dossier est de 30 Mo.`,
      },
    },
    processing: {
      mainTitle: 'Analyse de votre dossier d’expédition',
      subTitle: 'Veuillez conserver cette page ouverte pendant que l’IA extrait, classifie et certifie vos documents.',
      elapsed: 'Temps écoulé',
      currentPhase: 'Étape en cours',
      simulatedPace: 'Pipeline actif',
      stages: {
        reading: {
          title: 'Lecture & Découpage du PDF',
          desc: 'Extraction des couches de texte vectoriel et segmentation des pages du dossier...',
        },
        ocr: {
          title: 'Extraction du texte (Moteur ROC)',
          desc: 'Optimisation du contraste et reconnaissance optique sur les pages numérisées...',
        },
        classification: {
          title: 'Classification des types de documents',
          desc: 'Identification des instruments (Facture, Connaissement, Liste de colisage, Certificats)...',
        },
        extraction: {
          title: 'Extraction des données & Preuves textuelles',
          desc: 'Capture des montants, dates, parties prenantes, poids et citations textuelles exactes...',
        },
        validation: {
          title: 'Validation croisée de cohérence',
          desc: 'Comparaison des valeurs entre documents pour détecter les incohérences et scellés...',
        },
        results: {
          title: 'Génération du rapport d’analyse',
          desc: 'Compilation finale du rapport d’audit et des indicateurs de conformité...',
        },
      },
      toggles: {
        radar: 'Vue Scanner Radar',
        radarDesc: 'Animation d’inspection visuelle',
        liveLogs: 'Journal d’analyse en direct',
        liveLogsDesc: 'Télémétrie des jalons en temps réel',
        tips: 'Conseils & Audit Douanier',
        tipsDesc: 'Recommandations pratiques pendant l’attente',
      },
      logs: {
        init: 'Document reçu en mémoire vive. Démarrage de la séquence d’inspection...',
        reading: 'Analyse des en-têtes et des délimitations de pages...',
        ocrDetect: 'Prétraitement ROC appliqué aux pages scannées. Reconnaissance des caractères réussie.',
        classifying: 'Le classificateur IA a reconnu les pièces maîtresses du dossier d’expédition.',
        extractingFields: 'Extraction des schémas de données et ancrage des citations littérales justificatives.',
        crossValidating: 'Contrôle croisé de cohérence entre facture, liste de colisage et connaissement...',
        finalizing: 'Génération de la matrice des écarts et des recommandations douanières.',
      },
      tipsList: [
        {
          title: 'Règle Poids Brut vs Poids Net',
          text: 'Le poids brut indiqué sur le connaissement maritime (B/L) doit être supérieur ou rigoureusement égal à la somme inscrite sur la liste de colisage.',
        },
        {
          title: 'Orthographe du Destinataire (Consignee)',
          text: 'Une divergence même minime dans la raison sociale (ex. SARL vs EURL) entraîne fréquemment un blocage du dédouanement au port d’arrivée.',
        },
        {
          title: 'Délivrance du Certificat d’Origine',
          text: 'Le certificat d’origine doit comporter le visa officiel de la chambre de commerce du pays exportateur déclaré.',
        },
        {
          title: 'Arithmétique des Lignes de Facture',
          text: 'Notre IA vérifie la somme des lignes d’articles vis-à-vis du sous-total, du fret et du code devise ISO déclaré.',
        },
      ],
      nextTip: 'Conseil suivant',
      prevTip: 'Précédent',
      activeMotionBadge: 'Mode d’analyse interactif',
      fastScanLabel: 'Balayage du flux de pages',
    },
    results: {
      title: 'Résultats de l’analyse',
      subtitle: (count) => `${count} page${count > 1 ? 's' : ''} analysée${count > 1 ? 's' : ''}`,
      printReport: 'Imprimer le rapport',
      analyzeAnother: 'Analyser un autre PDF',
      noResultsTitle: 'Aucun résultat pour le moment',
      noResultsText: 'Téléversez un PDF d’expédition groupé pour afficher son rapport ici.',
      startNewLink: 'Démarrer une nouvelle analyse',
      ocrNeedsTitle: (pages) => `Aucun texte sélectionnable n’a été détecté dans ce PDF (${pages} page${pages === 1 ? '' : 's'}).`,
      ocrNeedsBody: (msg) => `${msg} Aucun document n’a pu être classifié ou contrôlé. Essayez un scan de meilleure résolution ou demandez un PDF électronique natif à l’exportateur.`,
      overallStatus: 'Statut global',
      bannerPassed: 'Les huit documents requis ont été détectés et aucune anomalie n’a été signalée.',
      bannerReview: 'Ce dossier requiert une vérification humaine. Un opérateur doit examiner les points signalés ci-dessous. Cela n’indique pas nécessairement une fraude.',
      bannerUnknown: (status) => `Le serveur a renvoyé un statut inconnu (« ${status} »). Traitez ce dossier comme nécessitant une vérification.`,
      ocrUsedHeader: 'Des pages numérisées ont été lues par ROC',
      ocrPagesInfo: (pages, conf) => `Pages ${pages}${typeof conf === 'number' ? ` · indice moyen de confiance ${Math.round(conf)}%` : ''}.`,
      ocrCheckScans: (pages) => `Vérifiez ces pages par rapport au document scanné original : ${pages}.`,
      ocrConfidenceGood: 'Le niveau de confiance du ROC est satisfaisant sur chaque page.',
      ocrProblems: 'Incidents ROC',
      stats: {
        pagesProcessed: 'Pages traitées',
        docsDetected: 'Documents détectés',
        requiredMissing: 'Obligatoires manquants',
        ofRequired: (total) => `sur ${total} requis`,
        crossPassed: 'Contrôles validés',
        ofTotal: (total) => `sur ${total}`,
        mismatchesReview: 'Discordances / À réviser',
        crossDoc: 'inter-documents',
      },
      requiredDocs: {
        title: 'Documents obligatoires',
        notFound: 'Non trouvé dans ce PDF',
        viewFields: 'Voir les champs',
        unidentifiedPages: 'Pages non identifiées',
      },
      extractedDocs: {
        title: 'Documents extraits',
        empty: 'Aucun document n’a été détecté.',
        pages: 'Pages',
        classifiedWith: (conf) => `Classifié avec ${Math.round(conf * 100)}% de confiance`,
        missingFields: 'Champs obligatoires manquants',
        invalidFields: 'Champs non valides',
        unsupportedEvidence: 'Preuves non étayées',
        unsupportedNote: 'La preuve textuelle citée par l’IA pour ces valeurs n’a pas été retrouvée mot pour mot dans le texte du PDF. Il s’agit d’une invitation à vérifier, non d’une certitude d’erreur.',
        warnings: 'Avertissements',
      },
      crossDoc: {
        title: 'Validation croisée entre documents',
        empty: 'Le système n’a renvoyé aucun contrôle croisé pour ce dossier.',
        colCheck: 'Contrôle',
        colStatus: 'Statut',
        colValues: 'Valeurs comparées',
        colMessage: 'Message',
        none: 'Aucun',
      },
      report: {
        title: 'Rapport de synthèse du dossier',
        overall: 'Statut global :',
        missing: 'Documents manquants :',
        requiringReview: 'Documents à examiner :',
        mismatches: 'Discordances détectées :',
        nextSteps: 'Prochaines étapes recommandées',
        noAction: 'Aucune action requise d’après les données retournées.',
        legalDisclaimer: 'Ce rapport est généré par un système automatisé pour usage interne. Il n’est ni signé électroniquement, ni certifié juridiquement, et ne constitue pas une attestation légale d’authenticité.',
        none: 'Aucun',
      },
      stepsGeneration: {
        missingDocs: (docs) => `Réclamer les documents manquants auprès de l’exportateur : ${docs}.`,
        unclassified: (pages) => `Examiner les pages ${pages} : le système n’a pas pu déterminer leur nature.`,
        reviewDoc: (doc, pages) => `Vérifier les champs signalés pour le document « ${doc} » (pages ${pages}).`,
        mismatchCheck: (check) => `Résoudre l’écart « ${check} » entre les documents.`,
        reviewCheck: (check, msg) => `Examiner le contrôle « ${check} » : ${msg}`,
      },
    },
    docTypes: {
      commercial_invoice: 'Facture commerciale',
      packing_list: 'Liste de colisage',
      bill_of_lading: 'Connaissement (Bill of Lading)',
      certificate_of_origin: 'Certificat d’origine',
      certificate_of_quality: 'Certificat de qualité',
      certificate_of_conformity: 'Certificat de conformité',
      phytosanitary_certificate: 'Certificat phytosanitaire',
      fumigation_certificate: 'Certificat de fumigation',
      unknown: 'Pages non identifiées',
    },
    statuses: {
      passed: 'Conforme',
      complete: 'Complet',
      needs_review: 'À vérifier',
      mismatch: 'Discordance',
      needs_ocr: 'ROC requis',
      missing: 'Manquant',
      detected: 'Détecté',
    },
    common: {
      notFound: 'Non trouvé',
      yes: 'Oui',
      no: 'Non',
    },
  },
}
