# core/game_core.py
import random
import re
import logging
from typing import List, Dict, Optional
from core.card import Card, CardType, land_mana_color

logger = logging.getLogger(__name__)

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'

class Player:
    def __init__(self, name: str):
        self.name = name
        self.life = 20
        self.library: List[Card] = []
        self.hand: List[Card] = []
        self.battlefield: List[Card] = []
        self.graveyard: List[Card] = []
        self.exile: List[Card] = []  # Añadir esta línea
        self.mana_pool: Dict[str, int] = {"W": 0, "U": 0, "B": 0, "R": 0, "G": 0, "C": 0}
        self.land_played_this_turn = False
        self.is_active = False
        self.floating_mana: List[Dict] = []

    def shuffle_library(self):
        random.shuffle(self.library)

    def draw_card(self, number: int = 1) -> List[Card]:
        drawn = []
        for _ in range(number):
            if self.library:
                card = self.library.pop(0)
                self.hand.append(card)
                drawn.append(card)
        return drawn

    def play_land(self, land: Card) -> bool:
        if land in self.hand and land.card_type == CardType.LAND and not self.land_played_this_turn:
            self.hand.remove(land)
            self.battlefield.append(land)
            self.land_played_this_turn = True
            return True
        return False

    def tap_land_for_mana(self, land: Card) -> bool:
        if land in self.battlefield and not land.tapped:
            land.tapped = True
            mana_color = land_mana_color(land.name)
            self.mana_pool[mana_color] = self.mana_pool.get(mana_color, 0) + 1
            self.floating_mana.append({"color": mana_color, "x": 0, "y": 0, "life": 60})
            return True
        return False

    def activate_creature_ability(self, creature: Card) -> bool:
        """Activa la habilidad de maná de una criatura (ej. Llanowar Elves)."""
        if creature.card_type != CardType.CREATURE or creature.tapped:
            return False
        if "{T}" in creature.text and "{G}" in creature.text:
            creature.tapped = True
            self.mana_pool["G"] = self.mana_pool.get("G", 0) + 1
            self.floating_mana.append({"color": "G", "x": 0, "y": 0, "life": 60})
            return True
        return False

    def untap_all(self):
        for card in self.battlefield:
            card.tapped = False
            if card.card_type == CardType.CREATURE:
                card.summoning_sickness = False
        self.floating_mana.clear()

    def can_pay_mana(self, mana_cost: str) -> bool:
        if not mana_cost:
            return True
        cost = self.parse_mana_cost(mana_cost)
        colored_needed = {k: v for k, v in cost.items() if k != "generic"}
        for color, amount in colored_needed.items():
            if self.mana_pool.get(color, 0) < amount:
                return False
        total = sum(self.mana_pool.values())
        return total >= cost.get("generic", 0) + sum(colored_needed.values())

    def pay_mana(self, mana_cost: str):
        if not mana_cost:
            return
        cost = self.parse_mana_cost(mana_cost)
        for color, amount in cost.items():
            if color != "generic":
                self.mana_pool[color] = self.mana_pool.get(color, 0) - amount
        for _ in range(cost.get("generic", 0)):
            for color in ["W", "U", "B", "R", "G", "C"]:
                if self.mana_pool.get(color, 0) > 0:
                    self.mana_pool[color] -= 1
                    break

    def parse_mana_cost(self, mana_cost: str) -> Dict[str, int]:
        result: Dict[str, int] = {"generic": 0}
        for symbol in re.findall(r'\{([^}]+)\}', mana_cost or ""):
            if symbol.isdigit():
                result["generic"] += int(symbol)
            elif symbol.upper() in ("W", "U", "B", "R", "G", "C"):
                c = symbol.upper()
                result[c] = result.get(c, 0) + 1
        return result

    def reset_mana_pool(self):
        for key in self.mana_pool:
            self.mana_pool[key] = 0
        self.floating_mana.clear()

    def take_damage(self, damage: int) -> bool:
        self.life -= damage
        return self.life <= 0

    def discard_to_hand_size(self):
        while len(self.hand) > 7:
            self.graveyard.append(self.hand.pop())

    def update_floating_mana(self):
        self.floating_mana = [m for m in self.floating_mana if m["life"] > 0]
        for m in self.floating_mana:
            m["life"] -= 1


class Game:
    PHASES = ["mantenimiento", "robo", "principal1", "combate", "principal2", "final"]

    def __init__(self, player1: Player, player2: Player):
        self.players = [player1, player2]
        self.active_player = 0
        self.turn = 1
        self.phase = "mantenimiento"
        self.turn_count = 1
        self.attackers: List[Card] = []
        self.blockers: Dict[Card, Card] = {}
        self.combat_active = False
        self.stack: List[Dict] = []
        self.log_messages: List[str] = []
        # Índice del defensor (el que NO ataca) — fijado al entrar en combate
        self.defending_player_index: int = 1

    def add_log(self, message: str):
        # Guardamos todos los mensajes sin límite
        self.log_messages.append(message)
        # Opcional: limitar a 500 para evitar memoria excesiva
        if len(self.log_messages) > 500:
            self.log_messages.pop(0)
        
        # Imprimir en consola con turno y fase
        turno = self.turn
        fase = self.phase.upper()[:4]
        jugador = "JUGADOR" if self.active_player == 0 else "IA"
        print(f"[T{turno}:{fase}:{jugador}] {message}")

    def current_player(self) -> Player:
        return self.players[self.active_player]

    def opponent(self) -> Player:
        return self.players[1 - self.active_player]

    def defending_player(self) -> Player:
        """El jugador que puede bloquear (el que NO está atacando)."""
        return self.players[self.defending_player_index]

    # ------------------------------------------------------------------
    # Fases
    # ------------------------------------------------------------------

    def advance_phase(self) -> bool:
        idx = self.PHASES.index(self.phase)
        if idx < len(self.PHASES) - 1:
            self.phase = self.PHASES[idx + 1]
            self.execute_phase_actions()
            return True
        self.end_turn()
        return False

    def execute_phase_actions(self):
        player = self.current_player()
        if self.phase == "mantenimiento":
            player.untap_all()
            self.add_log("🔄 Se enderezan todas las cartas")
        elif self.phase == "robo":
            player.draw_card()
            self.add_log(f"{player.name} roba una carta")
        elif self.phase in ("principal1", "principal2"):
            player.reset_mana_pool()
            self.add_log("✨ Maná reiniciado")
        elif self.phase == "combate":
            self.combat_active = True
            self.defending_player_index = 1 - self.active_player
            self.add_log("⚔️ Fase de combate iniciada ⚔️")
        elif self.phase == "final":
            # Sacrificar criaturas con "al final del turno, sacrifica"
            for card in player.battlefield[:]:
                if (card.card_type == CardType.CREATURE
                        and "sacrifica" in card.text.lower()
                        and "final del turno" in card.text.lower()):
                    player.battlefield.remove(card)
                    player.graveyard.append(card)
                    self.add_log(f"💀 {card.name} es sacrificado al final del turno")
            player.discard_to_hand_size()
            player.land_played_this_turn = False
            self.add_log("🔚 Fin del turno")

    def end_turn(self):
        self.current_player().reset_mana_pool()
        self.active_player = 1 - self.active_player
        self.turn += 1
        self.phase = "mantenimiento"
        self.turn_count = 1
        self.combat_active = False
        self.attackers.clear()
        self.blockers.clear()
        self.execute_phase_actions()
        self.add_log(f"{'='*38}")
        self.add_log(f"✨ Turno {self.turn} — {self.current_player().name} ✨")
        self.add_log(f"{'='*38}")

    # ------------------------------------------------------------------
    # Hechizos
    # ------------------------------------------------------------------

    def cast_spell(self, card: Card, targets: List = None) -> bool:
        player = self.current_player()
        if card.card_type == CardType.SORCERY and self.phase not in ("principal1", "principal2"):
            self.add_log("⚠️ Solo puedes lanzar conjuros en tu fase principal")
            return False
        if not player.can_pay_mana(card.mana_cost):
            self.add_log(f"⚠️ No tienes suficiente maná para {card.name}")
            return False
        player.pay_mana(card.mana_cost)
        player.hand.remove(card)
        self.stack.append({"card": card, "controller": player, "targets": targets or []})
        self.add_log(f"✨ {player.name} lanza {card.name}")
        self.resolve_stack()
        return True

    def resolve_stack(self):
        while self.stack:
            self.resolve_spell(self.stack.pop(0))

    def resolve_spell(self, spell: Dict):
        card = spell["card"]
        controller = spell["controller"]
        targets = spell["targets"]
        self.apply_card_effect(card, controller, targets)
        if card.card_type in (CardType.SORCERY, CardType.INSTANT):
            controller.graveyard.append(card)
            self.add_log(f"📜 {card.name} va al cementerio")
        else:
            controller.battlefield.append(card)
            if card.card_type == CardType.CREATURE:
                has_haste = "prisa" in card.text.lower() or "haste" in card.text.lower()
                card.summoning_sickness = not has_haste
                suffix = " con PRISA 🌟" if has_haste else " 🌟"
                self.add_log(f"🌟 {card.name} ({card.power}/{card.toughness}) entra al campo{suffix}")
            else:
                self.add_log(f"🌟 {card.name} entra al campo de batalla")

    def apply_card_effect(self, card: Card, controller: Player, targets: List):
        text = card.text.lower()
        if "daño" in text:
            m = re.search(r'(\d+)\s*puntos?\s*de\s*daño', text) or re.search(r'hace\s*(\d+)', text)
            if m:
                dmg = int(m.group(1))
                target = targets[0] if targets else self.opponent()
                if isinstance(target, Player):
                    target.take_damage(dmg)
                    self.add_log(f"💥 {card.name} hace {dmg} daño a {target.name}")
                elif isinstance(target, Card):
                    target.damage += dmg
                    self.add_log(f"💥 {card.name} hace {dmg} daño a {target.name}")
                    self.check_creature_death(target)
        elif "ganas" in text and "vida" in text:
            m = re.search(r'ganas\s*(\d+)\s*vidas?', text)
            if m:
                controller.life += int(m.group(1))
                self.add_log(f"💚 {controller.name} gana {m.group(1)} vidas")
        elif "entra al campo" in text and "ganas" in text:
            controller.life += 4
            self.add_log(f"💚 {controller.name} gana 4 vidas por {card.name}")

    # ------------------------------------------------------------------
    # Combate
    # ------------------------------------------------------------------

    # core/game_core.py
    # En check_creature_death, modificar la habilidad de Festering Goblin

    def check_creature_death(self, creature: Card):
        if creature.damage < (creature.toughness or 0):
            return
        
        for player in self.players:
            if creature in player.battlefield:
                player.battlefield.remove(creature)
                player.graveyard.append(creature)
                self.add_log(f"💀 {creature.name} muere")
                
                # Habilidad disparada: Festering Goblin
                if creature.name == "Festering Goblin":
                    # Buscar criaturas VIVAS en el campo de batalla (excluyendo al propio goblin que ya murió)
                    all_creatures = [
                        c for p in self.players 
                        for c in p.battlefield 
                        if c.card_type == CardType.CREATURE
                    ]
                    if all_creatures:
                        # Elegir la primera criatura viva (o podrías elegir aleatoriamente o la más débil)
                        target = all_creatures[0]
                        old_power = target.power
                        old_toughness = target.toughness
                        target.power = max(0, (target.power or 1) - 1)
                        target.toughness = max(0, (target.toughness or 1) - 1)
                        self.add_log(f"🔧 {creature.name}: {target.name} obtiene -1/-1 ({old_power}/{old_toughness} → {target.power}/{target.toughness})")
                    else:
                        self.add_log(f"🔧 {creature.name} muere, pero no hay criaturas objetivo")
                break

    def declare_attackers(self, attackers: List[Card]) -> bool:
        if self.phase != "combate" or not self.combat_active:
            return False
        valid = []
        for a in attackers:
            if a.can_attack():
                valid.append(a)
                a.tapped = True
                self.add_log(f"⚔️ {a.name} ({a.power}/{a.toughness}) ataca")
            else:
                reason = "fiebre de ataque" if a.summoning_sickness else "está girada"
                self.add_log(f"⚠️ {a.name} no puede atacar ({reason})")
        self.attackers = valid
        if valid:
            self.add_log(f"⚔️ {self.current_player().name} ataca con {len(valid)} criatura(s)")
        return True

    def declare_blockers(self, blockers: Dict[Card, Card]) -> bool:
        """blockers = {atacante: bloqueador}. Los bloqueadores son del defending_player."""
        if self.phase != "combate" or not self.attackers:
            return False
        
        defender_bf = set(self.defending_player().battlefield)
        valid: Dict[Card, Card] = {}
        
        for att, blk in blockers.items():
            if blk not in defender_bf or not blk.can_block():
                continue
            
            # 1. Verificar Vuela (Flying) en el ATACANTE
            att_flies = "vuela" in att.text.lower() or "flying" in att.text.lower()
            blk_flies = "vuela" in blk.text.lower() or "flying" in blk.text.lower()
            blk_reach = "alcance" in blk.text.lower() or "reach" in blk.text.lower()
            
            if att_flies and not blk_flies and not blk_reach:
                self.add_log(f"⚠️ {blk.name} no puede bloquear a {att.name} (tiene Vuela)")
                continue
            
            # 2. Verificar restricción de Cloud Sprite (solo puede bloquear criaturas con Vuela)
            if "solo puede bloquear" in blk.text.lower() or "only block creatures with flying" in blk.text.lower():
                if not att_flies:
                    self.add_log(f"⚠️ {blk.name} solo puede bloquear criaturas con Vuela, pero {att.name} no vuela")
                    continue
            
            valid[att] = blk
            self.add_log(f"🛡️ {blk.name} bloquea a {att.name}")
        
        for blk in valid.values():
            blk.tapped = True
        self.blockers = valid
        if valid:
            self.add_log(f"🛡️ {self.defending_player().name} bloquea {len(valid)} atacante(s)")
        return True

    def deal_combat_damage(self):
        if not self.attackers:
            return
        
        self.add_log("💢 Resolviendo daño de combate...")
        
        # Primera fase: aplicar todo el daño
        for attacker in self.attackers[:]:
            att_power = attacker.power or 0
            has_trample = "arrolla" in attacker.text.lower() or "trample" in attacker.text.lower()
            
            if attacker in self.blockers:
                blocker = self.blockers[attacker]
                blk_power = blocker.power or 0
                blocker_toughness = blocker.toughness or 0
                
                # Atacante daña al bloqueador
                blocker.damage += att_power
                self.add_log(f"  {attacker.name} ({att_power}) → {blocker.name}")
                
                # Bloqueador daña al atacante
                attacker.damage += blk_power
                self.add_log(f"  {blocker.name} ({blk_power}) → {attacker.name}")
                
                # Arrolla: calcular daño sobrante (se aplicará después)
                remaining_damage = max(0, att_power - blocker_toughness)
                if has_trample and remaining_damage > 0:
                    self.add_log(f"  🌟 ARROLLA! {attacker.name} hará {remaining_damage} daño sobrante")
            else:
                # Daño directo al jugador
                old_life = self.defending_player().life
                self.defending_player().take_damage(att_power)
                self.add_log(f"  {attacker.name} ({att_power}) → {self.defending_player().name} ({old_life} → {self.defending_player().life})")
        
        # Segunda fase: verificar muertes (después de todo el daño)
        self.add_log("  --- Verificando muertes ---")
        for attacker in self.attackers[:]:
            if attacker in self.blockers:
                blocker = self.blockers[attacker]
                self.check_creature_death(blocker)
                self.check_creature_death(attacker)
        
        # Tercera fase: aplicar daño sobrante de Arrolla (después de las muertes)
        for attacker in self.attackers[:]:
            if attacker in self.blockers:
                has_trample = "arrolla" in attacker.text.lower() or "trample" in attacker.text.lower()
                blocker = self.blockers[attacker]
                blocker_toughness = blocker.toughness or 0
                remaining_damage = max(0, (attacker.power or 0) - blocker_toughness)
                
                if has_trample and remaining_damage > 0 and attacker.damage < (attacker.toughness or 0):
                    old_life = self.defending_player().life
                    self.defending_player().take_damage(remaining_damage)
                    self.add_log(f"  🌟 ARROLLA! {attacker.name} hace {remaining_damage} daño SOBRANTE a {self.defending_player().name} ({old_life} → {self.defending_player().life})")
        
        self.attackers.clear()
        self.blockers.clear()
        self.combat_active = False
        self.add_log("💢 Daño de combate resuelto")

    def check_game_over(self) -> Optional[Player]:
        for player in self.players:
            if player.life <= 0:
                return player
        return None
