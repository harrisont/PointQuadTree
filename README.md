PointQuadTree
=============
An implementation of a quad-tree which stores points.  A quad-tree is a data structure that partitions 2-dimensional space into quadrants recursively.  A tree node subdivides when it contains too many points.

Point-quad-trees are useful for being able to effeciently query for all the points in a given rectangular area.

See http://en.wikipedia.org/wiki/Quadtree#Point_quadtree for more information.

Dependencies
------------
* Python 3
* `pip install --requirement requirements.txt`
    * Pygame

Demo
----
Run point_quad_tree_viewer.py.

Performance Testing
-------------------
Run profile.py.
