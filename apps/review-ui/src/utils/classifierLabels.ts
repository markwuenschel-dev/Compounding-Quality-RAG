/**
 * Human-friendly labels for the backend's canonical (snake_case / acronym) enum
 * values, so the UI never shows raw programming identifiers.
 *
 * Keyed by the exact value the API returns. The same value string always means
 * the same thing across enums, so a single flat map is safe. Unknown values fall
 * back to a sentence-cased de-snake of the raw value (see formatClassifier).
 */
export const CLASSIFIER_LABELS: Record<string, string> = {
  // Source type (retrieved evidence)
  sop: "SOP",
  synthetic_inquiry: "Synthetic inquiry",
  synthetic_api_reference: "Synthetic API reference",
  eval_question: "Eval question",

  // Intake source
  qre_general_question_form: "QRE general question form",
  customer_review: "Customer review",

  // Submitter role
  frontline_pharmacist: "Frontline pharmacist",
  customer: "Customer",
  customer_care: "Customer care",
  customer_review_system: "Customer review system",
  technical_services: "Technical services",
  operations_leadership: "Operations leadership",
  other: "Other",
  unknown: "Unknown",

  // Submission purpose
  customer_reported_concern: "Customer-reported concern",
  frontline_pharmacist_question: "Frontline pharmacist question",
  documentation_update: "Documentation update",
  escalation_request: "Escalation request",
  customer_review_followup: "Customer review follow-up",

  // Formal classification
  QRE: "Quality-related event (QRE)",
  general_question: "General question",

  // Formal category
  customer_service_related: "Customer service related",
  equipment_device_related: "Equipment / device related",
  medication_related: "Medication related",
  suspected_ADE: "Suspected adverse drug event",
  dispensing_error: "Dispensing error",

  // Formal subcategory
  customer_experience: "Customer experience",
  autoship_issue: "Autoship issue",
  click_to_delivery: "Click to delivery",
  packaging: "Packaging",
  pricing: "Pricing",
  missing_equipment: "Missing equipment",
  defective_device: "Defective device",
  syringe_issue: "Syringe issue",
  flavor: "Flavor",
  bud: "Beyond-use date (BUD)",
  formulation: "Formulation",
  package_size: "Package size",
  efficacy: "Efficacy",
  days_supply: "Days supply",
  flavor_related_ADE: "Flavor-related adverse drug event",
  wrong_quantity: "Wrong quantity",
  wrong_patient: "Wrong patient",
  wrong_medication: "Wrong medication",
  wrong_directions: "Wrong directions",
  missing_item: "Missing item",
  compounding_error: "Compounding error",
  labeling_error: "Labeling error",

  // Concern type
  pet_refused_flavor: "Pet refused flavor",
  smell_concern: "Smell concern",
  viscosity_or_thickness_concern: "Viscosity or thickness concern",
  color_change: "Color change",
  efficacy_concern: "Efficacy concern",
  possible_adverse_drug_event: "Possible adverse drug event",
  flavor_related_vomiting: "Flavor-related vomiting",
  ingredient_presence_question: "Ingredient presence question",
  oral_liquid_shortage: "Oral liquid shortage",
  days_supply_question: "Days supply question",
  bud_question: "Beyond-use date (BUD) question",
  temperature_excursion_question: "Temperature excursion question",
  limited_guidance_specialty_compound_question:
    "Limited-guidance specialty compound question",
  syringe_or_device_issue: "Syringe or device issue",
  package_damage_or_leakage: "Package damage or leakage",
  broken_tablet_or_capsule_damage: "Broken tablet or capsule damage",
  labeling_issue: "Labeling issue",
  possible_dispensing_error: "Possible dispensing error",
  wrong_patient_or_wrong_medication: "Wrong patient or wrong medication",
  possible_contamination: "Possible contamination",
  veterinarian_alleges_harm: "Veterinarian alleges harm",
  pet_hospitalized: "Pet hospitalized",
  pet_death: "Pet death",
  threatened_legal_action: "Threatened legal action",

  // Risk lane
  expected_self_limiting: "Expected, self-limiting",
  unexpected_non_life_threatening: "Unexpected, non-life-threatening",
  life_threatening_or_legal: "Life-threatening or legal",

  // Review scope
  full_quality_review: "Full quality review",
  customer_review_record_check: "Customer review record check",
  guidance_only: "Guidance only",
  escalation_review: "Escalation review",
  insufficient_information: "Insufficient information",

  // Record review result
  no_discrepancy_found: "No discrepancy found",
  documentation_incomplete: "Documentation incomplete",
  documentation_discrepancy_found: "Documentation discrepancy found",
  not_applicable: "Not applicable",

  // Lot / batch pattern summary
  no_similar_batch_concerns_found: "No similar batch concerns found",
  similar_concern_same_batch_found: "Similar concern in same batch found",
  similar_concern_same_medication_dosage_form_found:
    "Similar concern for same medication or dosage form",
  trend_threshold_met: "Trend threshold met",
  unavailable: "Unavailable",

  // Inventory inspection result
  no_inventory_available: "No inventory available",
  no_visual_concern_found: "No visual concern found",
  visual_concern_found: "Visual concern found",
  not_checked: "Not checked",

  // API reference review result
  not_needed: "Not needed",
  synthetic_reference_consulted: "Synthetic reference consulted",
  external_reference_consulted: "External reference consulted",
  external_reference_needed: "External reference needed",
  not_supported_by_public_corpus: "Not supported by public corpus",

  // Handling path
  document_only_no_action: "Document only, no action",
  delegate_to_frontline_pharmacist: "Delegate to frontline pharmacist",
  respond_to_frontline_pharmacist: "Respond to frontline pharmacist",
  technical_services_customer_outreach: "Technical services customer outreach",
  record_review_then_document: "Record review, then document",
  investigate_to_resolution: "Investigate to resolution",
  flag_leadership_during_investigation: "Flag leadership during investigation",
  leadership_escalation_before_resolution:
    "Leadership escalation before resolution",

  // Resolution options
  replacement_or_reship_review: "Replacement or reship review",
  refund_or_concession_review: "Refund or concession review",
  alternate_dosage_form_discussion: "Alternate dosage form discussion",
  counseling_or_follow_up: "Counseling or follow-up",
  leadership_directed_resolution: "Leadership-directed resolution",
  no_customer_facing_resolution: "No customer-facing resolution",

  // Escalation triggers
  pet_hospitalization: "Pet hospitalization",
  veterinarian_alleges_harm_from_compound:
    "Veterinarian alleges harm from compound",
  repeat_issue_same_lot_or_batch_with_conditions:
    "Repeat issue in same lot or batch",
  rare_regulatory_or_compliance_concern: "Regulatory or compliance concern",

  // Species
  cat: "Cat",
  dog: "Dog",
  horse: "Horse",

  // Dosage form
  oral_liquid: "Oral liquid",
  capsule: "Capsule",
  tablet: "Tablet",
  transdermal: "Transdermal",
  chewable: "Chewable",
  powder: "Powder",
  ophthalmic: "Ophthalmic",
  oral_paste: "Oral paste",
  topical: "Topical",

  // Extraction evidence status
  explicit: "Explicit",
  normalized: "Normalized",
  ambiguous: "Ambiguous",
  not_stated: "Not stated",

  // Aliases for the legacy "leADErship" typo, in case cached/older responses
  // still carry the corrupted value before the engine rebuild propagates.
  operations_leADErship: "Operations leadership",
  flag_leADErship_during_investigation: "Flag leadership during investigation",
  leADErship_escalation_before_resolution:
    "Leadership escalation before resolution",
  leADErship_directed_resolution: "Leadership-directed resolution",
};

/**
 * Maps a backend enum value to a human-friendly label. Falls back to a
 * sentence-cased de-snake of the raw value for anything not in the map
 * (e.g. free-form field identifiers). Returns null for null/blank input.
 */
export function formatClassifier(
  value: string | null | undefined,
): string | null {
  if (value == null) {
    return null;
  }

  const trimmed = value.trim();

  if (trimmed.length === 0) {
    return null;
  }

  const mapped = CLASSIFIER_LABELS[trimmed];

  if (mapped) {
    return mapped;
  }

  const words = trimmed.replace(/_/g, " ").trim();

  return words.charAt(0).toUpperCase() + words.slice(1);
}

/** Maps a list of enum values, keeping the raw value if it cannot be formatted. */
export function formatClassifierList(values: string[]): string[] {
  return values.map((value) => formatClassifier(value) ?? value);
}
