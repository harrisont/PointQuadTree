# TODO: Add motion to the points.
# TODO: Add the ability to save/load the current viewer state.
# TODO: Add the ability to change the node-capacity (rebuilding the tree).
# TODO: Add the ability to profile running one iteration of the current main loop.

from point_quad_tree import PointQuadTree, AxisAlignedBoundingBox, Point

import sys
import random
import pygame

QUAD_TREE_NODE_CAPACITY = 20
BOUNDARY_WIDTH, BOUNDARY_HEIGHT = 640, 480

def sign(x):
    """
    @return 1 if x >=0, -1 otherwise
    """
    if x >= 0:
        return 1
    else:
        return -1

class MovingPoint(Point):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.velocity = Point(0, 0)

class PointQuadTreeViewer:
    """
    Displays a PointQuadTree
     - Click to insert a point.
     - Points will randomly be added over time.
    """
    _POINT_RADIUS = 4
    _COLLISION_STATS_FONT_SIZE = 36
    _COLLISION_AREA_RADIUS_MIN = 2 * _POINT_RADIUS
    _COLLISION_AREA_RADIUS_INITIAL = _COLLISION_AREA_RADIUS_MIN
    _COLLISION_AREA_RADIUS_GROWTH_RATE = _POINT_RADIUS
    _RANDOM_POINT_INSERTION_RATE_INITIAL = 0

    _BACKGROUND_COLOR = pygame.Color(0, 0, 0)
    _COLLISION_AREA_STATS_BACKGROUND_COLOR = pygame.Color(0, 0, 0, 150)
    _WHITE_COLOR = pygame.Color(255, 255, 255)
    _RED_COLOR = pygame.Color(255, 0, 0)
    _GREEN_COLOR = pygame.Color(0, 255, 0)
    _COLLISION_LINE_COLOR = pygame.Color(30, 30, 255)

    _KEY_QUIT = pygame.K_ESCAPE
    _KEY_COLLISION_AREA_SHRINK = pygame.K_MINUS
    _KEY_COLLISION_AREA_GROW = pygame.K_EQUALS
    _KEY_TOGGLE_COLLISION_LINES = pygame.K_l
    _KEY_TOGGLE_SUBDIVISION_DISPLAY = pygame.K_SPACE
    _KEY_RANDOM_POINT_INSERTION_RATE_DECREASE = pygame.K_j
    _KEY_RANDOM_POINT_INSERTION_RATE_INCREASE = pygame.K_k
    _KEY_TOGGLE_POINT_MOVEMENT = pygame.K_m
    _KEY_REMOVE_COLLISION_AREA_POINTS = pygame.K_BACKSPACE

    def __init__(self, point_quad_tree):
        """
        @param point_quad_tree PointQuadTree
        """
        self._tree = point_quad_tree

        pygame.init()

        pygame.display.set_caption('PointQuadTree Viewer: node_capacity={}'.format(self._tree._node_capacity))

        self.fpsClock = pygame.time.Clock()

        self._font = pygame.font.Font(None, self._COLLISION_STATS_FONT_SIZE)

        self._random_point_insertion_rate = self._RANDOM_POINT_INSERTION_RATE_INITIAL
        self._random_point_insertion_accumulator = 0

        self._collision_area_points = []
        self._mouse_x = 0
        self._mouse_y = 0
        self._collision_area_radius = self._COLLISION_AREA_RADIUS_INITIAL
        self._collision_lines_visible = True
        self._subdivisions_visible = True
        self._has_point_movement = True

    def run(self):
        self.print_controls()

        self.screen = pygame.display.set_mode(self.size(), pygame.DOUBLEBUF)

        while True:
            self._handle_events()
            self._tick()
            self._draw()

            # Wait long enough to run at 30 FPS.
            self.fpsClock.tick(30)

    def print_controls(self):
        print('Controls:')
        print('\tleft-click: Add point')
        print('\t{}: Remove collision-area points'.format(pygame.key.name(self._KEY_REMOVE_COLLISION_AREA_POINTS)))
        print('\t{}: Toggle subdivision display'.format(pygame.key.name(self._KEY_TOGGLE_SUBDIVISION_DISPLAY)))
        print('\t{}: Toggle collison lines'.format(pygame.key.name(self._KEY_TOGGLE_COLLISION_LINES)))
        print('\t{}: Toggle point movement'.format(pygame.key.name(self._KEY_TOGGLE_POINT_MOVEMENT)))
        print('\t{}/{}: Decrease/increase random-point insertion-rate'.format(
            pygame.key.name(self._KEY_RANDOM_POINT_INSERTION_RATE_DECREASE),
            pygame.key.name(self._KEY_RANDOM_POINT_INSERTION_RATE_INCREASE)))
        print('\t{}/{}: Shrink/grow collision area'.format(
            pygame.key.name(self._KEY_COLLISION_AREA_SHRINK),
            pygame.key.name(self._KEY_COLLISION_AREA_GROW)))
        print('\t{}: Quit'.format(pygame.key.name(self._KEY_QUIT)))

    def _get_points(self):
        return self._tree.get_all_points()

    def size(self):
        """
        @return (boundary_width, boundary_height)
        """
        return (int(2*self._tree.boundary.half_size_x), int(2*self._tree.boundary.half_size_y))

    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == self._KEY_QUIT:
                    pygame.event.post(pygame.event.Event(pygame.QUIT))
                elif event.key == self._KEY_COLLISION_AREA_GROW:
                    self._grow_collision_area(self._COLLISION_AREA_RADIUS_GROWTH_RATE)
                elif event.key == self._KEY_COLLISION_AREA_SHRINK:
                    self._grow_collision_area(-1 * self._COLLISION_AREA_RADIUS_GROWTH_RATE)
                elif event.key == self._KEY_TOGGLE_COLLISION_LINES:
                    self._collision_lines_visible = not self._collision_lines_visible
                elif event.key == self._KEY_TOGGLE_SUBDIVISION_DISPLAY:
                    self._subdivisions_visible = not self._subdivisions_visible
                elif event.key == self._KEY_RANDOM_POINT_INSERTION_RATE_DECREASE:
                    self._change_random_point_insertion_rate(-1)
                elif event.key == self._KEY_RANDOM_POINT_INSERTION_RATE_INCREASE:
                    self._change_random_point_insertion_rate(1)
                elif event.key == self._KEY_REMOVE_COLLISION_AREA_POINTS:
                    self._remove_collision_area_points()
                elif event.key == self._KEY_TOGGLE_POINT_MOVEMENT:
                    self._has_point_movement = not self._has_point_movement
            elif event.type == pygame.MOUSEMOTION:
                mouse_x, mouse_y = event.pos
                self._update_mouse_position(mouse_x, mouse_y)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_x, mouse_y = event.pos
                self._add_point(MovingPoint(mouse_x, mouse_y))

    def _update_mouse_position(self, mouse_x, mouse_y):
        """
        @param mouse_point Point
        """
        self._mouse_x = mouse_x
        self._mouse_y = mouse_y
        self._update_mouse_collision_area_points()

    def _update_mouse_collision_area_points(self):
        self._collision_area_points = self._get_points_in_collision_area_for_point(self._mouse_x, self._mouse_y)

    def _get_points_in_collision_area_for_point(self, x, y):
        """
        @return iteratable(Point) the points in point's collision area
        """
        region = self._get_collision_boundary(x, y)
        return self._tree.query_points_in_region(region)

    def _grow_collision_area(self, amount):
        new_collision_area_radius = max(self._COLLISION_AREA_RADIUS_MIN, self._collision_area_radius + amount)
        if self._collision_area_radius != new_collision_area_radius:
            self._collision_area_radius = new_collision_area_radius
            self._update_mouse_collision_area_points()
            print('Collision-area radius changed to {}.'.format(self._collision_area_radius))

    def _remove_collision_area_points(self):
        for point in self._collision_area_points:
            self._remove_point(point)

    def _change_random_point_insertion_rate(self, amount):
        self._set_random_point_insertion_rate(self._random_point_insertion_rate + amount)

    def _set_random_point_insertion_rate(self, value):
        # Don't remove points if none are left
        if value < 0 and not self._get_points():
            return

        self._random_point_insertion_rate = value
        print('Random-point insertion-rate changed to {}.'.format(self._random_point_insertion_rate))

    def _stop_removing_points_if_none_are_left(self):
        if not self._get_points():
            self._set_random_point_insertion_rate(0)

    def _tick_point_insertion(self):
        self._random_point_insertion_accumulator += self._random_point_insertion_rate
        while abs(self._random_point_insertion_accumulator) >= 1:
            step = sign(self._random_point_insertion_accumulator)
            self._random_point_insertion_accumulator -= step
            if step > 0:
                self._add_random_point()
            else:
                self._remove_random_point()

    def _tick_point_movement(self):
        if self._has_point_movement:
            for point in self._get_points():
                self._move_point(point)

    def _move_point(self, point):
        translate_result = self._tree.translate_point(point, point.velocity.x, point.velocity.y)
        if translate_result == PointQuadTree.TranslatePointResult.removed:
            self._stop_removing_points_if_none_are_left()
        self._update_mouse_collision_area_points()

    def _tick(self):
        self._tick_point_insertion()
        self._tick_point_movement()

    def _add_random_point(self):
        x = random.randint(self._tree.boundary.x_min(), self._tree.boundary.x_max())
        y = random.randint(self._tree.boundary.y_min(), self._tree.boundary.y_max())
        point = MovingPoint(x, y)

        vx_sign = (2 * random.randint(0, 1)) - 1
        vx = random.uniform(1, 5) * vx_sign
        vy_sign = (2 * random.randint(0, 1)) - 1
        vy = random.uniform(1, 5) * vy_sign
        point.velocity.translate(vx, vy)

        self._add_point(point)

    def _add_point(self, point):
        self._tree.insert(point)
        self._update_mouse_collision_area_points()

    def _remove_random_point(self):
        points = self._get_points()
        if not points:
            return

        point = random.choice(points)
        self._remove_point(point)

    def _remove_point(self, point):
        self._tree.remove(point)
        self._update_mouse_collision_area_points()
        self._stop_removing_points_if_none_are_left()

    def _get_mouse_collision_boundary(self):
        return self._get_collision_boundary(self._mouse_x, self._mouse_y)

    def _get_collision_boundary(self, x, y):
        return AxisAlignedBoundingBox(
            center_x=x,
            center_y=y,
            half_size_x=self._collision_area_radius,
            half_size_y=self._collision_area_radius)

    def _draw(self):
        self.screen.fill(self._BACKGROUND_COLOR)

        if self._subdivisions_visible:
            self._draw_tree_partitions(self._WHITE_COLOR)

        if self._collision_lines_visible:
            self._draw_collision_lines(self._COLLISION_LINE_COLOR)

        self._draw_points(self._RED_COLOR)
        self._draw_collision_area_and_points(self._GREEN_COLOR)
        self._draw_collision_area_stats(self._WHITE_COLOR)

        pygame.display.flip()

    def _draw_points(self, color):
        for point in self._get_points():
            self._draw_point(color, point)

    def _draw_point(self, color, point):
        """
        @param point Point
        """
        pygame.draw.circle(self.screen, color, (round(point.x), round(point.y)), self._POINT_RADIUS)

    def _draw_collision_area_and_points(self, color):
        # Highlight the area near the mouse location.
        self._draw_boundry(color, self._get_mouse_collision_boundary(), border_thickness=1)

        # Highlight points near the mouse location.
        for point in self._collision_area_points:
            self._draw_point(color, point)

    def _draw_boundry(self, color, axis_aligned_bounding_box, border_thickness=0):
        """
        @param axis_aligned_bounding_box AxisAlignedBoundingBox
        @border_thickness Integer The border thickness.  Fills if the value is 0.
        """
        center_x = axis_aligned_bounding_box.center_x
        center_y = axis_aligned_bounding_box.center_y
        half_size_x = axis_aligned_bounding_box.half_size_y
        half_size_y = axis_aligned_bounding_box.half_size_y
        rect = (
            center_x - half_size_x,
            center_y - half_size_y,
            2 * half_size_x,
            2 * half_size_y)

        pygame.draw.rect(self.screen, color, rect, border_thickness)

    def _draw_tree_partitions(self, color):
        self._draw_tree_partitions_helper(self._tree, color)

    def _draw_tree_partitions_helper(self, tree, color):
        if not tree._has_subdivided():
            return

        center_x = tree.boundary.center_x
        center_y = tree.boundary.center_y
        pygame.draw.line(self.screen, color, (tree.boundary.x_min(), center_y), (tree.boundary.x_max(), center_y))
        pygame.draw.line(self.screen, color, (center_x, tree.boundary.y_min()), (center_x, tree.boundary.y_max()))

        for subtree in tree._subtree_iterator():
            self._draw_tree_partitions_helper(subtree, color)

    def _draw_collision_area_stats(self, color):
        message_background_surface = pygame.Surface((7*self._COLLISION_STATS_FONT_SIZE, self._COLLISION_STATS_FONT_SIZE))
        message_background_surface = message_background_surface.convert_alpha()
        message_background_surface.fill(self._COLLISION_AREA_STATS_BACKGROUND_COLOR)
        self.screen.blit(message_background_surface, (0, 0))

        message = 'Compare {}/{} points'.format(len(self._collision_area_points), len(self._get_points()))

        message_surface = self._font.render(message, True, color)
        message_rect = message_surface.get_rect()
        message_rect.topleft = (5, 5)
        self.screen.blit(message_surface, message_rect)

    def _draw_collision_lines(self, color):
        for point in self._get_points():
            collision_area_points = self._get_points_in_collision_area_for_point(point.x, point.y)
            for other_point in collision_area_points:
                pygame.draw.line(self.screen, color, (point.x, point.y), (other_point.x, other_point.y), self._POINT_RADIUS)

def view_point_quad_tree(point_quad_tree):
    viewer = PointQuadTreeViewer(point_quad_tree)
    viewer.run()

class DiagnosticPointQuadTree(PointQuadTree):
    def __init__(self, boundary, node_capacity):
        """
        @param boundary AxisAlignedBoundingBox
        @param node_capacity Integer the maximum number of points that each node in the tree can hold
        """
        self.num_points = 0
        super().__init__(boundary, node_capacity)

    def insert(self, point):
        """
        @param point Point
        @return True if the point was inserted, false otherwise (if the point is not in the tree's region)
        """
        self.num_points += 1
        super().insert(point)

def main():
    """
    Animate a PointQuadTree as points are added to it.
    """
    boundary_half_size = Point(BOUNDARY_WIDTH/2, BOUNDARY_HEIGHT/2)
    boundary = AxisAlignedBoundingBox(
        center_x=boundary_half_size.x,
        center_y=boundary_half_size.y,
        half_size_x=boundary_half_size.x,
        half_size_y=boundary_half_size.y)
    tree = DiagnosticPointQuadTree(boundary=boundary, node_capacity=QUAD_TREE_NODE_CAPACITY)

    view_point_quad_tree(tree)

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