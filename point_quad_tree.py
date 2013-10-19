# TODO: Optimization: add a method to move a point.
#       Currently, a point can be moved by removing it and then re-adding it,
#       but this is unnecessary if the new location is still inside the tree
#       that contains the point

# TODO: Optimization: add an option to have the tree store all its points in leaf nodes.

# TODO: Add cached PointQuadTree, which caches the result of:
#           get_all_points
#           query_points_in_region
#       It should invalidate the caches when any of the following are called:
#           insert
#           remove
#           clear
#           move_point

# TODO: Add AreaQuadTree class that stores areas instead of points.
#       This allows the client to query for areas that are in a region,
#       instead of just being able to query for points that are in a region.

from point import Point
from axis_aligned_bounding_box import AxisAlignedBoundingBox

class PointQuadTree:
    """
    The intended use of PointQuadTree is to create one, add points to it, and then query for ranges.
    It stores the location of points in a rectangular region, subdividing each region when it contains too many points.

    See http://en.wikipedia.org/wiki/Quadtree#Point_quadtree for more information.

    Create a tree whose boundary's lower-left is (0,-4) and lower-right is (16,4).
    >>> tree = PointQuadTree(boundary=AxisAlignedBoundingBox(center=Point(8, 0), half_size_x=8, half_size_y=4), node_capacity=2)
    >>> tree.boundary
    AABB<center=(8,0), half_size=(8,4)>

    Initially contains no points:
    >>> tree.get_all_points()
    []
    >>> tree.query_points_in_region(tree.boundary)
    []

    Fails to insert a point outside of the tree's boundary:
    >>> tree.insert(Point(17, 0))
    False

    >>> tree.insert(Point(7, 1))
    True
    >>> tree.insert(Point(9, 1))
    True
    >>> tree.insert(Point(7, -1))
    True
    >>> tree.get_all_points()
    [(7,1), (9,1), (7,-1)]

    Contains all points in its boundary:
    >>> tree.query_points_in_region(tree.boundary)
    [(7,1), (9,1), (7,-1)]

    Positive-quadrant query:
    >>> tree.query_points_in_region(AxisAlignedBoundingBox.positive_quadrant_box(16, 16))
    [(7,1), (9,1)]

    Size-8 box centered on the origin query:
    >>> tree.query_points_in_region(AxisAlignedBoundingBox(center=Point(0, 0), half_size_x=8, half_size_y=8))
    [(7,1), (7,-1)]

    You can add any type that conforms to the Point interface:
    >>> class ClassImplementingPointInterface:
    ...     def __init__(self, x, y, name):
    ...         self.x = x
    ...         self.y = y
    ...         self.name = name
    ...
    ...     def __repr__(self):
    ...         return "{}:({},{})".format(self.name, self.x, self.y)
    >>> tree = PointQuadTree(boundary=AxisAlignedBoundingBox(center=Point(0, 0), half_size_x=2, half_size_y=2), node_capacity=1)
    >>> obj1 = ClassImplementingPointInterface(0, 0, 'obj1')
    >>> obj2 = ClassImplementingPointInterface(2, 2, 'obj2')
    >>> tree.insert(obj1)
    True
    >>> tree.insert(obj2)
    True
    >>> tree.query_points_in_region(AxisAlignedBoundingBox(center=Point(0, 0), half_size_x=2, half_size_y=2))
    [obj1:(0,0), obj2:(2,2)]
    >>> tree.remove(ClassImplementingPointInterface(0, 0, 'obj1'))  # Points must be equal to be removed.
    False
    >>> tree.remove(obj1)
    True
    >>> tree.query_points_in_region(AxisAlignedBoundingBox(center=Point(0, 0), half_size_x=2, half_size_y=2))
    [obj2:(2,2)]
    >>> tree.remove(obj1)  # Removing a point twice will fail.
    False
    """

    def __init__(self, boundary, node_capacity):
        """
        @param boundary AxisAlignedBoundingBox
        @param node_capacity Integer the maximum number of points that each node in the tree can hold

        node_capacity must be at least 1:
        >>> PointQuadTree(boundary=None, node_capacity=0)
        Traceback (most recent call last):
        AssertionError
        """
        assert node_capacity >= 1

        self.boundary = boundary
        self._node_capacity = node_capacity
        self._points = []
        self._clear_subtrees()

    def get_all_points(self):
        """
        @return an array of all Point's contained in this tree

        >>> tree = PointQuadTree(boundary=AxisAlignedBoundingBox(center=Point(0, 0), half_size_x=3, half_size_y=3), node_capacity=1)
        >>> tree.get_all_points()
        []
        >>> tree.insert(Point(1, 1))
        True
        >>> tree.get_all_points()
        [(1,1)]
        >>> tree.insert(Point(2, 2))
        True
        >>> tree.get_all_points()
        [(1,1), (2,2)]
        >>> tree.get_all_points()
        [(1,1), (2,2)]
        """
        points = self._points.copy()

        # Add the points from the subtrees.
        if self._has_subdivided():
            for subtree in self._subtree_iterator():
                points.extend(subtree.get_all_points())

        return points

    def query_points_in_region(self, region):
        """
        @param region AxisAlignedBoundingBox
        @return an array of Point's in the region
        """
        points_in_region = []

        # If the query region is outside of the boundary, no points are inside it.
        if not self.boundary.intersects(region):
            return points_in_region

        # Query the points in this immediate tree.
        for point in self._points:
            if region.contains_point(point):
                points_in_region.append(point)

        # Query the subtrees.
        if self._has_subdivided():
            for subtree in self._subtree_iterator():
                points_in_region.extend(subtree.query_points_in_region(region))

        return points_in_region

    def insert(self, point):
        """
        @param point Point
        @return True if the point was inserted, false otherwise (if the point is not in the tree's region)

        >>> tree = PointQuadTree(boundary=AxisAlignedBoundingBox(center=Point(0, 0), half_size_x=2, half_size_y=2), node_capacity=1)

        A tree with a node_capacity of will subdivide after 2 insertions.
        >>> p1 = Point(1, 1)
        >>> p2 = Point(2, 2)
        >>> tree.insert(p1)
        True
        >>> tree._points == [p1]
        True
        >>> tree._has_subdivided()
        False
        >>> tree.insert(p2)
        True
        >>> tree._points == [p1]
        True
        >>> tree._has_subdivided()
        True

        ...and the subtrees will have a total of 1 point, which is the ssecond point added.
        >>> subtree_points = []
        >>> for subtree in tree._subtree_iterator(): subtree_points.extend(subtree._points)
        >>> subtree_points == [p2]
        True

        ...and none of the subtrees will have divided.
        >>> any((subtree._has_subdivided() for subtree in tree._subtree_iterator()))
        False
        """
        if not self.boundary.contains_point(point):
            return False

        if len(self._points) < self._node_capacity:
            self._points.append(point)
            return True
        else:
            if not self._has_subdivided():
                self._subdivide()

            for subtree in self._subtree_iterator():
                if subtree.insert(point):
                    return True

            # Could not insert into any subtree.  This should never happen.
            assert False

    def clear(self):
        """
        >>> tree = PointQuadTree(boundary=AxisAlignedBoundingBox(center=Point(0, 0), half_size_x=2, half_size_y=2), node_capacity=1)
        >>> p1 = Point(1, 1)
        >>> p2 = Point(2, 2)
        >>> tree.insert(p1)
        True
        >>> tree.insert(p2)
        True
        >>> tree.clear()
        >>> tree.get_all_points()
        []
        """
        self._points = []
        self._clear_subtrees()

    def remove(self, point):
        """
        @param point Point
        @return True if the point was removed, false otherwise (if the point is not in the tree)

        First add two points and remove the first...
        >>> tree = PointQuadTree(boundary=AxisAlignedBoundingBox(center=Point(0, 0), half_size_x=2, half_size_y=2), node_capacity=1)
        >>> p1 = Point(1, 1)
        >>> p2 = Point(2, 2)
        >>> tree.insert(p1)
        True
        >>> tree.insert(p2)
        True
        >>> tree.remove(p1)
        True
        >>> tree._points == [p2]
        True
        >>> tree._has_subdivided()
        False

        ...then add two points and remove the second.
        >>> tree.clear()
        >>> tree.insert(p1)
        True
        >>> tree.insert(p2)
        True
        >>> tree.remove(p2)
        True
        >>> tree._points == [p1]
        True
        >>> tree._has_subdivided()
        False

        Add some points, then remove them:
        >>> tree = PointQuadTree(boundary=AxisAlignedBoundingBox.positive_quadrant_box(8, 8), node_capacity=1)
        >>> points = []
        >>> for i in range(8):
        ...     point = Point(i, i)
        ...     points.append(point)
        ...     tree.insert(point)
        True
        True
        True
        True
        True
        True
        True
        True
        >>> sorted(tree.get_all_points())
        [(0,0), (1,1), (2,2), (3,3), (4,4), (5,5), (6,6), (7,7)]
        >>> for point in points:
        ...     tree.remove(point)
        ...     sorted(tree.get_all_points())
        True
        [(1,1), (2,2), (3,3), (4,4), (5,5), (6,6), (7,7)]
        True
        [(2,2), (3,3), (4,4), (5,5), (6,6), (7,7)]
        True
        [(3,3), (4,4), (5,5), (6,6), (7,7)]
        True
        [(4,4), (5,5), (6,6), (7,7)]
        True
        [(5,5), (6,6), (7,7)]
        True
        [(6,6), (7,7)]
        True
        [(7,7)]
        True
        []
        """
        assert point

        if not self.boundary.contains_point(point):
            return False

        if point in self._points:
            self._remove_from_self(point)
            return True
        elif self._has_subdivided():
            point_was_removed = self._remove_from_subtree(point)
            if point_was_removed:
                self._remove_empty_subtrees()
            return point_was_removed
        else:
            return False

    class TranslatePointResult:
        translated = 1
        out_of_bounds = 2
        not_in_tree = 3
        removed = 4

    def translate_point(self, point, x, y):
        """
        This has the same behavior as, but is more efficient than, removing the point and then
        re-adding it at the new location.

        If the translated position is outside the tree's boundary, the point will be removed.

        @param point Point
        @param x, y Number The amount to translate the point by.
        @return TranslatePointResult

        Attempt to translate a point not in the tree:
        >>> tree = PointQuadTree(boundary=AxisAlignedBoundingBox(center=Point(0, 0), half_size_x=1, half_size_y=1), node_capacity=1)
        >>> tree.translate_point(Point(0, 0), x=1, y=1) == PointQuadTree.TranslatePointResult.not_in_tree
        True

        Attempt to translate an out of bounds point:
        >>> tree = PointQuadTree(boundary=AxisAlignedBoundingBox(center=Point(0, 0), half_size_x=1, half_size_y=1), node_capacity=1)
        >>> tree.translate_point(Point(2, 2), x=1, y=1) == PointQuadTree.TranslatePointResult.out_of_bounds
        True

        Translate a point to a new position in the same node:
        >>> tree = PointQuadTree(boundary=AxisAlignedBoundingBox(center=Point(0, 0), half_size_x=2, half_size_y=2), node_capacity=1)
        >>> p1 = Point(1, 1)
        >>> tree.insert(p1)
        True
        >>> tree.translate_point(p1, 1, 1) == PointQuadTree.TranslatePointResult.translated
        True
        >>> tree.get_all_points()
        [(2,2)]
        >>> tree._has_subdivided()
        False

        Translate a point such that its new position is out of the tree:
        >>> tree = PointQuadTree(boundary=AxisAlignedBoundingBox(center=Point(0, 0), half_size_x=1, half_size_y=1), node_capacity=1)
        >>> p1 = Point(1, 1)
        >>> tree.insert(p1)
        True
        >>> tree.translate_point(p1, 1, 1) == PointQuadTree.TranslatePointResult.removed
        True
        >>> tree.get_all_points()
        []

        Translate a deep point:
        >>> tree = PointQuadTree(boundary=AxisAlignedBoundingBox(center=Point(0, 0), half_size_x=3, half_size_y=3), node_capacity=1)
        >>> p1 = Point(1, 1)
        >>> p2 = Point(2, 2)
        >>> p3 = Point(3, 3)
        >>> tree.insert(p1)
        True
        >>> tree.insert(p2)
        True
        >>> tree.insert(p3)
        True
        >>> tree.translate_point(p3, -6, -6) == PointQuadTree.TranslatePointResult.translated
        True
        >>> tree.get_all_points()
        [(1,1), (2,2), (-3,-3)]

        Translate a deep point such that its new position is out of the tree:
        >>> tree = PointQuadTree(boundary=AxisAlignedBoundingBox(center=Point(0, 0), half_size_x=3, half_size_y=3), node_capacity=1)
        >>> p1 = Point(1, 1)
        >>> p2 = Point(2, 2)
        >>> p3 = Point(3, 3)
        >>> tree.insert(p1)
        True
        >>> tree.insert(p2)
        True
        >>> tree.insert(p3)
        True
        >>> tree.translate_point(p3, 1, 1) == PointQuadTree.TranslatePointResult.removed
        True
        >>> tree.get_all_points()
        [(1,1), (2,2)]
        """
        assert point

        if not self.boundary.contains_point(point):
            return PointQuadTree.TranslatePointResult.out_of_bounds
        elif point in self._points:
            return self._translate_point_in_self(point, x, y)
        elif self._has_subdivided():
            return self._translate_point_in_subtree(point, x, y)
        else:
            return PointQuadTree.TranslatePointResult.not_in_tree

    def _remove_from_self(self, point):
        """
        Remove point from this node and bubble up a point from a subtree
        in order to keep the nodes at the top of the tree full.

        @param point Point
        """
        self._points.remove(point)
        self._bubble_up_point()

    def _remove_from_subtree(self, point):
        """
        @param point Point
        @return True if the point was removed, false otherwise (if the point is not in the tree)
        """
        for subtree in self._subtree_iterator():
            if subtree.remove(point):
                return True
        return False

    def _bubble_up_point(self):
        """
        Removes a point from a leaf node and adds it to the current node.
        """
        removed_point = self._remove_from_leaf()
        if removed_point:
            self._points.append(removed_point)

    def _remove_from_leaf(self):
        """
        Remove a point from a leaf node and return it.
        If all subtrees are then empty, remove them.
        @return the removed point
        """
        if self._has_subdivided():
            return self._remove_from_subtree_leaf()
        else:
            return None

    def _remove_from_subtree_leaf(self):
        """
        Remove a point from a subtree leaf node and return it.
        If all subtrees are then empty, remove them.
        @return the removed point
        """
        if self._has_subdivided():
            for subtree in self._subtree_iterator():
                removed_point = subtree._remove_from_subtree_leaf()
                if removed_point:
                    self._remove_empty_subtrees()
                    return removed_point
            return None
        else:
            return self._pop_point()

    def _pop_point(self):
        """
        Removes and returns the first point from self._points.
        @return the removed point, or None if there are no points.
        """
        if self._points:
            return self._points.pop(0)
        else:
            return None

    def _translate_point_in_self(self, point, x, y):
        if self.boundary.contains(point.x + x, point.y + y):
            point.translate(x, y)
            return PointQuadTree.TranslatePointResult.translated
        else:
            self.remove(point)
            self._remove_empty_subtrees()
            point.translate(x, y)
            return PointQuadTree.TranslatePointResult.removed

    def _translate_point_in_subtree(self, point, x, y):
        for subtree in self._subtree_iterator():
            translate_result = subtree.translate_point(point, x, y)
            if translate_result == PointQuadTree.TranslatePointResult.out_of_bounds:
                # Continue on to the next subtree.
                continue
            elif (translate_result == PointQuadTree.TranslatePointResult.translated or
                translate_result == PointQuadTree.TranslatePointResult.not_in_tree):
                return translate_result
            elif translate_result == PointQuadTree.TranslatePointResult.removed:
                # The point is already translated.
                if self.boundary.contains_point(point):
                    self.insert(point)
                    return PointQuadTree.TranslatePointResult.translated
                else:
                    return PointQuadTree.TranslatePointResult.removed
            else:
                # All the TranslatePointResult values should have been handled.
                assert false

        # The point was not found in any of the subtrees.
        return PointQuadTree.TranslatePointResult.not_in_tree

    def _remove_empty_subtrees(self):
        if not self._has_subtree_points():
            self._clear_subtrees()

    def _subdivide(self):
        for (subtree_index, factor_x, factor_y) in self._subtree_quadrant_iterator():
            self._set_subtree(subtree_index, self._create_subdivision(factor_x, factor_y))
        assert self._has_subdivided()

    def _create_subdivision(self, factor_x, factor_y):
        """
        @param factor_x Number {-1, 1}
        @param factor_y Number {-1, 1}
        """
        return PointQuadTree(
            boundary=self._calculate_subdivision_boundary(factor_x, factor_y),
            node_capacity=self._node_capacity)

    def _calculate_subdivision_boundary(self, factor_x, factor_y):
        """
        @param factor_x Number {-1, 1}
        @param factor_y Number {-1, 1}

        >>> tree = PointQuadTree(boundary=AxisAlignedBoundingBox(center=Point(1, 0), half_size_x=2, half_size_y=2), node_capacity=1)
        >>> tree._calculate_subdivision_boundary(1, 1)
        AABB<center=(2.0,1.0), half_size=(1.0,1.0)>
        >>> tree._calculate_subdivision_boundary(-1, -1)
        AABB<center=(0.0,-1.0), half_size=(1.0,1.0)>
        """
        subdivision_half_size_x = self.boundary.half_size_x / 2
        subdivision_half_size_y = self.boundary.half_size_y / 2
        subdivision_center = self._calculate_subdivision_center(subdivision_half_size_x, subdivision_half_size_y, factor_x, factor_y)
        return AxisAlignedBoundingBox(subdivision_center, subdivision_half_size_x, subdivision_half_size_y)

    def _calculate_subdivision_center(self, subdivision_half_size_x, subdivision_half_size_y, factor_x, factor_y):
        """
        @param subdivision_half_size Number
        @param factor_x Number {-1, 1}
        @param factor_y Number {-1, 1}
        """
        return Point(
            self.boundary.center.x + (factor_x * subdivision_half_size_x),
            self.boundary.center.y + (factor_y * subdivision_half_size_y))

    def _has_subdivided(self):
        return any(self._subtree_iterator())

    def _has_subtree_points(self):
        return any((len(subtree._points) for subtree in self._subtree_iterator() if subtree))

    def _clear_subtrees(self):
        for (subtree_index, factor_x, factor_y) in self._subtree_quadrant_iterator():
            self._set_subtree(subtree_index, None)

    def _set_subtree(self, subtree_index, new_subtree):
        # Upper-left, upper-right, lower-left, and lower-right subtrees
        if subtree_index == 0:
            self._subtree_ul = new_subtree
        elif subtree_index == 1:
            self._subtree_ur = new_subtree
        elif subtree_index == 2:
            self._subtree_ll = new_subtree
        elif subtree_index == 3:
            self._subtree_lr = new_subtree

    def _subtree_iterator(self):
        """
        @return each subtree
        """
        yield self._subtree_ul
        yield self._subtree_ur
        yield self._subtree_ll
        yield self._subtree_lr

    def _subtree_quadrant_iterator(self):
        """
        @return (subtree_index, factor_x, factor_y) for each subtree
        """
        yield 0, -1, +1
        yield 1, +1, +1
        yield 2, -1, -1
        yield 3, +1, -1

def run_tests():
    """
    @return (failure_count, test_count)
    """
    import axis_aligned_bounding_box
    module_dependencies = [axis_aligned_bounding_box]

    import sys
    import test
    return test.run_doctests(sys.modules[__name__], module_dependencies)

if __name__ == '__main__':
    run_tests()
