import math
import random
import sys

import pygame

W, H = 900, 600
FPS = 60

PLAYER_SPEED = 260
PLAYER_R = 14
TARGET_R = 16
ENEMY_PROJ_R = 7
PLAYER_PROJ_R = 5
PLAYER_PROJ_SPEED = 560
SHOT_COOLDOWN = 0.22
HIT_DAMAGE = 12
SUPER_GAIN_PER_HIT = 8
SUPER_INVULN_TIME = 0.9

COL_BG = (16, 19, 28)
COL_GRID = (30, 36, 51)
COL_PLAYER = (77, 166, 255)
COL_PLAYER_INVULN = (255, 209, 102)
COL_TARGET = (126, 231, 135)
COL_ENEMY_PROJ = (255, 92, 92)
COL_PLAYER_PROJ = (142, 203, 255)
COL_TEXT = (232, 236, 244)
COL_ACCENT = (255, 209, 102)


def make_target():
    ang = random.uniform(0, math.tau)
    return {
        "x": random.uniform(100, W - 100),
        "y": random.uniform(100, H - 100),
        "vx": math.cos(ang) * 90,
        "vy": math.sin(ang) * 90,
    }


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((W, H))
        pygame.display.set_caption("Arena Trainer")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("arial", 18)
        self.big_font = pygame.font.SysFont("arial", 32, bold=True)
        self.reset()
        self.state = "START"

    def reset(self):
        self.player = {"x": W / 2, "y": H / 2, "hp": 100.0}
        self.enemy_projectiles = []
        self.player_projectiles = []
        self.targets = [make_target(), make_target()]
        self.score = 0
        self.shots_fired = 0
        self.shots_hit = 0
        self.super_meter = 0.0
        self.elapsed = 0.0
        self.spawn_timer = 0.0
        self.last_shot_time = -999.0
        self.invuln_until = 0.0

    def difficulty(self):
        t = self.elapsed
        return {
            "spawn_interval": max(0.28, 0.9 - t * 0.008),
            "proj_speed": 180 + min(160, t * 3),
        }

    def spawn_enemy_projectile(self):
        side = random.randint(0, 3)
        if side == 0:
            x, y = 0, random.uniform(0, H)
        elif side == 1:
            x, y = W, random.uniform(0, H)
        elif side == 2:
            x, y = random.uniform(0, W), 0
        else:
            x, y = random.uniform(0, W), H
        dx, dy = self.player["x"] - x, self.player["y"] - y
        length = math.hypot(dx, dy) or 1
        spd = self.difficulty()["proj_speed"]
        self.enemy_projectiles.append(
            {"x": x, "y": y, "vx": dx / length * spd, "vy": dy / length * spd}
        )

    def try_shoot(self, mouse_pos):
        now = self.elapsed
        if now - self.last_shot_time < SHOT_COOLDOWN:
            return
        self.last_shot_time = now
        self.shots_fired += 1
        dx = mouse_pos[0] - self.player["x"]
        dy = mouse_pos[1] - self.player["y"]
        length = math.hypot(dx, dy) or 1
        self.player_projectiles.append(
            {
                "x": self.player["x"],
                "y": self.player["y"],
                "vx": dx / length * PLAYER_PROJ_SPEED,
                "vy": dy / length * PLAYER_PROJ_SPEED,
            }
        )

    def try_activate_super(self):
        if self.super_meter < 100:
            return
        self.super_meter = 0
        self.score += 50
        self.enemy_projectiles.clear()
        self.invuln_until = self.elapsed + SUPER_INVULN_TIME

    def update(self, dt, keys, mouse_pos):
        self.elapsed += dt

        dx = dy = 0
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            dy -= 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            dy += 1
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dx -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dx += 1
        length = math.hypot(dx, dy)
        if length > 0:
            self.player["x"] += dx / length * PLAYER_SPEED * dt
            self.player["y"] += dy / length * PLAYER_SPEED * dt
        self.player["x"] = max(PLAYER_R, min(W - PLAYER_R, self.player["x"]))
        self.player["y"] = max(PLAYER_R, min(H - PLAYER_R, self.player["y"]))

        diff = self.difficulty()
        self.spawn_timer -= dt
        if self.spawn_timer <= 0:
            self.spawn_enemy_projectile()
            self.spawn_timer = diff["spawn_interval"]

        invuln = self.elapsed < self.invuln_until
        for p in self.enemy_projectiles[:]:
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            if p["x"] < -20 or p["x"] > W + 20 or p["y"] < -20 or p["y"] > H + 20:
                self.enemy_projectiles.remove(p)
                continue
            if not invuln and math.hypot(p["x"] - self.player["x"], p["y"] - self.player["y"]) < ENEMY_PROJ_R + PLAYER_R:
                self.player["hp"] -= HIT_DAMAGE
                self.enemy_projectiles.remove(p)
                if self.player["hp"] <= 0:
                    self.state = "GAMEOVER"
                    return

        for p in self.player_projectiles[:]:
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            if p["x"] < -10 or p["x"] > W + 10 or p["y"] < -10 or p["y"] > H + 10:
                self.player_projectiles.remove(p)
                continue
            for i, t in enumerate(self.targets):
                if math.hypot(p["x"] - t["x"], p["y"] - t["y"]) < PLAYER_PROJ_R + TARGET_R:
                    self.shots_hit += 1
                    self.score += 10
                    self.super_meter = min(100, self.super_meter + SUPER_GAIN_PER_HIT)
                    self.targets[i] = make_target()
                    if p in self.player_projectiles:
                        self.player_projectiles.remove(p)
                    break

        for t in self.targets:
            t["x"] += t["vx"] * dt
            t["y"] += t["vy"] * dt
            if t["x"] < TARGET_R or t["x"] > W - TARGET_R:
                t["vx"] *= -1
            if t["y"] < TARGET_R or t["y"] > H - TARGET_R:
                t["vy"] *= -1
            t["x"] = max(TARGET_R, min(W - TARGET_R, t["x"]))
            t["y"] = max(TARGET_R, min(H - TARGET_R, t["y"]))

    def draw(self, mouse_pos):
        self.screen.fill(COL_BG)
        for x in range(0, W, 45):
            pygame.draw.line(self.screen, COL_GRID, (x, 0), (x, H))
        for y in range(0, H, 45):
            pygame.draw.line(self.screen, COL_GRID, (0, y), (W, y))

        for t in self.targets:
            pygame.draw.circle(self.screen, COL_TARGET, (int(t["x"]), int(t["y"])), TARGET_R)
        for p in self.enemy_projectiles:
            pygame.draw.circle(self.screen, COL_ENEMY_PROJ, (int(p["x"]), int(p["y"])), ENEMY_PROJ_R)
        for p in self.player_projectiles:
            pygame.draw.circle(self.screen, COL_PLAYER_PROJ, (int(p["x"]), int(p["y"])), PLAYER_PROJ_R)

        invuln = self.elapsed < self.invuln_until
        col = COL_PLAYER_INVULN if invuln else COL_PLAYER
        pygame.draw.circle(self.screen, col, (int(self.player["x"]), int(self.player["y"])), PLAYER_R)
        pygame.draw.line(self.screen, (255, 255, 255, 40), (self.player["x"], self.player["y"]), mouse_pos, 1)

        self.draw_hud()

    def draw_hud(self):
        pct = round((self.shots_hit / self.shots_fired) * 100) if self.shots_fired else 0
        lines = [
            f"HP {max(0, round(self.player['hp']))}",
            f"Score {self.score}",
            f"Treffer {self.shots_hit}/{self.shots_fired} ({pct}%)",
            f"Zeit {int(self.elapsed)}s",
            f"Super {round(self.super_meter)}%",
        ]
        x = 10
        for line in lines:
            surf = self.font.render(line, True, COL_TEXT)
            self.screen.blit(surf, (x, 10))
            x += surf.get_width() + 24

    def draw_overlay(self, title, subtitle_lines):
        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((10, 12, 20, 200))
        self.screen.blit(overlay, (0, 0))

        title_surf = self.big_font.render(title, True, COL_ACCENT)
        self.screen.blit(title_surf, (W / 2 - title_surf.get_width() / 2, H / 2 - 120))

        y = H / 2 - 60
        for line in subtitle_lines:
            surf = self.font.render(line, True, COL_TEXT)
            self.screen.blit(surf, (W / 2 - surf.get_width() / 2, y))
            y += 26

        hint = self.font.render("ENTER = Start / Neustart", True, COL_ACCENT)
        self.screen.blit(hint, (W / 2 - hint.get_width() / 2, y + 20))

    def run(self):
        while True:
            dt = min(0.05, self.clock.tick(FPS) / 1000)
            mouse_pos = pygame.mouse.get_pos()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN and self.state in ("START", "GAMEOVER"):
                        self.reset()
                        self.state = "PLAYING"
                    if event.key == pygame.K_SPACE and self.state == "PLAYING":
                        self.try_activate_super()
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN and self.state == "PLAYING":
                    self.try_shoot(mouse_pos)

            if self.state == "PLAYING":
                keys = pygame.key.get_pressed()
                self.update(dt, keys, mouse_pos)

            self.draw(mouse_pos)

            if self.state == "START":
                self.draw_overlay(
                    "Arena Trainer",
                    [
                        "WASD / Pfeiltasten: bewegen & ausweichen",
                        "Maus + Klick: auf Ziel schiessen (vorhalten!)",
                        "Leertaste bei vollem Super-Balken: Super-Blast",
                    ],
                )
            elif self.state == "GAMEOVER":
                pct = round((self.shots_hit / self.shots_fired) * 100) if self.shots_fired else 0
                self.draw_overlay(
                    "Game Over",
                    [
                        f"Score: {self.score}",
                        f"Ueberlebt: {int(self.elapsed)}s",
                        f"Treffgenauigkeit: {pct}%",
                    ],
                )

            pygame.display.flip()


if __name__ == "__main__":
    Game().run()
