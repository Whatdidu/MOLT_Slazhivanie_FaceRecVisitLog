"""
Функции для работы с эмбеддингами (векторами лиц).
"""

import numpy as np
from typing import Sequence


def cosine_similarity(embedding1: Sequence[float], embedding2: Sequence[float]) -> float:
    """
    Вычисляет косинусное сходство между двумя векторами.

    Args:
        embedding1: Первый вектор
        embedding2: Второй вектор

    Returns:
        Сходство от 0.0 до 1.0 (1.0 = идентичные)
    """
    vec1 = np.array(embedding1)
    vec2 = np.array(embedding2)

    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)

    if norm1 == 0 or norm2 == 0:
        return 0.0

    similarity = dot_product / (norm1 * norm2)
    return float(np.clip((similarity + 1) / 2, 0.0, 1.0))


def euclidean_distance(embedding1: Sequence[float], embedding2: Sequence[float]) -> float:
    """
    Вычисляет евклидово расстояние между векторами.

    Args:
        embedding1: Первый вектор
        embedding2: Второй вектор

    Returns:
        Расстояние (меньше = более похожи)
    """
    vec1 = np.array(embedding1)
    vec2 = np.array(embedding2)
    return float(np.linalg.norm(vec1 - vec2))


def find_best_match(
    target_embedding: Sequence[float],
    embeddings_db: list[tuple[int, str, Sequence[float]]],
    threshold: float = 0.55
) -> tuple[int | None, str | None, float]:
    """
    Находит наиболее похожий эмбеддинг в базе.

    Args:
        target_embedding: Вектор для поиска
        embeddings_db: База эмбеддингов [(person_id, name, embedding), ...]
        threshold: Минимальный порог сходства

    Returns:
        (person_id, person_name, similarity) или (None, None, 0.0)
    """
    if not embeddings_db:
        return None, None, 0.0

    best_match_id = None
    best_match_name = None
    best_similarity = 0.0

    for person_id, name, embedding in embeddings_db:
        similarity = cosine_similarity(target_embedding, embedding)
        if similarity > best_similarity:
            best_similarity = similarity
            best_match_id = person_id
            best_match_name = name

    if best_similarity >= threshold:
        return best_match_id, best_match_name, best_similarity

    return None, None, best_similarity


def normalize_embedding(embedding: Sequence[float]) -> list[float]:
    """Нормализует вектор до единичной длины."""
    vec = np.array(embedding)
    norm = np.linalg.norm(vec)
    if norm == 0:
        return list(vec)
    return list(vec / norm)
