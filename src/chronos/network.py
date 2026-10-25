"""
Prosopographic Network Graph Engine for Sumerian Administrative Networks.
Extracts co-occurrences, bureaucratic workflows, and seal attestations into a NetworkX graph,
computing degree centrality, betweenness centrality, communities, and Cytoscape/D3 topologies.
"""

from dataclasses import dataclass, field
import json
import re
from typing import Any, Dict, List, Optional, Set, Tuple
import networkx as nx

from src.compiler.parser import TabletRecord
from src.chronos.prosopography import ProsopographyExtractor
from src.authors.scribe_identifier import AuthorIdentifier


@dataclass
class NetworkNode:
    name: str
    role: str
    tablet_count: int
    attested_years: List[str]
    degree: int
    degree_centrality: float
    betweenness_centrality: float
    community_id: int


@dataclass
class NetworkEdge:
    source: str
    target: str
    weight: int
    tablets: List[str]
    relation_types: List[str]


class ProsopographicNetwork:
    """Builds and analyzes social and administrative interaction graphs of Ur III Mesopotamia."""

    def __init__(self):
        self.graph = nx.Graph()
        self.extractor = ProsopographyExtractor()
        self.author_id = AuthorIdentifier()
        self._node_metadata: Dict[str, Dict[str, Any]] = {}

    def build_network(
        self,
        tablets: List[TabletRecord],
        min_co_occurrences: int = 1,
    ) -> nx.Graph:
        """
        Constructs the undirected co-occurrence and collaboration graph across all input tablets.
        """
        self.graph.clear()
        self._node_metadata.clear()

        # Temporary co-occurrence map: (u, v) -> {tablets: set(), relations: set()}
        edge_data: Dict[Tuple[str, str], Dict[str, Any]] = {}
        actor_tablets: Dict[str, Set[str]] = {}
        actor_years: Dict[str, Set[str]] = {}
        actor_roles: Dict[str, str] = {}

        for tab in tablets:
            entities = self.extractor.extract_from_tablet(tab)
            actors_in_tab: Set[str] = set(entities.officials)

            # Check explicit author/scribe
            author = self.author_id.extract_explicit_author(tab)
            if author and author.identified_scribe:
                actors_in_tab.add(author.identified_scribe)
                actor_roles[author.identified_scribe] = author.title or "dub-sar"

            # Filter out generic lacuna tokens
            clean_actors = {
                a for a in actors_in_tab
                if len(a) > 2 and not a.startswith("...") and a not in ("x", "X", "unknown")
            }

            for actor in clean_actors:
                if actor not in actor_tablets:
                    actor_tablets[actor] = set()
                    actor_years[actor] = set()
                    actor_roles.setdefault(actor, "official")

                actor_tablets[actor].add(tab.id_text)
                if entities.year_code:
                    actor_years[actor].add(entities.year_code)

            # Create edges between all co-occurring actors on this tablet
            sorted_actors = sorted(list(clean_actors))
            for i in range(len(sorted_actors)):
                for j in range(i + 1, len(sorted_actors)):
                    u = sorted_actors[i]
                    v = sorted_actors[j]
                    pair = (u, v) if u < v else (v, u)

                    if pair not in edge_data:
                        edge_data[pair] = {"tablets": set(), "relations": set(["co_occurrence"])}
                    edge_data[pair]["tablets"].add(tab.id_text)

        # Populate NetworkX graph
        for (u, v), data in edge_data.items():
            weight = len(data["tablets"])
            if weight >= min_co_occurrences:
                self.graph.add_edge(
                    u,
                    v,
                    weight=weight,
                    tablets=sorted(list(data["tablets"]))[:15],
                    relations=sorted(list(data["relations"])),
                )

        # Add single nodes with high tablet counts even if no co-occurrence meets threshold
        for actor, tabs in actor_tablets.items():
            if actor not in self.graph:
                self.graph.add_node(actor)

        # Compute graph metrics
        degree_dict = dict(self.graph.degree())
        deg_centrality = nx.degree_centrality(self.graph) if len(self.graph) > 0 else {}
        betweenness = nx.betweenness_centrality(self.graph) if len(self.graph) > 0 else {}

        # Detect communities using modularity
        community_map: Dict[str, int] = {}
        if len(self.graph) > 1 and self.graph.number_of_edges() > 0:
            try:
                communities = list(nx.algorithms.community.greedy_modularity_communities(self.graph))
                for comm_id, members in enumerate(communities):
                    for member in members:
                        community_map[member] = comm_id
            except Exception:
                for idx, node in enumerate(self.graph.nodes()):
                    community_map[node] = 0
        else:
            for node in self.graph.nodes():
                community_map[node] = 0

        # Store node metadata
        for node in self.graph.nodes():
            self._node_metadata[node] = {
                "name": node,
                "role": actor_roles.get(node, "official"),
                "tablet_count": len(actor_tablets.get(node, set())),
                "attested_years": sorted(list(actor_years.get(node, set()))),
                "degree": degree_dict.get(node, 0),
                "degree_centrality": round(deg_centrality.get(node, 0.0), 4),
                "betweenness_centrality": round(betweenness.get(node, 0.0), 4),
                "community_id": community_map.get(node, 0),
                "sample_tablets": sorted(list(actor_tablets.get(node, set())))[:6],
            }
            # Set attributes on NetworkX node
            self.graph.nodes[node].update(self._node_metadata[node])

        return self.graph

    def build_network_from_duckdb(
        self,
        db_path: str = "data/processed/nisaba.duckdb",
        min_weight: int = 3,
        max_edges: int = 350,
    ) -> nx.Graph:
        """
        Constructs macro-prosopographic network directly from all 398,000 transactions in DuckDB.
        """
        import duckdb
        con = duckdb.connect(db_path, read_only=True)
        try:
            query = """
                SELECT source_party, receiving_party, count(*) as weight, list(distinct id_text)[:8] as tabs
                FROM transactions
                WHERE source_party != 'Unknown' AND receiving_party != 'Unknown' AND source_party != receiving_party
                GROUP BY source_party, receiving_party
                HAVING count(*) >= ?
                ORDER BY weight DESC
                LIMIT ?
            """
            rows = con.execute(query, [min_weight, max_edges]).fetchall()

            self.graph.clear()
            self._node_metadata.clear()

            node_tablets: Dict[str, Set[str]] = {}
            for u, v, w, tabs in rows:
                self.graph.add_edge(u, v, weight=w, tablets=tabs)
                node_tablets.setdefault(u, set()).update(tabs)
                node_tablets.setdefault(v, set()).update(tabs)

            degree_dict = dict(self.graph.degree())
            deg_centrality = nx.degree_centrality(self.graph) if len(self.graph) > 0 else {}
            betweenness = nx.betweenness_centrality(self.graph) if len(self.graph) > 0 else {}

            community_map: Dict[str, int] = {}
            if len(self.graph) > 1 and self.graph.number_of_edges() > 0:
                try:
                    communities = list(nx.algorithms.community.greedy_modularity_communities(self.graph))
                    for comm_id, members in enumerate(communities):
                        for member in members:
                            community_map[member] = comm_id
                except Exception:
                    for idx, node in enumerate(self.graph.nodes()):
                        community_map[node] = 0
            else:
                for node in self.graph.nodes():
                    community_map[node] = 0

            # Historical chancellery mapping
            bureau_map = {
                "ab-ba-sa6-ga": "Puzrish-Dagan (Livestock Intake)",
                "na-lu5": "Puzrish-Dagan (Disbursement)",
                "in-ta-e3-a": "Puzrish-Dagan (Central Accounting)",
                "ur-szu-ga-lam-ma": "Puzrish-Dagan (Bovine Bureau)",
                "du11-ga": "Puzrish-Dagan (Expenditures)",
                "lu2-kal-la": "Umma (Chancellery Archon)",
                "ensi2-ka": "Umma (Governor Chancellery)",
                "ur-mes": "Ur / Puzrish-Dagan (Seal Bureau)",
                "da-da-ga": "Umma (Finance & Metals)",
            }

            for node in self.graph.nodes():
                # Count total transactions involving this official
                tab_count = con.execute(
                    "SELECT count(distinct id_text) FROM transactions WHERE source_party = ? OR receiving_party = ?",
                    [node, node]
                ).fetchone()[0]

                role = bureau_map.get(node, "Chancellery Administrator")
                self._node_metadata[node] = {
                    "name": node,
                    "role": role,
                    "tablet_count": tab_count,
                    "attested_years": ["Ur III Imperial Period"],
                    "degree": degree_dict.get(node, 0),
                    "degree_centrality": round(deg_centrality.get(node, 0.0), 4),
                    "betweenness_centrality": round(betweenness.get(node, 0.0), 4),
                    "community_id": community_map.get(node, 0),
                    "sample_tablets": sorted(list(node_tablets.get(node, set())))[:6],
                }
                self.graph.nodes[node].update(self._node_metadata[node])

            return self.graph
        finally:
            con.close()

    def get_top_influencers(self, top_n: int = 15) -> List[Dict[str, Any]]:
        """Returns the top central officials ranked by betweenness centrality and degree."""
        nodes = list(self._node_metadata.values())
        nodes.sort(key=lambda x: (x["betweenness_centrality"], x["degree"], x["tablet_count"]), reverse=True)
        return nodes[:top_n]

    def to_cytoscape_json(self, min_weight: int = 1, max_nodes: Optional[int] = 100) -> Dict[str, Any]:
        """
        Exports the prosopographic graph in Cytoscape.js format ({elements: {nodes: [...], edges: [...]}}).
        """
        # Select nodes
        all_nodes = list(self._node_metadata.values())
        all_nodes.sort(key=lambda x: (x["degree"], x["tablet_count"]), reverse=True)
        if max_nodes and len(all_nodes) > max_nodes:
            selected_node_names = {n["name"] for n in all_nodes[:max_nodes]}
        else:
            selected_node_names = set(self._node_metadata.keys())

        cy_nodes = []
        for name in selected_node_names:
            meta = self._node_metadata[name]
            cy_nodes.append({
                "data": {
                    "id": meta["name"],
                    "label": meta["name"],
                    "role": meta["role"],
                    "tablet_count": meta["tablet_count"],
                    "years": ", ".join(meta["attested_years"]) if meta["attested_years"] else "Undated",
                    "degree": meta["degree"],
                    "betweenness": meta["betweenness_centrality"],
                    "community": meta["community_id"],
                    "sample_tablets": meta.get("sample_tablets", []),
                }
            })

        cy_edges = []
        edge_id = 0
        for u, v, data in self.graph.edges(data=True):
            if u in selected_node_names and v in selected_node_names:
                weight = data.get("weight", 1)
                if weight >= min_weight:
                    edge_id += 1
                    cy_edges.append({
                        "data": {
                            "id": f"e{edge_id}",
                            "source": u,
                            "target": v,
                            "weight": weight,
                            "tablets": data.get("tablets", []),
                        }
                    })

        return {
            "elements": {
                "nodes": cy_nodes,
                "edges": cy_edges,
            },
            "summary": {
                "total_nodes": len(cy_nodes),
                "total_edges": len(cy_edges),
                "communities": len({n["data"]["community"] for n in cy_nodes}),
            }
        }

    def to_d3_json(self, min_weight: int = 1, max_nodes: Optional[int] = 100) -> Dict[str, Any]:
        """
        Exports the prosopographic graph in D3 force-directed format ({nodes: [...], links: [...]}).
        """
        cy_data = self.to_cytoscape_json(min_weight=min_weight, max_nodes=max_nodes)
        d3_nodes = [node["data"] for node in cy_data["elements"]["nodes"]]
        d3_links = [
            {
                "source": edge["data"]["source"],
                "target": edge["data"]["target"],
                "value": edge["data"]["weight"],
                "tablets": edge["data"]["tablets"],
            }
            for edge in cy_data["elements"]["edges"]
        ]
        return {
            "nodes": d3_nodes,
            "links": d3_links,
            "summary": cy_data["summary"],
        }
