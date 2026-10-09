"""Scientific Named Entity, Formula & Citation Extractor for Privreach GraphRAG.

Performs high-precision deterministic extraction of:
1. Scientific Eponyms, Theories, Laws, and Principles.
2. Mathematical Quantities, Physical Constants, and Variables.
3. Formal Bibliographic Citations & Cross-Document References.
4. Semantic Subject-Predicate-Object Triplet Relations.
"""

import re
from typing import List, Dict, Tuple, Set, Optional, Any


# Pre-compiled high-frequency scientific entities and laws
KNOWN_SCIENTIFIC_ENTITIES = {
    # Quantum & Atomic Physics
    "de broglie wavelength": "de Broglie Wavelength",
    "de broglie hypothesis": "de Broglie Hypothesis",
    "matter waves": "Matter Waves",
    "wave-particle duality": "Wave-Particle Duality",
    "bohr's model": "Bohr's Atomic Model",
    "bohr orbit": "Bohr Orbit",
    "bohr radius": "Bohr Radius",
    "bohr quantization": "Bohr Quantization Condition",
    "angular momentum": "Angular Momentum",
    "planck's constant": "Planck's Constant",
    "planck's quantum theory": "Planck's Quantum Theory",
    "heisenberg uncertainty principle": "Heisenberg Uncertainty Principle",
    "schrodinger equation": "Schrödinger Equation",
    "schrödinger equation": "Schrödinger Equation",
    "wave function": "Wave Function",
    "rydberg constant": "Rydberg Constant",
    "rydberg formula": "Rydberg Formula",
    "balmer series": "Balmer Series",
    "lyman series": "Lyman Series",
    "paschen series": "Paschen Series",
    "photoelectric effect": "Photoelectric Effect",
    "compton effect": "Compton Effect",
    "davisson-germer experiment": "Davisson-Germer Experiment",
    "pauli exclusion principle": "Pauli Exclusion Principle",
    "hund's rule": "Hund's Rule",
    "aufbau principle": "Aufbau Principle",
    "kinetic energy": "Kinetic Energy",
    "potential energy": "Potential Energy",
    "standing wave": "Standing Wave",
    "quantum number": "Quantum Number",
    "principal quantum number": "Principal Quantum Number",
    "speed of light": "Speed of Light",
    "electron momentum": "Electron Momentum",
    "ground state": "Ground State",
    "excited state": "Excited State",
    "ionization energy": "Ionization Energy",
}

# Regex for capitalized scientific terms and eponyms (e.g., Einstein-Podolsky-Rosen, Maxwell-Boltzmann)
EPONYM_PATTERN = re.compile(
    r'\b(?:[A-Z][a-z]+(?:[-–][A-Z][a-z]+)?(?:\'s)?\s+)?'
    r'[A-Z][a-z]+(?:[-–][A-Z][a-z]+)?(?:\'s)?\s+'
    r'(?:model|law|principle|formula|equation|theory|hypothesis|effect|constant|series|rule|theorem|experiment|quantization|condition|distribution|relation)\b',
    re.IGNORECASE
)

# Regex for formal academic citation brackets
CITATION_BRACKET_PATTERN = re.compile(r'\[(\d+(?:[–-]\d+)?(?:,\s*\d+)*)\]')
CITATION_AUTHOR_YEAR_PATTERN = re.compile(r'\b([A-Z][a-z]+(?:\s+et\s+al\.)?)\s*\((\d{4})\)')


class ExtractedRelation:
    """Semantic relation triplet linking two entities."""
    def __init__(self, subject: str, predicate: str, obj: str, weight: float = 1.0, evidence: str = ""):
        self.subject = subject
        self.predicate = predicate
        self.obj = obj
        self.weight = weight
        self.evidence = evidence

    def to_dict(self) -> Dict[str, Any]:
        return {
            "subject": self.subject,
            "predicate": self.predicate,
            "object": self.obj,
            "weight": self.weight,
            "evidence": self.evidence
        }


class ScientificEntityExtractor:
    """Deterministic extractor for scientific knowledge nodes and citation edges."""

    @classmethod
    def extract_entities(cls, text: str) -> List[str]:
        """
        Extracts normalized scientific entity concepts from text.
        """
        if not text:
            return []

        found: Set[str] = set()
        text_lower = text.lower()

        # 1. Exact match against known scientific ontology dictionary
        for key, canonical in KNOWN_SCIENTIFIC_ENTITIES.items():
            if key in text_lower:
                found.add(canonical)

        # 2. Match generalized eponymous laws and principles
        for match in EPONYM_PATTERN.finditer(text):
            raw = match.group(0).strip()
            # Normalize title case
            canonical = " ".join(word.capitalize() if not word.lower().startswith("de") else "de" for word in raw.split())
            if len(canonical) > 3 and not canonical.lower().startswith("in "):
                found.add(canonical)

        # 3. Detect LaTeX equation targets (e.g. \lambda = h/p -> de Broglie / wavelength)
        if r"\lambda" in text:
            found.add("Wavelength (λ)")
        if "mvr" in text or "m*v*r" in text:
            found.add("Bohr Quantization Condition")
        if r"\hbar" in text or "h / 2" in text or "h/(2pi)" in text:
            found.add("Reduced Planck Constant (ℏ)")

        return sorted(list(found))

    @classmethod
    def extract_citations(cls, text: str) -> List[str]:
        """
        Extracts formal citation markers (e.g. '[1]', '[2]', 'Bohr (1913)').
        """
        citations = []
        for m in CITATION_BRACKET_PATTERN.finditer(text):
            citations.append(f"[{m.group(1)}]")
        for m in CITATION_AUTHOR_YEAR_PATTERN.finditer(text):
            citations.append(f"{m.group(1)} ({m.group(2)})")
        return citations

    @classmethod
    def extract_relations(cls, text: str, entities: Optional[List[str]] = None) -> List[ExtractedRelation]:
        """
        Extracts semantic relational triplets between entities in text.
        """
        if entities is None:
            entities = cls.extract_entities(text)

        if len(entities) < 2:
            return []

        relations: List[ExtractedRelation] = []
        sentences = re.split(r'(?<=[.!?])\s+', text)

        # Semantic predicate rules
        predicate_patterns = [
            (re.compile(r'\b(?:derived\s+from|derives\s+from|originates\s+from)\b', re.I), "DERIVED_FROM"),
            (re.compile(r'\b(?:relates\s+to|related\s+to|connected\s+with|corresponds\s+to)\b', re.I), "RELATES_TO"),
            (re.compile(r'\b(?:defines|states\s+that|formulates|specifies)\b', re.I), "DEFINES"),
            (re.compile(r'\b(?:quantizes|imposes\s+quantization|restricts)\b', re.I), "QUANTIZES"),
            (re.compile(r'\b(?:proves|demonstrates|confirms|verified\s+by)\b', re.I), "VERIFIED_BY"),
            (re.compile(r'\b(?:leads\s+to|yields|results\s+in|produces)\b', re.I), "LEADS_TO"),
            (re.compile(r'\b(?:proportional\s+to|inversely\s+proportional)\b', re.I), "PROPORTIONAL_TO"),
            (re.compile(r'\b(?:requires|satisfies|depends\s+on)\b', re.I), "REQUIRES"),
        ]

        # Scan each sentence for pairs of co-occurring entities
        for sent in sentences:
            sent_lower = sent.lower()
            present_in_sent = [e for e in entities if e.lower() in sent_lower]
            if len(present_in_sent) >= 2:
                # Determine predicate
                pred_label = "CO_OCCURS_WITH"
                for pat, label in predicate_patterns:
                    if pat.search(sent):
                        pred_label = label
                        break

                # Link pair
                for i in range(len(present_in_sent)):
                    for j in range(i + 1, len(present_in_sent)):
                        e1, e2 = present_in_sent[i], present_in_sent[j]
                        relations.append(ExtractedRelation(
                            subject=e1,
                            predicate=pred_label,
                            obj=e2,
                            weight=1.5 if pred_label != "CO_OCCURS_WITH" else 1.0,
                            evidence=sent[:120].strip()
                        ))

        return relations
