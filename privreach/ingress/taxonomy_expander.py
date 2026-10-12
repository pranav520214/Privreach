"""
Deterministic Taxonomy Expansion Engine (Zero-LLM).

Expands research queries using deterministic ontology graph traversal,
synonym sets, hypernyms/hyponyms, and domain-specific acronym mappings.
Contains zero stochastic neural generation to ensure complete reproducibility.
"""

from typing import List, Dict, Set, Optional
import re
from collections import defaultdict


DEFAULT_STEM_TAXONOMY: Dict[str, Dict[str, List[str]]] = {
    # Semiconductor Physics & Lithography
    "lithography": {
        "synonyms": ["photolithography", "microlithography", "nanolithography"],
        "narrower": ["euv", "extreme ultraviolet lithography", "duv", "deep ultraviolet lithography",
                     "immersion lithography", "electron beam lithography", "nanoimprint lithography",
                     "x-ray lithography", "directed self-assembly"],
        "related": ["photoresist", "photomask", "pellicle", "stepper", "scanner", "numerical aperture",
                    "rayleigh criterion", "critical dimension", "line edge roughness", "overlay error"],
        "broader": ["semiconductor fabrication", "microfabrication", "nanotechnology"],
    },
    "semiconductor": {
        "synonyms": ["solid-state", "integrated circuit", "microchip"],
        "narrower": ["silicon", "gallium nitride", "silicon carbide", "gallium arsenide", "indium phosphide", "two-dimensional materials", "graphene", "transition metal dichalcogenides"],
        "related": ["bandgap", "doping", "carrier mobility", "transistor", "finfet", "gaafet", "nanosheet", "cmos"],
        "broader": ["condensed matter physics", "materials science", "solid state physics"],
    },
    "euv": {
        "synonyms": ["extreme ultraviolet", "13.5nm lithography"],
        "narrower": ["high-na euv", "0.55 na euv"],
        "related": ["tin plasma source", "lpp source", "multilayer mo/si mirror", "euv pellicle", "stochastic defects"],
        "broader": ["lithography", "ultraviolet optics"],
    },
    "duv": {
        "synonyms": ["deep ultraviolet", "193nm lithography", "248nm lithography"],
        "narrower": ["arf immersion", "krf excimer laser"],
        "related": ["water immersion", "double patterning", "quadruple patterning"],
        "broader": ["lithography"],
    },
    # Quantum Computing & Information
    "quantum computing": {
        "synonyms": ["quantum information processing", "quantum computation"],
        "narrower": ["superconducting qubits", "trapped ion qubits", "neutral atom qubits", "photonic quantum computing", "topological qubits", "spin qubits"],
        "related": ["quantum decoherence", "quantum gate fidelity", "quantum error correction", "surface code", "quantum supremacy", "quantum advantage", "bloch sphere"],
        "broader": ["quantum mechanics", "computer science", "quantum information science"],
    },
    "quantum error correction": {
        "synonyms": ["qec", "fault-tolerant quantum computing"],
        "narrower": ["surface code", "color code", "bacon-shor code", "ldpc codes", "cat codes"],
        "related": ["syndrome extraction", "fault tolerance threshold", "logical qubit", "physical qubit"],
        "broader": ["quantum computing", "coding theory"],
    },
    # Machine Learning & AI
    "machine learning": {
        "synonyms": ["statistical learning", "pattern recognition"],
        "narrower": ["deep learning", "reinforcement learning", "supervised learning", "unsupervised learning", "representation learning"],
        "related": ["generalization", "gradient descent", "loss function", "backpropagation", "regularization", "transformer architecture"],
        "broader": ["artificial intelligence", "computer science"],
    },
    "retrieval augmented generation": {
        "synonyms": ["rag", "grounded retrieval", "hybrid search"],
        "narrower": ["graphrag", "dense passage retrieval", "reciprocal rank fusion"],
        "related": ["bm25", "faiss", "vector embeddings", "knowledge graph", "citation verification", "hallucination mitigation"],
        "broader": ["natural language processing", "information retrieval"],
    },
    # Materials Science & Chemistry
    "superconductivity": {
        "synonyms": ["superconducting state", "zero electrical resistance"],
        "narrower": ["high-temperature superconductivity", "cuprate superconductors", "iron-based superconductors", "hydride superconductors", "unconventional superconductivity"],
        "related": ["meissner effect", "critical temperature", "bcs theory", "cooper pairs", "josephson junction", "london penetration depth"],
        "broader": ["condensed matter physics", "solid-state physics"],
    },
    "perovskite": {
        "synonyms": ["halide perovskite", "perovskite crystal structure"],
        "narrower": ["metal halide perovskites", "lead halide perovskites", "lead-free perovskites"],
        "related": ["solar cells", "photovoltaic efficiency", "bandgap engineering", "stability degradation", "optoelectronics"],
        "broader": ["materials science", "crystallography", "photovoltaics"],
    },
}

# Domain acronym lookups for deterministic bidirectional resolution
ACRONYM_MAP: Dict[str, str] = {
    "euv": "extreme ultraviolet",
    "duv": "deep ultraviolet",
    "finfet": "fin field-effect transistor",
    "gaafet": "gate-all-around field-effect transistor",
    "na": "numerical aperture",
    "qec": "quantum error correction",
    "rag": "retrieval augmented generation",
    "bm25": "best matching 25",
    "faiss": "facebook ai similarity search",
    "rrf": "reciprocal rank fusion",
    "fem": "finite element method",
    "fea": "finite element analysis",
    "drc": "design rule check",
    "pcb": "printed circuit board",
    "cmos": "complementary metal-oxide-semiconductor",
    "gan": "gallium nitride",
    "sic": "silicon carbide",
    "cvd": "chemical vapor deposition",
    "ald": "atomic layer deposition",
    "afm": "atomic force microscopy",
    "tem": "transmission electron microscopy",
    "sem": "scanning electron microscopy",
    "xrd": "x-ray diffraction",
}


class DeterministicTaxonomyExpander:
    """
    Expands research topics into comprehensive, domain-grounded query terms
    using deterministic graph traversal without LLM hallucination.
    """

    def __init__(self, custom_taxonomy: Optional[Dict[str, Dict[str, List[str]]]] = None):
        self.taxonomy = dict(DEFAULT_STEM_TAXONOMY)
        if custom_taxonomy:
            for term, relations in custom_taxonomy.items():
                if term in self.taxonomy:
                    for rel_type, values in relations.items():
                        existing = self.taxonomy[term].setdefault(rel_type, [])
                        for val in values:
                            if val not in existing:
                                existing.append(val)
                else:
                    self.taxonomy[term] = relations

        # Inverted index: word -> canonical key in taxonomy
        self._term_index: Dict[str, Set[str]] = defaultdict(set)
        for canonical_term, relations in self.taxonomy.items():
            self._term_index[canonical_term.lower()].add(canonical_term)
            for synonym in relations.get("synonyms", []):
                self._term_index[synonym.lower()].add(canonical_term)
            for narrower in relations.get("narrower", []):
                self._term_index[narrower.lower()].add(canonical_term)

    def normalize_term(self, text: str) -> str:
        """Strips punctuation, lowercases, and collapses whitespace."""
        clean = re.sub(r"[^\w\s-]", " ", text.lower())
        return " ".join(clean.split())

    def extract_ngrams(self, text: str, max_n: int = 3) -> List[str]:
        """Extract unigrams, bigrams, and trigrams from normalized query string."""
        words = self.normalize_term(text).split()
        ngrams: List[str] = []
        for n in range(1, min(max_n + 1, len(words) + 1)):
            for i in range(len(words) - n + 1):
                ngrams.append(" ".join(words[i : i + n]))
        return ngrams

    def expand(self, query: str, max_terms: int = 30, depth: int = 2) -> List[str]:
        """
        Deterministically expands query string into a ranked list of search terms.

        Args:
            query: User's raw search prompt (e.g. "semiconductor lithography")
            max_terms: Maximum number of expanded keywords to emit
            depth: Graph traversal depth for narrower/related nodes

        Returns:
            Deduplicated, prioritized list of search terms.
        """
        normalized_query = self.normalize_term(query)
        expanded: Set[str] = set()
        queue_keys: Set[str] = set()

        # 1. Always retain the original query terms
        expanded.add(normalized_query)
        raw_words = normalized_query.split()
        for w in raw_words:
            if len(w) > 2:
                expanded.add(w)

        # 2. Check for acronym expansions / reversals
        for w in raw_words:
            if w in ACRONYM_MAP:
                expanded.add(ACRONYM_MAP[w])
        for acr, expansion in ACRONYM_MAP.items():
            if expansion in normalized_query:
                expanded.add(acr)

        # 3. Extract n-grams and match with canonical ontology keys
        ngrams = self.extract_ngrams(normalized_query)
        for ngram in ngrams:
            if ngram in self._term_index:
                queue_keys.update(self._term_index[ngram])
            # Check partial matches
            for key in self.taxonomy:
                if key in ngram or ngram in key:
                    queue_keys.add(key)

        # 4. Deterministic Graph Traversal
        visited_keys: Set[str] = set()
        current_layer = set(queue_keys)

        for _ in range(depth):
            next_layer: Set[str] = set()
            for key in current_layer:
                if key in visited_keys:
                    continue
                visited_keys.add(key)
                node = self.taxonomy.get(key, {})

                # Collect direct synonyms (highest priority)
                for syn in node.get("synonyms", []):
                    expanded.add(syn.lower())

                # Collect narrower terms (specific research subtopics)
                for n_term in node.get("narrower", []):
                    n_norm = n_term.lower()
                    expanded.add(n_norm)
                    if n_norm in self.taxonomy:
                        next_layer.add(n_norm)

                # Collect related technical terms
                for r_term in node.get("related", []):
                    r_norm = r_term.lower()
                    expanded.add(r_norm)
                    if r_norm in self.taxonomy:
                        next_layer.add(r_norm)

                # Collect broader terms for context
                for b_term in node.get("broader", []):
                    expanded.add(b_term.lower())

            current_layer = next_layer

        # 5. Deterministic sorting: Exact query first, then length/specificity, then alphabetical
        def sort_key(term: str):
            is_exact = 0 if term == normalized_query else 1
            is_in_query = 0 if term in normalized_query else 1
            # More specific terms (longer word count) ranked before single generic words
            word_count = len(term.split())
            return (is_exact, is_in_query, -word_count, term)

        sorted_results = sorted(expanded, key=sort_key)
        return sorted_results[:max_terms]
