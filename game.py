import pygame
import math
import time
from settings import *
from levels  import LEVELS
from sprites import Platform, Crystal, GlitchDoor, Laser, Player, glow_surf


class Game:
    def __init__(self, screen, clock):
        self.screen = screen
        self.clock  = clock
        self.font_big   = pygame.font.SysFont("Consolas", 52, bold=True)
        self.font_med   = pygame.font.SysFont("Consolas", 28, bold=True)
        self.font_small = pygame.font.SysFont("Consolas", 20)

        self.level_index = 0
        self.total_time  = 0.0
        self.level_times = []
        self.best_times  = [None] * len(LEVELS)

        self.state = "menu"   # menu | playing | level_clear | game_over | win

    # ────────────────────────────────────────────────────────────────────────
    def run(self):
        while True:
            dt = self.clock.tick(FPS) / 1000.0
            self._handle_events()
            self._update(dt)
            self._draw()

    # ── events ───────────────────────────────────────────────────────────────
    def _handle_events(self):
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                import sys; sys.exit()

            if ev.type == pygame.KEYDOWN:
                if self.state == "menu":
                    if ev.key == pygame.K_RETURN:
                        self._start_level(0)

                elif self.state == "playing":
                    if ev.key == pygame.K_SPACE:
                        self.player.jump()
                    if ev.key == pygame.K_r:
                        self._start_level(self.level_index)
                    if ev.key == pygame.K_ESCAPE:
                        self.state = "menu"

                elif self.state in ("level_clear", "game_over", "win"):
                    if ev.key == pygame.K_RETURN:
                        if self.state == "level_clear":
                            next_l = self.level_index + 1
                            if next_l < len(LEVELS):
                                self._start_level(next_l)
                            else:
                                self.state = "win"
                        elif self.state == "game_over":
                            self._start_level(self.level_index)
                        elif self.state == "win":
                            self.level_index = 0
                            self.total_time  = 0.0
                            self.state       = "menu"
                    if ev.key == pygame.K_ESCAPE:
                        self.state = "menu"

    # ── level setup ──────────────────────────────────────────────────────────
    def _start_level(self, idx):
        self.level_index = idx
        data = LEVELS[idx]

        self.platforms = pygame.sprite.Group()
        self.crystals  = pygame.sprite.Group()
        self.lasers    = pygame.sprite.Group()
        self.doors     = pygame.sprite.Group()
        self.all_sprites = pygame.sprite.Group()

        self.player   = None
        self.door     = None
        self.crystals_total = 0

        rows = len(data)
        cols = max(len(r) for r in data)

        for row_i, row in enumerate(data):
            col_run = 0
            while col_run < len(row):
                ch = row[col_run]
                x  = col_run * TILE
                y  = row_i   * TILE

                if ch == '#':
                    # count consecutive '#' to merge into one wide platform
                    run = 0
                    while col_run + run < len(row) and row[col_run + run] == '#':
                        run += 1
                    p = Platform(x, y, run * TILE, TILE // 2)
                    self.platforms.add(p)
                    self.all_sprites.add(p)
                    col_run += run
                    continue

                elif ch == 'M':
                    p = Platform(x, y, TILE * 2, TILE // 2, moving=True, axis='h')
                    self.platforms.add(p)
                    self.all_sprites.add(p)

                elif ch == 'V':
                    p = Platform(x, y, TILE * 2, TILE // 2, moving=True, axis='v')
                    self.platforms.add(p)
                    self.all_sprites.add(p)

                elif ch == 'C':
                    c = Crystal(x + TILE // 2, y + TILE // 2)
                    self.crystals.add(c)
                    self.all_sprites.add(c)
                    self.crystals_total += 1

                elif ch == 'D':
                    d = GlitchDoor(x, y - TILE)   # door is 2 tiles tall
                    self.door = d
                    self.doors.add(d)
                    self.all_sprites.add(d)

                elif ch == 'L':
                    l = Laser(x + TILE // 2 - 4, y, TILE * 3)
                    self.lasers.add(l)
                    self.all_sprites.add(l)

                elif ch == 'P':
                    self.player = Player(x, y - (Player.H - TILE // 2))

                col_run += 1

        self.all_sprites.add(self.player)

        # camera offset
        self.cam_x = 0
        self.cam_y = 0

        # timer
        self.level_start = time.time()

        # background stars
        import random
        self.stars = [
            (random.randint(0, SCREEN_WIDTH),
             random.randint(0, SCREEN_HEIGHT),
             random.random())
            for _ in range(120)
        ]

        self.state = "playing"

    # ── update ───────────────────────────────────────────────────────────────
    def _update(self, dt):
        if self.state != "playing":
            return

        keys = pygame.key.get_pressed()
        self.player.handle_input(keys)

        # update moving platforms first
        self.platforms.update()
        self.crystals.update()
        self.lasers.update()
        self.doors.update()

        # pass platform list to player
        self.player.update(list(self.platforms))

        # ── crystal collection ───
        hits = pygame.sprite.spritecollide(self.player, self.crystals, True)

        # ── door unlock ──────────
        if self.door and len(self.crystals) == 0 and not self.door.open:
            self.door.unlock()

        # ── door enter ───────────
        if self.door and self.door.open:
            if self.player.rect.colliderect(self.door.rect):
                elapsed = time.time() - self.level_start
                self.level_times.append(elapsed)
                self.total_time += elapsed
                if (self.best_times[self.level_index] is None or
                        elapsed < self.best_times[self.level_index]):
                    self.best_times[self.level_index] = elapsed
                if self.level_index + 1 >= len(LEVELS):
                    self.state = "win"
                else:
                    self.state = "level_clear"
                return

        # ── laser death ──────────
        for laser in self.lasers:
            if laser.active and self.player.rect.colliderect(laser.rect):
                self.player.dead = True

        # ── death check ──────────
        if self.player.dead:
            self.state = "game_over"

        # ── camera follow ────────
        target_x = self.player.rect.centerx - SCREEN_WIDTH  // 2
        target_y = self.player.rect.centery - SCREEN_HEIGHT // 2
        self.cam_x += (target_x - self.cam_x) * 0.1
        self.cam_y += (target_y - self.cam_y) * 0.1
        self.cam_x  = max(0, self.cam_x)
        self.cam_y  = max(0, self.cam_y)

    # ── draw ─────────────────────────────────────────────────────────────────
    def _draw(self):
        if self.state == "menu":
            self._draw_menu()
        elif self.state == "playing":
            self._draw_game()
        elif self.state == "level_clear":
            self._draw_level_clear()
        elif self.state == "game_over":
            self._draw_game_over()
        elif self.state == "win":
            self._draw_win()
        pygame.display.flip()

    # ── background ───────────────────────────────────────────────────────────
    def _draw_bg(self):
        self.screen.fill(C_BG)
        t = pygame.time.get_ticks()
        for sx, sy, speed in self.stars:
            flicker = int(180 + 75 * math.sin(t * 0.001 * speed * 3))
            col = (flicker, flicker, min(255, flicker + 60))
            pygame.draw.circle(self.screen, col, (sx, sy), 1)

        # scanlines
        for y in range(0, SCREEN_HEIGHT, 4):
            pygame.draw.line(self.screen, (0, 0, 0), (0, y), (SCREEN_WIDTH, y))

    # ── game draw ────────────────────────────────────────────────────────────
    def _draw_game(self):
        self._draw_bg()

        ox, oy = int(self.cam_x), int(self.cam_y)

        # draw player trail
        self.player.draw_trail(self.screen)

        # draw all sprites with camera offset
        for sprite in self.all_sprites:
            if sprite is self.player:
                continue
            self.screen.blit(sprite.image,
                             (sprite.rect.x - ox, sprite.rect.y - oy))

        # door glow when open
        if self.door and self.door.open:
            gx = self.door.rect.centerx - ox
            gy = self.door.rect.centery - oy
            gs = glow_surf(40, C_NEON_CYAN, 60)
            self.screen.blit(gs, (gx - 40, gy - 40))

        # player
        self.screen.blit(self.player.image,
                         (self.player.rect.x - ox, self.player.rect.y - oy))

        # player glow
        gx = self.player.rect.centerx - ox
        gy = self.player.rect.centery - oy
        gs = glow_surf(22, C_NEON_PURPLE, 50)
        self.screen.blit(gs, (gx - 22, gy - 22))

        self._draw_hud()

    # ── HUD ──────────────────────────────────────────────────────────────────
    def _draw_hud(self):
        elapsed = time.time() - self.level_start
        bar_w   = 260

        # dark panel
        pygame.draw.rect(self.screen, C_HUD_BG, (0, 0, bar_w, 50))
        pygame.draw.rect(self.screen, C_NEON_PURPLE, (0, 0, bar_w, 50), 1)

        lvl_txt = self.font_small.render(
            f"LEVEL {self.level_index + 1:02d} / {len(LEVELS):02d}", True, C_NEON_CYAN)
        self.screen.blit(lvl_txt, (10, 6))

        cry_txt = self.font_small.render(
            f"CRYSTALS  {self.crystals_total - len(self.crystals)}/{self.crystals_total}",
            True, C_CRYSTAL)
        self.screen.blit(cry_txt, (10, 27))

        # timer top-right
        tim_txt = self.font_med.render(f"{elapsed:06.2f}s", True, C_NEON_YELLOW)
        self.screen.blit(tim_txt, (SCREEN_WIDTH - tim_txt.get_width() - 10, 10))

        # dash cooldown bar
        if self.player.dash_cd > 0:
            frac = 1 - self.player.dash_cd / DASH_COOLDOWN
            pygame.draw.rect(self.screen, C_HUD_BG,
                             (SCREEN_WIDTH - 120, SCREEN_HEIGHT - 30, 110, 16))
            pygame.draw.rect(self.screen, C_NEON_CYAN,
                             (SCREEN_WIDTH - 120, SCREEN_HEIGHT - 30,
                              int(110 * frac), 16))
            d_txt = self.font_small.render("DASH", True, C_NEON_CYAN)
            self.screen.blit(d_txt, (SCREEN_WIDTH - 120, SCREEN_HEIGHT - 50))

        # controls hint (fades after 5 s)
        if elapsed < 5:
            alpha = int(255 * (1 - elapsed / 5))
            hint = self.font_small.render(
                "← → MOVE   SPACE JUMP   Z/SHIFT DASH   R RESTART",
                True, C_GREY)
            hint.set_alpha(alpha)
            self.screen.blit(hint,
                (SCREEN_WIDTH // 2 - hint.get_width() // 2, SCREEN_HEIGHT - 30))

    # ── overlay helper ───────────────────────────────────────────────────────
    def _overlay(self, alpha=160):
        ov = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        ov.fill((8, 6, 20, alpha))
        self.screen.blit(ov, (0, 0))

    def _neon_text(self, text, font, colour, cx, cy, glow=True):
        surf = font.render(text, True, colour)
        x    = cx - surf.get_width()  // 2
        y    = cy - surf.get_height() // 2
        if glow:
            gs = glow_surf(surf.get_width() // 2, colour, 40)
            self.screen.blit(gs, (x - surf.get_width() // 2,
                                  y - surf.get_height() // 2))
        self.screen.blit(surf, (x, y))

    # ── screens ──────────────────────────────────────────────────────────────
    def _draw_menu(self):
        self.screen.fill(C_BG)
        t = pygame.time.get_ticks() * 0.001

        # animated grid lines
        for i in range(0, SCREEN_WIDTH, 60):
            alpha = int(30 + 20 * math.sin(t + i * 0.05))
            pygame.draw.line(self.screen, (*C_NEON_PURPLE, alpha),
                             (i, 0), (i, SCREEN_HEIGHT))
        for j in range(0, SCREEN_HEIGHT, 60):
            alpha = int(30 + 20 * math.sin(t + j * 0.05))
            pygame.draw.line(self.screen, (*C_NEON_CYAN, alpha),
                             (0, j), (SCREEN_WIDTH, j))

        cx = SCREEN_WIDTH // 2

        # title
        pulse = int(255 * (0.7 + 0.3 * math.sin(t * 2)))
        title_col = (pulse, 20, 200)
        self._neon_text("NEON VAULT", self.font_big, title_col, cx, 160)

        self._neon_text("A CYBERPUNK PLATFORMER",
                        self.font_small, C_NEON_CYAN, cx, 230, glow=False)

        # blink
        if int(t * 2) % 2 == 0:
            self._neon_text("PRESS ENTER TO START",
                            self.font_med, C_NEON_YELLOW, cx, 340)

        # controls
        for i, line in enumerate([
            "← →  MOVE",
            "SPACE  JUMP  (DOUBLE JUMP IN AIR)",
            "Z / SHIFT  DASH",
            "COLLECT ALL CRYSTALS → UNLOCK GLITCH GATE",
        ]):
            self._neon_text(line, self.font_small, C_GREY,
                            cx, 420 + i * 28, glow=False)

    def _draw_level_clear(self):
        self._draw_bg()
        self._overlay()
        elapsed = self.level_times[-1] if self.level_times else 0
        best    = self.best_times[self.level_index]
        cx      = SCREEN_WIDTH // 2
        self._neon_text("LEVEL CLEAR!", self.font_big, C_NEON_GREEN, cx, 180)
        self._neon_text(f"TIME   {elapsed:.2f}s",
                        self.font_med, C_NEON_YELLOW, cx, 270)
        if best is not None:
            self._neon_text(f"BEST   {best:.2f}s",
                            self.font_med, C_NEON_CYAN, cx, 310)
        self._neon_text("PRESS ENTER FOR NEXT LEVEL",
                        self.font_small, C_GREY, cx, 380, glow=False)

    def _draw_game_over(self):
        self.screen.fill(C_BG)
        self._overlay(200)
        cx = SCREEN_WIDTH // 2
        t  = pygame.time.get_ticks() * 0.001
        pulse = int(200 + 55 * math.sin(t * 3))
        self._neon_text("SYSTEM FAILURE", self.font_big,
                        (pulse, 20, 20), cx, 220)
        self._neon_text("YOU FELL INTO THE VOID",
                        self.font_med, C_NEON_ORANGE, cx, 300)
        self._neon_text("ENTER — RESTART    ESC — MENU",
                        self.font_small, C_GREY, cx, 380, glow=False)

    def _draw_win(self):
        self.screen.fill(C_BG)
        cx = SCREEN_WIDTH // 2
        t  = pygame.time.get_ticks() * 0.001

        # rainbow title
        r = int(128 + 127 * math.sin(t))
        g = int(128 + 127 * math.sin(t + 2))
        b = int(128 + 127 * math.sin(t + 4))
        self._neon_text("VAULT CONQUERED!", self.font_big, (r, g, b), cx, 160)

        self._neon_text("ALL 10 LEVELS CLEARED",
                        self.font_med, C_NEON_CYAN, cx, 250)

        total_min = int(self.total_time // 60)
        total_sec = self.total_time % 60
        self._neon_text(f"TOTAL TIME  {total_min:02d}:{total_sec:05.2f}",
                        self.font_med, C_NEON_YELLOW, cx, 300)

        self._neon_text("ENTER — MAIN MENU",
                        self.font_small, C_GREY, cx, 400, glow=False)
