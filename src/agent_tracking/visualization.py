from typing import Optional
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from git import Repo
from radon.visitors import ComplexityVisitor
from pathlib import Path


def analyze_local_codebase(path: str = ".") -> pd.DataFrame:
    """Analyse le code source réel pour extraire Churn, Complexité et LOC."""
    try:
        repo = Repo(path, search_parent_directories=True)
    except:
        repo = None
    project_dir = Path(path)
    results = []

    # On ne scanne que les fichiers Python qui ne sont pas dans des dossiers cachés ou venv
    files = [
        f
        for f in project_dir.rglob("*.py")
        if not any(part.startswith(".") or part == "venv" for part in f.parts)
    ]

    for file_path in files:
        relative_path = file_path.relative_to(project_dir)

        # 1. Calcul de la Complexité (Radon)
        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read()
            try:
                visitor = ComplexityVisitor.from_code(code)
                complexity = sum(
                    [m.complexity for m in visitor.functions + visitor.classes]
                ) / (len(visitor.functions + visitor.classes) or 1)
                loc = len(code.splitlines())
            except:
                continue  # Ignore les fichiers avec erreurs de syntaxe

        # 2. Calcul du Churn (Git)
        # Nombre de commits impliquant ce fichier
        try:
            if repo:
                git_relative = file_path.relative_to(repo.working_dir)
                commits = list(repo.iter_commits(paths=git_relative))
                churn = len(commits)
            else:
                churn = 0
        except:
            churn = 0

        results.append(
            {
                "filename": str(relative_path),
                "churn": churn,
                "complexity": complexity,
                "loc": loc,
            }
        )

    return pd.DataFrame(results)


def generate_hotspot_scatter(
    df: pd.DataFrame, save_path: Optional[Path | str] = None, show: bool = True
):
    """
    Affiche la matrice de risque et permet l'export en image.
    Haut-Droite = Hotspots (Code complexe souvent modifié = Danger)
    """
    plt.figure(figsize=(12, 8))

    # Taille bulle proportionnelle au volume de code (LOC)
    # On normalise un peu pour éviter des bulles géantes ou invisibles
    bubble_size = (df["loc"] / df["loc"].max()) * 1000 + 100

    scatter = plt.scatter(
        df["churn"],
        df["complexity"],
        s=bubble_size,
        c=df["complexity"],
        cmap="Reds",
        alpha=0.6,
        edgecolors="w",
    )

    # Identification des fichiers critiques (Top 5)
    top_risk = df.sort_values(by=["churn", "complexity"], ascending=False).head(5)
    for _, row in top_risk.iterrows():
        plt.text(
            row["churn"],
            row["complexity"],
            row["filename"],
            fontsize=9,
            fontweight="bold",
        )

    # Lignes de démarcation (médianes) pour créer les quadrants
    plt.axhline(df["complexity"].median(), color="gray", linestyle="--", alpha=0.5)
    plt.axvline(df["churn"].median(), color="gray", linestyle="--", alpha=0.5)

    plt.title("Analyse des Hotspots (Réel)", fontsize=15)
    plt.xlabel("Nombre de modifications (Churn Git)")
    plt.ylabel("Complexité Cyclomatique Moyenne")
    plt.colorbar(scatter, label="Intensité de complexité")

    # Gestion de l'export
    if save_path:
        # ensure_ascii=False n'est pas nécessaire ici, mais bbox_inches='tight'
        # permet d'éviter que les labels soient coupés
        plt.savefig(save_path, bbox_inches="tight", dpi=300)
        print(f"Graphique sauvegardé sous : {save_path}")

    if show:
        plt.show()
    else:
        plt.close()  # Libère la mémoire si on n'affiche pas
