import pygame
import random
import math
import time
import sys

# --- КОНФИГУРАЦИЯ ---
WIDTH, HEIGHT = 1600, 900
FPS = 30
BG_COLOR = (2, 2, 8)
GRID_COLOR = (10, 35, 35) 
BASE_ZONE = pygame.Rect(30, 30, 250, 250)
SIDE_PANEL = pygame.Rect(1250, 0, 350, HEIGHT)

REPRO_AGE = 420  
MIN_LIFE, MAX_LIFE = 700, 900
ACID_COLORS = [(0, 255, 150), (200, 255, 0), (0, 200, 255), (255, 100, 0), (255, 0, 200)]

RES_TYPES = {
    'BIO':   {'color': (0, 200, 120), 'hp': 45, 'lvl': 0.1, 'name': 'Био-масса'},
    'NRG':   {'color': (0, 120, 200), 'hp': 15, 'lvl': 1.0, 'name': 'Энергия'},
    'RARE':  {'color': (180, 40, 220), 'hp': 70, 'lvl': 2.0, 'name': 'Изотоп'}
}

WEAPON_TYPES = {
    'LASER':   {'color': (255, 255, 255), 'cd': 15, 'speed': 14, 'dmg': 15, 'label': 'Лазер'},
    'PLASMA':  {'color': (255, 100, 255), 'cd': 45, 'speed': 8, 'dmg': 45, 'label': 'Плазма'},
    'RAIL':    {'color': (255, 200, 0),   'cd': 60, 'speed': 25, 'dmg': 120, 'label': 'Рельса'}
}

FORM_MODS = {
    'circle': {'hp': 80, 'speed': 0.8, 'armor': 1.0, 'cd': 1.0, 'label': 'РАЗВЕДЧИК'},
    'rect':   {'hp': 100, 'speed': 0.6, 'armor': 0.6, 'cd': 1.0, 'label': 'ТАНК'},
    'poly':   {'hp': 100, 'speed': 0.9, 'armor': 1.0, 'cd': 0.8, 'label': 'ШТУРМОВИК'}
}

WORLD_STATS = {"res_coll": 0, "en_killed": 0, "born": 1, "history": []}
THOUGHT_POOL = ["Анализ", "Дрейф", "Охота", "Связь", "Сон", "Цель найдена", "Защита"]

class SimpleBrain:
    def __init__(self, weights=None):
        self.w = weights if weights else [[random.uniform(-1, 1) for _ in range(7)] for _ in range(2)]
    def predict(self, inputs):
        return [math.tanh(sum(i * w for i, w in zip(inputs, row))) for row in self.w]
    def mutate(self):
        return SimpleBrain([[v + random.uniform(-0.1, 0.1) for v in r] for r in self.w])

class Shape:
    def __init__(self, x=None, y=None, brain=None, gen=1, color=None, form=None, start_lvl=1.0):
        self.x, self.y = x or random.randint(50, 250), y or random.randint(50, 250)
        self.brain = brain or SimpleBrain()
        self.gen, self.name = gen, f"УЗЕЛ-{random.randint(100,999)}"
        if color:
            if random.random() < 0.1: self.color = random.choice(ACID_COLORS)
            else: self.color = tuple(max(0, min(255, color[i] + random.randint(-45, 45))) for i in range(3))
        else: self.color = random.choice(ACID_COLORS)
        if form and random.random() > 0.3: self.form = form
        else: self.form = random.choice(['circle', 'rect', 'poly'])
        self.mods = FORM_MODS[self.form]
        self.angle = random.uniform(0, 2*math.pi)
        self.hp = float(self.mods['hp'])
        self.spawn_time = time.time()
        self.lifetime = random.randint(MIN_LIFE, MAX_LIFE)
        self.weapon, self.shoot_cd, self.lvl = 'LASER', 0, start_lvl
        self.thought, self.t_timer = random.choice(THOUGHT_POOL), time.time()
        self.group_bonus = 1.0
        self.target_line = None

    def update(self, resources, weapons_on_ground, enemies, bullets, others):
        self.shoot_cd = max(0, self.shoot_cd - 1)
        if time.time() - self.t_timer > 5:
            self.thought, self.t_timer = random.choice(THOUGHT_POOL), time.time()
        conn = 0
        for o in others:
            if o != self:
                diff = sum(abs(self.color[i] - o.color[i]) for i in range(3))
                if diff < 100 and math.hypot(self.x-o.x, self.y-o.y) < 140: conn += 1
        self.group_bonus = 1.0 + (conn * 0.1)
        r_ang, r_dist = 0, 1.0
        all_t = resources + weapons_on_ground + enemies
        target = min(all_t, key=lambda t: math.hypot(self.x-t['x'], self.y-t['y'])) if all_t else None
        if target:
            self.target_line = (target['x'], target['y'])
            t_ang = math.atan2(target['y'] - self.y, target['x'] - self.x)
            r_ang = ((t_ang - self.angle + math.pi) % (2 * math.pi) - math.pi) / math.pi
            r_dist = math.hypot(self.x - target['x'], self.y - target['y']) / 1000
        else: self.target_line = None
        p = self.brain.predict([self.x/1250, self.y/900, self.hp/self.mods['hp'], r_ang, r_dist, len(enemies)/5, 0.5])
        self.angle += (p[0] * 0.12) + (r_ang * 0.05)
        spd = 1.8 * self.mods['speed'] * (p[1] + 1.2) * (1.0 + self.lvl * 0.02)
        self.x += math.cos(self.angle) * spd
        self.y += math.sin(self.angle) * spd
        if self.shoot_cd == 0:
            for e in enemies:
                if math.hypot(self.x-e['x'], self.y-e['y']) < 400:
                    self.fire(bullets, math.atan2(e['y']-self.y, e['x']-self.x)); break
        self.x, self.y = max(30, min(self.x, 1220)), max(30, min(self.y, 870))

    def fire(self, bullets, angle):
        cfg = WEAPON_TYPES[self.weapon]
        bullets.append({'x': self.x, 'y': self.y, 'angle': angle, 'color': cfg['color'], 'speed': cfg['speed'], 'dmg': cfg['dmg']*(1.0+self.lvl*0.05)*self.group_bonus, 'alive': True})
        self.shoot_cd = cfg['cd'] * self.mods['cd']

    def draw(self, screen, f, is_sel):
        cx, cy, sz = int(self.x), int(self.y), int(12 + min(10, self.lvl // 2))
        age = int(time.time() - self.spawn_time)
        if self.target_line: pygame.draw.line(screen, (self.color[0]//5, self.color[1]//5, self.color[2]//5), (cx, cy), self.target_line, 1)
        screen.blit(f.render(f"{self.thought} | {age}с", True, (160, 160, 160)), (cx-30, cy-sz-25))
        pygame.draw.rect(screen, (30, 30, 40), (cx-15, cy-sz-8, 30, 3))
        pygame.draw.rect(screen, self.color, (cx-15, cy-sz-8, int(30 * (self.hp/self.mods['hp'])), 3))
        if is_sel: pygame.draw.circle(screen, (255, 255, 255), (cx, cy), sz+10, 1)
        if self.form == 'circle': pygame.draw.circle(screen, self.color, (cx, cy), sz, 2)
        elif self.form == 'rect': pygame.draw.rect(screen, self.color, (cx-sz, cy-sz, sz*2, sz*2), 2)
        else: pygame.draw.polygon(screen, self.color, [(cx, cy-sz), (cx-sz, cy+sz), (cx+sz, cy+sz)], 2)

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    f_s, f_b = pygame.font.SysFont("Arial", 12), pygame.font.SysFont("Arial", 16, bold=True)
    clock = pygame.time.Clock()
    shapes, enemies, resources, weapons_ground, bullets = [Shape()], [], [], [], []
    selected, last_h = None, time.time()

    while True:
        screen.fill(BG_COLOR)
        now = time.time()
        for i in range(0, 1251, 40): pygame.draw.line(screen, GRID_COLOR, (i, 0), (i, HEIGHT), 1)
        for i in range(0, HEIGHT, 40): pygame.draw.line(screen, GRID_COLOR, (0, i), (1250, i), 1)
        pygame.draw.rect(screen, (0, 60, 150), BASE_ZONE, 1)

        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                if mx < 1250:
                    if event.button == 1: selected = next((s for s in shapes if math.hypot(s.x-mx, s.y-my) < 40), None)
                    if event.button == 2: resources.append({'x': mx, 'y': my, 'type': random.choice(['BIO','NRG','RARE']), 'alive': True})
                    if event.button == 3: weapons_ground.append({'x': mx, 'y': my, 'type': random.choice(['PLASMA','RAIL']), 'alive': True})

        if random.random() < 0.04 and len(resources) < 35: resources.append({'x': random.randint(50, 1200), 'y': random.randint(50, 850), 'type': random.choice(['BIO','NRG','RARE']), 'alive': True})
        if random.random() < 0.005 and len(weapons_ground) < 5: weapons_ground.append({'x': random.randint(50, 1200), 'y': random.randint(50, 850), 'type': random.choice(list(WEAPON_TYPES.keys())), 'alive': True})
        if random.random() < 0.002 and len(enemies) < 4: enemies.append({'x': 1240, 'y': random.randint(50, 850), 'hp': 40.0, 'alive': True})

        temp = []
        for s in shapes:
            s.update(resources, weapons_ground, enemies, bullets, shapes); s.draw(screen, f_s, s == selected)
            for r in resources:
                if math.hypot(s.x-r['x'], s.y-r['y']) < 30:
                    s.hp = min(s.mods['hp'], s.hp + RES_TYPES[r['type']]['hp']); s.lvl += RES_TYPES[r['type']]['lvl']; r['alive'] = False; WORLD_STATS['res_coll'] += 1
            for w in weapons_ground:
                if math.hypot(s.x-w['x'], s.y-w['y']) < 30: s.weapon = w['type']; w['alive'] = False
            if now - s.spawn_time > REPRO_AGE and len(shapes) < 40:
                new_form = s.form if random.random() > 0.3 else random.choice(['circle', 'rect', 'poly'])
                temp.append(Shape(s.x+30, s.y+30, s.brain.mutate(), s.gen+1, s.color, new_form, s.lvl*0.5)); s.spawn_time, WORLD_STATS['born'] = now, WORLD_STATS['born']+1
            if s.hp > 0 and now - s.spawn_time < s.lifetime: temp.append(s)
        shapes = temp if temp else [Shape()]

        for b in bullets:
            b['x'] += math.cos(b['angle'])*b['speed']; b['y'] += math.sin(b['angle'])*b['speed']
            pygame.draw.circle(screen, b['color'], (int(b['x']), int(b['y'])), 3)
            for e in enemies:
                if math.hypot(b['x']-e['x'], b['y']-e['y']) < 30:
                    e['hp'] -= b['dmg']; b['alive'] = False
                    if e['hp'] <= 0: e['alive'] = False; WORLD_STATS['en_killed'] += 1
        for e in enemies:
            pygame.draw.circle(screen, (255, 50, 50), (int(e['x']), int(e['y'])), 15, 1)
            if shapes:
                t = min(shapes, key=lambda s: math.hypot(s.x-e['x'], s.y-e['y']))
                e['x'] += math.cos(math.atan2(t.y-e['y'], t.x-e['x'])) * 0.8; e['y'] += math.sin(math.atan2(t.y-e['y'], t.x-e['x'])) * 0.8
                if math.hypot(e['x']-t.x, e['y']-t.y) < 20: t.hp -= 0.6

        resources = [r for r in resources if r['alive']]; weapons_ground = [w for w in weapons_ground if w['alive']]; bullets = [b for b in bullets if b['alive'] and 0 < b['x'] < 1250]; enemies = [e for e in enemies if e['alive']]
        for r in resources: pygame.draw.circle(screen, RES_TYPES[r['type']]['color'], (int(r['x']), int(r['y'])), 6, 1)
        for w in weapons_ground: pygame.draw.rect(screen, WEAPON_TYPES[w['type']]['color'], (int(w['x']-6), int(w['y']-6), 12, 12), 2)

        pygame.draw.rect(screen, (10, 10, 20), SIDE_PANEL); pygame.draw.line(screen, (0, 255, 150), (1250, 0), (1250, HEIGHT), 2)
        screen.blit(f_b.render("СИСТЕМА ЭВОЛЮЦИИ 3.5", True, (0, 255, 200)), (1270, 20))
        st = [f"Популяция: {len(shapes)}", f"Всего рождено: {WORLD_STATS['born']}", f"Собрано ресурсов: {WORLD_STATS['res_coll']}", f"Врагов повержено: {WORLD_STATS['en_killed']}"]
        for i, txt in enumerate(st): screen.blit(f_s.render(txt, True, (150, 150, 150)), (1270, 60 + i*22))
        
        if selected and selected in shapes:
            pygame.draw.rect(screen, (20, 20, 40), (1265, 180, 320, 300), border_radius=10)
            age_now = int(now - selected.spawn_time)
            info = [f"ОБЪЕКТ: {selected.name}", f"КЛАСС: {selected.mods['label']}", f"ОРУЖИЕ: {WEAPON_TYPES[selected.weapon]['label']}", f"УРОВЕНЬ: {int(selected.lvl)}", f"ВРЕМЯ ЖИЗНИ: {age_now}с", f"БОНУС СТАИ: x{selected.group_bonus:.1f}"]
            for i, txt in enumerate(info): screen.blit(f_s.render(txt, True, selected.color), (1280, 200 + i*22))
            in_l, out_l = ["ВХОД: X", "ВХОД: Y", "ВХОД: HP", "ВХОД: Угол", "ВХОД: Дист", "ВХОД: Враг", "ВХОД: Конст"], ["ВЫХОД: ПОВОРОТ", "ВЫХОД: СКОРОСТЬ"]
            for i, l in enumerate(in_l): screen.blit(f_s.render(l, True, (120, 120, 120)), (1280, 350+i*18))
            for i, l in enumerate(out_l): screen.blit(f_s.render(l, True, (0, 200, 255)), (1480, 370+i*80))
            for i in range(7):
                for j in range(2):
                    w = selected.brain.w[j][i]
                    pygame.draw.line(screen, (0, 255, 100) if w > 0 else (255, 50, 50), (1330, 358+i*18), (1475, 380+j*80), 1)

        screen.blit(f_s.render("[КЛИК КОЛЕСОМ] - Ресурс | [ПКМ] - Оружие", True, (100, 100, 100)), (1270, 875))
        if now - last_h > 1.0: WORLD_STATS['history'].append(len(shapes)); last_h = now
        pygame.draw.rect(screen, (0, 0, 0), (1270, 750, 310, 110))
        pts = [(1270 + i*4, 850 - v*4) for i, v in enumerate(WORLD_STATS['history'][-75:])]
        if len(pts) > 1: pygame.draw.lines(screen, (0, 255, 200), False, pts, 2)
        pygame.display.flip(); clock.tick(FPS)

if __name__ == "__main__": main()
