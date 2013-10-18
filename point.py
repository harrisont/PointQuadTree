import math

class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def distance(self, other_point):
        """
        >>> p = Point(1, 2)
        >>> p.distance(Point(2, 2))
        1.0
        >>> p.distance(Point(4, 6))
        5.0
        >>> p.distance(p)
        0.0
        """
        return math.sqrt((self.x - other_point.x)**2 + (self.y - other_point.y)**2)

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
