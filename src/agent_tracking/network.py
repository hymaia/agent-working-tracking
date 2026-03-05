import ast
import os
from pathlib import Path
from pyvis.network import Network
from pathlib import Path


class GlobalProjectAnalyzer:
    def __init__(self, root_dir, output_dir):
        self.root_dir = Path(root_dir)
        self.output_dir = Path(output_dir)
        self.nodes = {}  # Nom -> {type, file}
        self.edges = set()  # Set de tuples (Source, Cible) pour éviter les doublons
        self.all_defined_targets = set()

    def scan_project(self):
        """Premier passage : Indexer toutes les définitions"""
        for py_file in self.root_dir.rglob("*.py"):
            with open(py_file, "r", encoding="utf-8") as f:
                try:
                    tree = ast.parse(f.read())
                    for node in ast.walk(tree):
                        if isinstance(
                            node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
                        ):
                            self.nodes[node.name] = {
                                "type": "function"
                                if not isinstance(node, ast.ClassDef)
                                else "class",
                                "file": py_file.name,
                            }
                            self.all_defined_targets.add(node.name)
                except Exception as e:
                    print(f"Erreur lecture {py_file}: {e}")

    def analyze_interactions(self):
        """Second passage : Mapper les appels entre les fichiers"""
        for py_file in self.root_dir.rglob("*.py"):
            with open(py_file, "r", encoding="utf-8") as f:
                try:
                    tree = ast.parse(f.read())
                    current_scope = None

                    for node in ast.walk(tree):
                        # On change de scope quand on entre dans une fonction/classe
                        if isinstance(
                            node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
                        ):
                            current_scope = node.name

                        # On cherche les appels de fonctions
                        if isinstance(node, ast.Call) and current_scope:
                            target = None
                            if isinstance(node.func, ast.Name):
                                target = node.func.id
                            elif isinstance(node.func, ast.Attribute):
                                target = node.func.attr

                            if (
                                target in self.all_defined_targets
                                and target != current_scope
                            ):
                                self.edges.add((current_scope, target))
                except:
                    continue

    def generate_graph(self):
        net = Network(
            height="900px",
            width="100%",
            bgcolor="#0f172a",
            font_color="white",
            directed=True,
        )
        net.force_atlas_2based()

        # Ajouter les nœuds avec des couleurs par fichier pour s'y retrouver
        files = list(set(info["file"] for info in self.nodes.values()))
        colors = ["#38bdf8", "#fbbf24", "#f87171", "#34d399", "#a78bfa", "#f472b6"]
        file_color_map = {file: colors[i % len(colors)] for i, file in enumerate(files)}

        for name, info in self.nodes.items():
            net.add_node(
                name,
                label=name,
                color=file_color_map[info["file"]],
                title=f"Fichier: {info['file']}\nType: {info['type']}",
            )

        for source, target in self.edges:
            net.add_edge(source, target, color="#64748b")

        # chemin du fichier
        output_file = self.output_dir / "project_interaction_map.html"

        # PyVis attend une string
        net.show(str(output_file), notebook=False)

        print(f"🚀 Carte globale générée dans '{output_file}'")
