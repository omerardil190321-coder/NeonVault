import pygame
import math
from settings import *


# ── helpers ─────────────────────────────────────────────────────────────────

def glow_surf(size, colour, alpha=80):
    """Return a soft circular glow surface."""
    s = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
    for r in range(size, 0, -1):
        a = int(alpha * (r / size) ** 0.5)
        pygame.draw.circle(s, (*colour, a), (size, size), r)
    return s


# ── Platform ────────────────────────────────────────────────────────────────

class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h, moving=False, axis='h'):
        super().__init__()
        self.image = self._make_surf(w, h, moving)
        self.rect  = self.image.get_rect(topleft=(x, y))
        self.moving = moving
        self.axis   = axis
        self.origin = pygame.Vector2(x, y)
        self.speed  = 2
        self.dist   = TILE * 3
        self.t      = 0

    def _make_surf(self, w, h, moving):
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        body_col  = C_MOVE_PLAT   if moving else C_PLATFORM
        edge_col  = C_MOVE_PLAT_E if moving else C_PLATFORM_E
        # body
        pygame.draw.rect(s, body_col, (0, 0, w, h), border_radius=4)
        # top edge glow
        pygame.draw.rect(s, edge_col, (0, 0, w, 3), border_radius=2)
        # grid lines
        for gx in range(0, w, 12):
            pygame.draw.line(s, (*edge_col, 40), (gx, 0), (gx, h))
        return s

    def update(self):
        if not self.moving:
            return
        self.t += self.speed
        off = math.sin(math.radians(self.t)) * self.dist
        if self.axis == 'h':
            self.rect.x = int(self.origin.x + off)
        else:
            self.rect.y = int(self.origin.y + off)


# ── Crystal ─────────────────────────────────────────────────────────────────

class Crystal(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.base_x = x
        self.base_y = y
        self.t      = 0
        self._build()

    def _build(self):
        size = 22
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        cx, cy = size // 2, size // 2
        colour = C_CRYSTAL
        # diamond shape
        pts = [(cx, 2), (cx+8, cy), (cx, size-2), (cx-8, cy)]
        pygame.draw.polygon(self.image, colour, pts)
        pygame.draw.polygon(self.image, C_CRYSTAL2, pts, 2)
        # inner highlight
        pygame.draw.line(self.image, C_WHITE, (cx, 4), (cx+4, cy), 1)
        self.rect = self.image.get_rect(center=(self.base_x, self.base_y))

    def update(self):
        self.t += 2
        self.rect.y = self.base_y + int(math.sin(math.radians(self.t)) * 4)


# ── GlitchDoor ──────────────────────────────────────────────────────────────

class GlitchDoor(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.w  = TILE
        self.h  = TILE * 2
        self.t  = 0
        self.open = False
        self.image = self._make(self.open)
        self.rect  = self.image.get_rect(topleft=(x, y))

    def _make(self, opened):
        s = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        colour = C_DOOR_OPEN if opened else C_DOOR_CLOSED
        glow   = C_NEON_CYAN if opened else C_NEON_PURPLE

        # frame
        pygame.draw.rect(s, colour, (0, 0, self.w, self.h), border_radius=6)
        pygame.draw.rect(s, glow,   (0, 0, self.w, self.h), 3, border_radius=6)

        # glitch stripes
        if opened:
            for i in range(0, self.h, 8):
                alpha = 180 if (i // 8) % 2 == 0 else 60
                pygame.draw.rect(s, (*C_NEON_CYAN, alpha), (4, i, self.w - 8, 4))
        else:
            # lock symbol
            cx = self.w // 2
            pygame.draw.circle(s, glow, (cx, self.h // 2 - 8), 10, 3)
            pygame.draw.rect(s, glow, (cx - 7, self.h // 2 - 6, 14, 12), border_radius=3)

        return s

    def unlock(self):
        self.open  = True
        self.image = self._make(True)

    def update(self):
        if self.open:
            self.t += 3
            # pulse glow handled in draw


# ── Laser ────────────────────────────────────────────────────────────────────

class Laser(pygame.sprite.Sprite):
    def __init__(self, x, y, length=TILE * 3):
        super().__init__()
        self.length = length
        self.t      = 0
        self.active = True
        self.image  = self._make(True)
        self.rect   = self.image.get_rect(topleft=(x, y))

    def _make(self, active):
        w, h = 8, self.length
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        if active:
            pygame.draw.rect(s, C_LASER,      (3, 0, 2, h))
            pygame.draw.rect(s, C_LASER_GLOW, (1, 0, 6, h), border_radius=3)
        return s

    def update(self):
        self.t += 1
        # blink every 90 frames
        if self.t % 90 < 60:
            self.active = True
            self.image  = self._make(True)
        else:
            self.active = False
            self.image  = self._make(False)


# ── Player ───────────────────────────────────────────────────────────────────

class Player(pygame.sprite.Sprite):
    W, H = 28, 40

    def __init__(self, x, y):
        super().__init__()
        self.image  = self._make_frame(False, False)
        self.rect   = self.image.get_rect(topleft=(x, y))

        # physics
        self.vx = 0.0
        self.vy = 0.0
        self.on_ground    = False
        self.jumps_left   = 2     # double jump

        # dash
        self.dashing       = False
        self.dash_timer    = 0
        self.dash_cd       = 0
        self.dash_dir      = 1

        # state
        self.facing        = 1   # 1 right, -1 left
        self.anim_t        = 0
        self.dead          = False
        self.won           = False

        # trail
        self.trail = []

    # ── drawing ──────────────────────────────────────────
    def _make_frame(self, dashing, facing_left):
        s = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        cx = self.W // 2

        # suit body
        suit_col  = C_NEON_PURPLE if not dashing else C_NEON_CYAN
        body_col  = C_PLAYER_BODY
        pygame.draw.rect(s, suit_col,  (cx-8, 14, 16, 20), border_radius=4)
        pygame.draw.rect(s, body_col,  (cx-6, 16, 12, 16), border_radius=3)

        # visor / head
        pygame.draw.ellipse(s, suit_col,  (cx-7, 2, 14, 14))
        pygame.draw.ellipse(s, C_NEON_CYAN, (cx-4, 4, 8, 6))

        # legs
        pygame.draw.rect(s, suit_col, (cx-8, 32, 7, 8),  border_radius=2)
        pygame.draw.rect(s, suit_col, (cx+1, 32, 7, 8),  border_radius=2)

        # arm detail
        arm_x = cx + 8 if not facing_left else cx - 8 - 4
        pygame.draw.rect(s, C_NEON_CYAN, (arm_x, 16, 4, 10), border_radius=2)

        # dash spark
        if dashing:
            for i in range(3):
                sx = cx - 12 - i * 5 if facing_left else cx + 12 + i * 5
                pygame.draw.circle(s, C_NEON_CYAN, (sx, 20), 3 - i)

        return s

    # ── input + update ───────────────────────────────────
    def handle_input(self, keys):
        if self.dead or self.won:
            return

        # horizontal
        self.vx = 0
        if keys[pygame.K_LEFT]:
            self.vx = -PLAYER_SPEED
            self.facing = -1
        if keys[pygame.K_RIGHT]:
            self.vx = PLAYER_SPEED
            self.facing = 1

        # dash (Z or LEFT_SHIFT)
        if (keys[pygame.K_z] or keys[pygame.K_LSHIFT]) and self.dash_cd == 0:
            self.dashing    = True
            self.dash_timer = DASH_DURATION
            self.dash_dir   = self.facing
            self.dash_cd    = DASH_COOLDOWN

    def jump(self):
        if self.dead or self.won:
            return
        if self.jumps_left > 0:
            is_double = self.jumps_left == 1
            self.vy         = DOUBLE_JUMP if is_double else JUMP_FORCE
            self.jumps_left -= 1
            self.on_ground  = False

    def update(self, platforms):
        if self.dead or self.won:
            return

        self.anim_t += 1
        self.dash_cd = max(0, self.dash_cd - 1)

        # dash override
        if self.dashing:
            self.vx         = self.dash_dir * DASH_SPEED
            self.vy         = 0
            self.dash_timer -= 1
            if self.dash_timer <= 0:
                self.dashing = False

        # gravity
        if not self.dashing:
            self.vy += GRAVITY
            self.vy  = min(self.vy, 20)

        # move X
        self.rect.x += int(self.vx)
        self._collide_x(platforms)

        # move Y
        self.rect.y += int(self.vy)
        self.on_ground = False
        self._collide_y(platforms)

        # trail
        self.trail.append(pygame.Vector2(self.rect.centerx, self.rect.centery))
        if len(self.trail) > 8:
            self.trail.pop(0)

        # redraw
        facing_left = self.facing == -1
        self.image  = self._make_frame(self.dashing, facing_left)

        # fell off screen
        if self.rect.top > SCREEN_HEIGHT + 100:
            self.dead = True

    def _collide_x(self, platforms):
        for p in platforms:
            if self.rect.colliderect(p.rect):
                if self.vx > 0:
                    self.rect.right = p.rect.left
                elif self.vx < 0:
                    self.rect.left  = p.rect.right
                self.vx = 0

    def _collide_y(self, platforms):
        for p in platforms:
            if self.rect.colliderect(p.rect):
                if self.vy > 0:
                    self.rect.bottom = p.rect.top
                    self.on_ground   = True
                    self.jumps_left  = 2
                    self.vy          = 0
                elif self.vy < 0:
                    self.rect.top = p.rect.bottom
                    self.vy       = 0

    def draw_trail(self, surface):
        for i, pos in enumerate(self.trail):
            alpha = int(200 * (i / len(self.trail)))
            r     = max(2, int(6 * (i / len(self.trail))))
            gsurf = glow_surf(r + 4, C_NEON_CYAN, alpha // 2)
            surface.blit(gsurf, (int(pos.x) - r - 4, int(pos.y) - r - 4))
