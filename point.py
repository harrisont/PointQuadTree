import math

class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def magnitude(self):
        """
        >>> Point(3, 4).magnitude()
        5.0
        >>> Point(-5, -12).magnitude()
        13.0
        """
        return math.sqrt(self.magnitude_squared())

    def magnitude_squared(self):
        """
        >>> Point(3, 4).magnitude_squared()
        25
        >>> Point(-5, -12).magnitude_squared()
        169
        """
        return self.x**2 + self.y**2

    def distance(self, other_point):
        """
        >>> p = Point(1, 2)
        >>> p.distance(Point(2, 2))
        1.0
        >>> p.distance(Point(4, 6))
        5.0
        >>> p.distance(Point(-3, -1))
        5.0
        >>> p.distance(p)
        0.0
        """
        return math.sqrt(self.distance_squared(other_point))

    def distance_squared(self, other_point):
        """
        >>> p = Point(1, 2)
        >>> p.distance_squared(Point(2, 2))
        1
        >>> p.distance_squared(Point(4, 6))
        25
        >>> p.distance_squared(Point(-3, -1))
        25
        >>> p.distance_squared(p)
        0
        """
        return (self.x - other_point.x)**2 + (self.y - other_point.y)**2



    def __lt__(self, other):
        """
        >>> Point(1, 0) < Point(0, 2)
        False
        >>> Point(1, 0) < Point(2, 0)
        True
        >>> Point(1, 0) < Point(1, 0)
        False
        >>> Point(1, 0) < Point(1, 1)
        True
        """
        diff_x = self.x - other.x
        if diff_x != 0:
            return diff_x < 0

        return self.y < other.y

    def __repr__(self):
        return "({},{})".format(self.x, self.y)

def run_tests():
    """
    @return (failure_count, test_count)
    """
    import sys
    import test
    return test.run_doctests(sys.modules[__name__])

if __name__ == '__main__':
    run_tests()
