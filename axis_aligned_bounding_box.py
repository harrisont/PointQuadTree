from point import Point

class AxisAlignedBoundingBox:
    """
    Abbreviated as AABB.
    """
    @staticmethod
    def positive_quadrant_box(size_x, size_y):
        """
        >>> box = AxisAlignedBoundingBox.positive_quadrant_box(2, 2)
        >>> box.center
        (1.0,1.0)
        >>> box.half_size
        (1.0,1.0)
        """
        return AxisAlignedBoundingBox(center=Point(size_x/2, size_y/2), half_size=Point(size_x/2, size_y/2))

    def __init__(self, center, half_size):
        """
        @param center Point
        @param half_size Point
        """
        self.center = center
        self.half_size = half_size

    def x_min(self):
        return self.center.x - self.half_size.x

    def x_max(self):
        return self.center.x + self.half_size.x

    def y_min(self):
        return self.center.y - self.half_size.y

    def y_max(self):
        return self.center.y + self.half_size.y

    def contains(self, point):
        """
        >>> box = AxisAlignedBoundingBox(Point(0, 0), Point(2, 2))

        Contains center:
        >>> box.contains(box.center)
        True

        Does not contain:
        >>> box.contains(Point(3, 0))
        False

        Contains a point on the left edge:
        >>> box.contains(Point(-2, 0))
        True

        Contains a point on the right edge:
        >>> box.contains(Point(2, 0))
        True

        Contains a point on the top edge:
        >>> box.contains(Point(0, 2))
        True

        Contains a point on the bottom edge:
        >>> box.contains(Point(0, -2))
        True

        Contains a point on the upper-left corner:
        >>> box.contains(Point(-2, 2))
        True

        Contains a point on the upper-right corner:
        >>> box.contains(Point(2, 2))
        True

        Contains a point on the lower-left corner:
        >>> box.contains(Point(-2, -2))
        True

        Contains a point on the lower-right corner:
        >>> box.contains(Point(2, -2))
        True
        """
        x_min = self.center.x - self.half_size.x
        x_max = self.center.x + self.half_size.x
        y_min = self.center.y - self.half_size.y
        y_max = self.center.y + self.half_size.y

        return (
            (x_min <= point.x <= x_max) and
            (y_min <= point.y <= y_max))

    def intersects(self, other):
        """
        @param other AxisAlignedBoundingBox
        @return true if this intersects the other AABB

        >>> box = AxisAlignedBoundingBox(Point(0, 0), Point(2, 2))

        Does not intersect:
        >>> box.intersects(AxisAlignedBoundingBox(Point(5, 0), Point(2, 2)))
        False

        Intersects itself:
        >>> box.intersects(box)
        True

        Intersects a box it encompases:
        >>> box.intersects(AxisAlignedBoundingBox(Point(0, 0), Point(1, 1)))
        True

        Intersects a box encompasing it:
        >>> box.intersects(AxisAlignedBoundingBox(Point(0, 0), Point(3, 3)))
        True

        Intersects the right edge:
        >>> box.intersects(AxisAlignedBoundingBox(Point(4, 0), Point(2, 2)))
        True

        Intersects the left edge:
        >>> box.intersects(AxisAlignedBoundingBox(Point(-4, 0), Point(2, 2)))
        True

        Intersects the top edge:
        >>> box.intersects(AxisAlignedBoundingBox(Point(0, 4), Point(2, 2)))
        True

        Intersects the bottom edge:
        >>> box.intersects(AxisAlignedBoundingBox(Point(0, -4), Point(2, 2)))
        True

        Intersects the upper-left corner:
        >>> box.intersects(AxisAlignedBoundingBox(Point(-4, 4), Point(2, 2)))
        True

        Intersects the upper-right corner:
        >>> box.intersects(AxisAlignedBoundingBox(Point(4, 4), Point(2, 2)))
        True

        Intersects the lower-left corner:
        >>> box.intersects(AxisAlignedBoundingBox(Point(-4, -4), Point(2, 2)))
        True

        Intersects the lower-right corner:
        >>> box.intersects(AxisAlignedBoundingBox(Point(4, -4), Point(2, 2)))
        True
        """
        assert other is not None

        self_x_min = self.center.x - self.half_size.x
        self_x_max = self.center.x + self.half_size.x
        self_y_min = self.center.y - self.half_size.y
        self_y_max = self.center.y + self.half_size.y

        other_x_min = other.center.x - other.half_size.x
        other_x_max = other.center.x + other.half_size.x
        other_y_min = other.center.y - other.half_size.y
        other_y_max = other.center.y + other.half_size.y

        return (self_x_min <= other_x_max
            and self_x_max >= other_x_min
            and self_y_min <= other_y_max
            and self_y_max >= other_y_min)

    def __repr__(self):
        return "AABB<center={}, half_size={}>".format(self.center, self.half_size)

def run_tests():
    """
    @return (failure_count, test_count)
    """
    import point
    module_dependencies = [point]

    import sys
    import test
    return test.run_doctests(sys.modules[__name__], module_dependencies)

if __name__ == '__main__':
    run_tests()
