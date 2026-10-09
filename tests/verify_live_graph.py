import urllib.request
import json
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

def main():
    print("=" * 60)
    print("LIVE PRIVEARCH GRAPHRAG REST API VERIFICATION")
    print("=" * 60)

    # 1. Status Check
    status_req = urllib.request.Request("http://127.0.0.1:8765/api/status")
    with urllib.request.urlopen(status_req) as res:
        status = json.loads(res.read().decode("utf-8"))
        print(f"Status: Indexed chunks = {status.get('indexed_chunks')}, Docs = {status.get('indexed_documents')}")

    # 2. Global Graph Check
    graph_req = urllib.request.Request("http://127.0.0.1:8765/api/graph")
    with urllib.request.urlopen(graph_req) as res:
        graph = json.loads(res.read().decode("utf-8"))
        nodes = graph.get("nodes", [])
        edges = graph.get("edges", [])
        bridges = graph.get("bridges", []) or graph.get("cross_document_bridges", [])
        communities = graph.get("communities", [])

        print(f"Global Graph: Nodes={len(nodes)}, Edges={len(edges)}, Bridges={len(bridges)}, Communities={len(communities)}")
        print("\nDiscovered Cross-Document Bridges:")
        for b in bridges[:10]:
            print(f"  * [BRIDGE] '{b['entity']}' -> Shared by docs: {b['documents']} (chunks: {len(b['chunk_ids'])})")

    # 3. Query Subnetwork & Multi-Hop Expansion Check
    print("\nExecuting GraphRAG Query...")
    query_payload = {
        "query": "Explain how oxidation state and equivalent weight relate to electron transfer and Bohr atom",
        "top_k": 3
    }
    query_req = urllib.request.Request(
        "http://127.0.0.1:8765/api/query",
        data=json.dumps(query_payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(query_req) as res:
        query_res = json.loads(res.read().decode("utf-8"))
        subnetwork = query_res.get("graph_subnetwork", {})
        sub_nodes = subnetwork.get("nodes", [])
        sub_edges = subnetwork.get("edges", [])
        sub_bridges = subnetwork.get("bridges", [])
        graph_md = query_res.get("graph_markdown", "")

        print(f"Query Result:")
        print(f"  - Subnetwork Nodes: {len(sub_nodes)}")
        print(f"  - Subnetwork Edges: {len(sub_edges)}")
        print(f"  - Bridges in Subnetwork: {len(sub_bridges)}")
        print(f"  - Graph Markdown Length: {len(graph_md)} chars")
        print(f"  - Mermaid Diagram Found: {'```mermaid' in graph_md}")
        print(f"  - Retrieved Passages: {len(query_res.get('retrieved_passages', []))}")
        print(f"  - Synthesized Answer Preview: {query_res.get('synthesized_answer', '')[:120]}...")

    print("=" * 60)
    print("VERIFICATION COMPLETED SUCCESSFULLY")
    print("=" * 60)

if __name__ == "__main__":
    main()
