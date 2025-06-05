import pytest
from triangle_class import Triangle, IncorrectTriangleSides

# Позитивные тесты
def test_equilateral_triangle():
    t = Triangle(3, 3, 3)
    assert t.triangle_type() == "equilateral"
    assert t.perimeter() == 9

def test_isosceles_triangle():
    t = Triangle(3, 3, 2)
    assert t.triangle_type() == "isosceles"
    assert t.perimeter() == 8

def test_nonequilateral_triangle():
    t = Triangle(3, 4, 5)
    assert t.triangle_type() == "nonequilateral"
    assert t.perimeter() == 12

# Негативные тесты (ожидаем исключение)
@pytest.mark.parametrize("a, b, c", [
    (0, 2, 2),    # нулевая сторона
    (-1, 2, 3),   # отрицательная сторона
    (1, 2, 3),    # нарушение неравенства треугольника
    (5, 1, 1),    # нарушение неравенства треугольника
])
def test_invalid_triangles(a, b, c):
    with pytest.raises(IncorrectTriangleSides):
        Triangle(a, b, c)
