"""
Equation AST Isomorphism Engine.

Discovers mathematical analogies across disparate scientific disciplines by
canonicalizing SymPy expression trees and identifying shared operator structures
regardless of domain-specific variable naming conventions.
"""

from typing import List, Dict, Set, Tuple, Optional, Any
import hashlib
import sympy as sp
from sympy.core.basic import Basic
from pydantic import BaseModel, Field


class EquationNode(BaseModel):
    """Metadata record for an ingested mathematical equation."""
    equation_id: str
    name: str
    raw_expression: str
    domain: str  # e.g., "astrophysics", "electromagnetism", "thermodynamics"
    source_doc: Optional[str] = None
    canonical_form: str = ""
    ast_signature: str = ""


class IsomorphismCluster(BaseModel):
    """A cluster of isomorphic equations across different scientific fields."""
    cluster_id: str
    ast_signature: str
    domains_involved: List[str] = Field(default_factory=list)
    equations: List[EquationNode] = Field(default_factory=list)
    analogy_description: str = ""


class IsomorphismReport(BaseModel):
    """Comprehensive discovery report for cross-disciplinary mathematical analogies."""
    total_equations_indexed: int = 0
    total_isomorphic_clusters: int = 0
    cross_domain_discoveries: List[IsomorphismCluster] = Field(default_factory=list)


class EquationIsomorphismEngine:
    """
    Parses, canonicalizes, and groups mathematical equations by topological AST equivalence.
    """

    def __init__(self):
        self.equations: List[EquationNode] = []
        self._clusters: Dict[str, List[EquationNode]] = {}

    def _parse_to_sympy(self, expr_str: str) -> Optional[sp.Expr]:
        """Parses a mathematical string into a SymPy expression."""
        clean_str = expr_str.strip()
        # If equation has equality "=", move to one side: A = B -> A - (B)
        if "=" in clean_str:
            parts = clean_str.split("=", 1)
            clean_str = f"({parts[0]}) - ({parts[1]})"

        try:
            parsed = sp.sympify(clean_str, evaluate=False)
            return parsed
        except Exception:
            try:
                # Fallback to standard evaluated parse
                return sp.sympify(clean_str)
            except Exception:
                return None

    def canonicalize_ast(self, expr: sp.Basic) -> Tuple[str, str]:
        """
        Recursively replaces variable symbols with canonical positional placeholders
        (v0, v1, v2...) in deterministic pre-order traversal.

        Returns:
            (canonical_str_representation, ast_sha256_signature)
        """
        # Collect all free symbols in deterministic sorted order
        free_syms = sorted(expr.free_symbols, key=lambda s: s.name)
        substitution_map = {
            sym: sp.Symbol(f"v_{idx}") for idx, sym in enumerate(free_syms)
        }

        # Substitute into canonicalized expression
        canonical_expr = expr.subs(substitution_map)
        canonical_str = str(canonical_expr)

        # Generate an abstract operator topology string (operators only + placeholder indices)
        def _get_tree_structure(node: sp.Basic) -> str:
            node_type = node.__class__.__name__
            if not node.args:
                # Leaf node: indicate if symbol or number
                if node.is_Symbol:
                    return f"Sym({node.name})"
                elif node.is_Number:
                    return f"Num({float(node):.2f})" if node.is_real else "Num"
                return node_type

            arg_structures = sorted([_get_tree_structure(arg) for arg in node.args])
            return f"{node_type}({','.join(arg_structures)})"

        structural_topology = _get_tree_structure(canonical_expr)
        ast_signature = hashlib.sha256(structural_topology.encode("utf-8")).hexdigest()[:16]

        return canonical_str, ast_signature

    def register_equation(
        self,
        name: str,
        expression_str: str,
        domain: str,
        equation_id: Optional[str] = None,
        source_doc: Optional[str] = None,
    ) -> Optional[EquationNode]:
        """
        Parses, canonicalizes, and registers an equation in the isomorphism index.
        """
        parsed_expr = self._parse_to_sympy(expression_str)
        if parsed_expr is None:
            return None

        canonical_str, ast_sig = self.canonicalize_ast(parsed_expr)
        eq_id = equation_id or f"eq_{len(self.equations) + 1:03d}"

        node = EquationNode(
            equation_id=eq_id,
            name=name,
            raw_expression=expression_str,
            domain=domain,
            source_doc=source_doc,
            canonical_form=canonical_str,
            ast_signature=ast_sig,
        )

        self.equations.append(node)
        self._clusters.setdefault(ast_sig, []).append(node)
        return node

    def detect_isomorphisms(self) -> IsomorphismReport:
        """
        Analyzes the index for cross-domain mathematical isomorphisms.
        """
        cross_domain_clusters: List[IsomorphismCluster] = []

        for sig, cluster_equations in self._clusters.items():
            domains = list(set(eq.domain for eq in cluster_equations))
            # If cluster contains equations from 2 or more distinct scientific domains
            if len(domains) >= 2 and len(cluster_equations) >= 2:
                names = [eq.name for eq in cluster_equations]
                description = (
                    f"Structural AST equivalence identified between {len(cluster_equations)} equations "
                    f"across {len(domains)} disciplines ({', '.join(domains)}): {', '.join(names)}"
                )
                cross_domain_clusters.append(
                    IsomorphismCluster(
                        cluster_id=f"cluster_{sig}",
                        ast_signature=sig,
                        domains_involved=domains,
                        equations=cluster_equations,
                        analogy_description=description,
                    )
                )

        return IsomorphismReport(
            total_equations_indexed=len(self.equations),
            total_isomorphic_clusters=len(cross_domain_clusters),
            cross_domain_discoveries=cross_domain_clusters,
        )
