"""
Profiles PointQuadTree.
"""

from point_quad_tree import PointQuadTree, AxisAlignedBoundingBox, Point
import cProfile
import pstats
import random
import time

NUM_POINTS = 1000
POINT_HALF_SIZE = 0.005

class PointQuadTreeProfileRunner:
    def __init__(self, node_capacity):
        """
        @param node_capacity Integer The node-capacity to use for the PointQuadTree
        """
        boundary = AxisAlignedBoundingBox.positive_quadrant_box(1, 1)
        self._tree = PointQuadTree(boundary=boundary, node_capacity=node_capacity)

    def run(self, seed, num_points):
        """
        @param seed Integer The random-number-generator seed
        @num_points Integer The number of points to use in the profile
        """
        print('Profiling PointQuadTree: node_capacity={}, num_points={}, seed={}.'.format(self._tree._node_capacity, num_points, seed))

        random.seed(seed)

        self._add_random_points(num_points)
        self._query_all_points()
        self._remove_random_points(num_points)
        assert len(self._get_points()) == 0

        self._add_random_points(num_points)
        half_num_points = int(num_points/2)
        self._remove_random_points(half_num_points)
        self._add_random_points(half_num_points)
        assert len(self._get_points()) == num_points

    def _add_random_points(self, num_points):
        for i in range(num_points):
            x = random.random()
            y = random.random()
            self._tree.insert(Point(x, y))

    def _remove_random_points(self, num_points):
        points = self._get_points()
        random.shuffle(points)
        assert num_points <= len(points)
        for i in range(num_points):
            point = points[i]
            self._tree.remove(point)

    def _query_all_points(self):
        for point in self._get_points():
            point_region = AxisAlignedBoundingBox(center=point, half_size=Point(POINT_HALF_SIZE, POINT_HALF_SIZE))
            self._tree.query_points_in_region(point_region)

    def _get_points(self):
        return self._tree.get_all_points()

def run_profile_suite(seed, node_capacity):
    """
    @param seed Integer The random-number-generator seed
    @param node_capacity Integer The node-capacity to use for the PointQuadTree
    """
    runner = PointQuadTreeProfileRunner(node_capacity)
    runner.run(seed, NUM_POINTS)

def profile(seed, node_capacity):
    """
    @param seed Integer The random-number-generator seed
    @param node_capacity Integer The node-capacity to use for the PointQuadTree
    """
    profiler = cProfile.Profile()
    profiler.enable()
    profiler.runcall(run_profile_suite, seed, node_capacity)
    profiler.disable()
    stats_restrictions = 'point_quad_tree.py|axis_aligned_bounding_box.py|point.py'
    pstats.Stats(profiler).strip_dirs().sort_stats('cumulative').print_stats(stats_restrictions, 0.5)

def profile_node_capacities(seed, node_capacities):
    """
    @param seed Integer The random-number-generator seed
    @node_capacities iteratable(Integer) the node capacities to profile
    """
    for node_capacity in node_capacities:
        profile(seed, node_capacity)

def main():
    seed = time.time()
    profile_node_capacities(seed, (1, 4, 20, 100, NUM_POINTS))

def run_tests():
    """
    @return (failure_count, test_count)
    """
    import point_quad_tree
    module_dependencies = [point_quad_tree]

    import sys
    import test
    return test.run_doctests(sys.modules[__name__], module_dependencies)

if __name__ == '__main__':
    failure_count, test_count = run_tests()
    if failure_count == 0:
        main()