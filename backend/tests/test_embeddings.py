import math

from app.services.embeddings import embed_texts


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def test_empty_input_returns_empty_list():
    assert embed_texts([]) == []


def test_returns_one_384_dimension_vector_per_text():
    vectors = embed_texts(["first text", "second text", "third text"])

    assert len(vectors) == 3
    assert all(len(v) == 384 for v in vectors)


def test_vectors_are_normalised():
    vector = embed_texts(["any sentence at all"])[0]

    assert math.isclose(dot(vector, vector), 1.0, abs_tol=1e-4)


def test_similar_texts_score_higher_than_unrelated_ones():
    cat, kitten, tax = embed_texts([
        "A cat sat on the mat.",
        "A kitten is sitting on a rug.",
        "Quarterly tax returns are due in April.",
    ])

    assert dot(cat, kitten) > dot(cat, tax)