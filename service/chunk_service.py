import re
from bs4 import BeautifulSoup
from service.db_service import insert_chunk


def clean_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def chunk_html(html: str, max_chunk_size: int = 2000):
    soup = BeautifulSoup(html, "html.parser")

    # Supprimer scripts et styles
    for tag in soup.find_all(["iframe", "script", "style", "noscript"]):
        tag.decompose()

    chunks = []

    # Trouver tous les éléments structurels
    all_tags = soup.find_all(True)
    sections = [tag for tag in all_tags if is_structural_element(tag)]

    if not sections:
        sections = [soup.body or soup]

    processed = set()

    for sec in sections:
        if sec in processed or any(parent in processed for parent in sec.parents):
            continue

        html_chunk = str(sec)  # <-- conserver tout le HTML du bloc
        if html_chunk.strip():
            chunks.append(html_chunk)
            processed.add(sec)

    return chunks


def is_structural_element(tag):
    """
    Détection intelligente des éléments structurels
    """
    if not tag.name:
        return False

    # 1. Balises standards structurelles
    structural_tags = {
        "article",
        "section",
        "main",
        "aside",
        "nav",
        "header",
        "footer",
        "div",
        "form",
        "fieldset",
        "details",
        "figure",
    }

    if tag.name in structural_tags:
        return True

    # 2. Custom elements (contiennent un tiret)
    if "-" in tag.name:
        return True

    # 3. Éléments avec attributs de rôle structurel
    if tag.get("role") in ["region", "article", "main", "complementary", "navigation"]:
        return True

    # 4. Éléments avec classes suggérant une structure
    classes = tag.get("class", [])
    structural_class_patterns = [
        "container",
        "wrapper",
        "section",
        "block",
        "card",
        "panel",
        "component",
        "widget",
        "module",
        "box",
        "item",
    ]
    if any(
        pattern in " ".join(classes).lower() for pattern in structural_class_patterns
    ):
        return True

    # 5. Éléments avec plusieurs enfants (heuristique)
    direct_children = list(tag.find_all(True, recursive=False))
    if len(direct_children) >= 2:  # Au moins 2 enfants
        return True

    # 6. Éléments avec du texte substantiel ET des enfants
    own_text = "".join(tag.find_all(string=True, recursive=False))
    if len(own_text.strip()) > 70 and len(direct_children) > 0:
        return True

    return False


def chunk_html(html: str, max_chunk_size: int = 2000):
    soup = BeautifulSoup(html, "html.parser")

    # Nettoyer
    for tag in soup.find_all(["iframe", "script", "style", "noscript"]):
        tag.decompose()

    chunks = []

    # Trouver tous les éléments structurels
    all_tags = soup.find_all(True)
    sections = [tag for tag in all_tags if is_structural_element(tag)]

    if not sections:
        sections = [soup.body or soup]

    # Trier : parents avant enfants (par profondeur croissante)
    sections = sorted(sections, key=lambda x: len(list(x.parents)))

    processed = set()

    for sec in sections:
        # Éviter la duplication
        if sec in processed or any(parent in processed for parent in sec.parents):
            continue

        text = clean_text(str(sec))
        if not text:
            continue

        # Stratégie : garder le parent si possible
        if len(text) <= max_chunk_size:
            chunks.append(text)
            processed.add(sec)
        else:
            # Subdiviser en cherchant des enfants structurels
            children = [
                child
                for child in sec.find_all(True, recursive=False)
                if is_structural_element(child) and child not in processed
            ]

            if children:
                # Traiter récursivement les enfants
                for child in children:
                    if child in processed:
                        continue

                    child_text = clean_text(str(child))
                    if not child_text:
                        continue

                    if len(child_text) <= max_chunk_size:
                        chunks.append(child_text)
                    else:
                        # Découpage brutal si vraiment trop grand
                        for i in range(0, len(child_text), max_chunk_size):
                            chunks.append(child_text[i : i + max_chunk_size])

                    processed.add(child)

                processed.add(sec)
            else:
                # Aucun enfant structurel : découpage brutal
                for i in range(0, len(text), max_chunk_size):
                    chunks.append(text[i : i + max_chunk_size])
                processed.add(sec)

    return chunks


def store_chunk(url: str, chunk: str):
    return True
