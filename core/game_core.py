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
        # Verificar si hay prevención de daño activa
        if hasattr(self, 'prevent_next_damage') and self.prevent_next_damage > 0:
            prevented = min(damage, self.prevent_next_damage)
            damage -= prevented
            self.prevent_next_damage -= prevented
            self.game.add_log(f"🛡️ Se previenen {prevented} puntos de daño a {self.name}")
        
        if damage > 0:
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
        self.pending_target_selection = None

    def add_log(self, message: str):
        # Guardamos todos los mensajes sin límite
        self.log_messages.append(message)        
        # Imprimir en consola con turno y fase
        turno = self.turn
        fase = self.phase.upper()[:4]
        if self.phase == "combate" and hasattr(self, 'subphase'):
            fase = f"COMB({self.subphase[:3].upper()})"
        else:
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
            player.land_played_this_turn = False  # Asegurar reset al inicio del turno
            print(f"DEBUG: Mantenimiento - reset land_played_this_turn para {player.name}")  # Añadir print
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
            # Revertir buffs temporales de criaturas
            for player in self.players:
                for card in player.battlefield:
                    if hasattr(card, 'temp_buffs') and card.temp_buffs:
                        for buff_name, power_bonus, toughness_bonus in card.temp_buffs:
                            card.power = (card.power or 0) - power_bonus
                            card.toughness = (card.toughness or 0) - toughness_bonus
                            self.add_log(f"🔄 {card.name}: Se revierte {buff_name} ({card.power}/{card.toughness})")
                        card.temp_buffs.clear()
            
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
            print(f"DEBUG: Reset land_played_this_turn para {player.name}")  # Añadir print
            self.add_log("🔚 Fin del turno")

    def end_turn(self):
        self.current_player().reset_mana_pool()
        self.active_player = 1 - self.active_player
        self.turn += 1
        self.phase = "mantenimiento"
        self.combat_active = False
        self.attackers.clear()
        self.blockers.clear()
        
        # Resetear land_played_this_turn para el nuevo jugador activo
        self.current_player().land_played_this_turn = False
        
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
        
        # ============================================================
        # BANDAGE (prevenir daño + robar carta)
        # ============================================================
        if "bandage" in card.name.lower():
            if targets and len(targets) > 0:
                target = targets[0]
                if not hasattr(target, 'prevent_next_damage'):
                    target.prevent_next_damage = 0
                target.prevent_next_damage += 1
                target_name = target.name if hasattr(target, 'name') else str(target)
                self.add_log(f"🩹 {card.name}: Previene el próximo 1 punto de daño a {target_name}")
            
            # Robar carta
            controller.draw_card()
            self.add_log(f"📖 {card.name}: {controller.name} roba una carta")
            return
        
        # ============================================================
        # PEEK (robar carta + mirar mano)
        # ============================================================
        if "peek" in card.name.lower():
            # Robar carta
            controller.draw_card()
            self.add_log(f"📖 {card.name}: {controller.name} roba una carta")
            
            # Mirar mano del oponente
            opponent = self.opponent()
            hand_str = ", ".join([c.name for c in opponent.hand])
            self.add_log(f"👁️ {card.name}: Mano de {opponent.name}: {hand_str}")
            return
        
        # ============================================================
        # TERROR (destruir criatura)
        # ============================================================
        if "terror" in card.name.lower():
            if targets and len(targets) > 0 and isinstance(targets[0], Card):
                target = targets[0]
                # Verificar que no sea artefacto ni negra
                is_artifact = "artefacto" in target.text.lower()
                is_black = Color.BLACK in target.colors
                
                if is_artifact:
                    self.add_log(f"⚠️ {card.name}: {target.name} es un artefacto, no puede ser objetivo")
                elif is_black:
                    self.add_log(f"⚠️ {card.name}: {target.name} es negra, no puede ser objetivo")
                else:
                    # Destruir la criatura
                    target.damage = target.toughness or 1
                    self.add_log(f"💀 {card.name}: {target.name} es destruida")
                    self.check_creature_death(target)
            return
        
        # ============================================================
        # GIANT GROWTH (+3/+3)
        # ============================================================
        if "giant growth" in card.name.lower():
            if targets and len(targets) > 0 and isinstance(targets[0], Card):
                target = targets[0]
                old_power = target.power
                old_toughness = target.toughness
                if not hasattr(target, 'temp_buffs'):
                    target.temp_buffs = []
                target.temp_buffs.append(("giant_growth", 3, 3))
                target.power = (target.power or 0) + 3
                target.toughness = (target.toughness or 0) + 3
                self.add_log(f"🌿 {card.name}: {target.name} obtiene +3/+3 ({old_power}/{old_toughness} → {target.power}/{target.toughness})")
            return
        
        # ============================================================
        # FISTS OF THE ANVIL (+4/+0)
        # ============================================================
        if "fists of the anvil" in card.name.lower():
            if targets and len(targets) > 0 and isinstance(targets[0], Card):
                target = targets[0]
                old_power = target.power
                if not hasattr(target, 'temp_buffs'):
                    target.temp_buffs = []
                target.temp_buffs.append(("fists", 4, 0))
                target.power = (target.power or 0) + 4
                self.add_log(f"👊 {card.name}: {target.name} obtiene +4/+0 ({old_power} → {target.power})")
            return
        
        # ============================================================
        # HECHIZOS DE DAÑO (Rayo, Descarga, etc.)
        # ============================================================
        if "daño" in text and "prevén" not in text:
            m = re.search(r'(\d+)\s*puntos?\s*de\s*daño', text) or re.search(r'hace\s*(\d+)', text)
            if m:
                dmg = int(m.group(1))
                if targets and len(targets) > 0:
                    target = targets[0]
                    if isinstance(target, Player):
                        target.take_damage(dmg)
                        self.add_log(f"💥 {card.name} hace {dmg} daño a {target.name}")
                    elif isinstance(target, Card):
                        target.damage += dmg
                        self.add_log(f"💥 {card.name} hace {dmg} daño a {target.name}")
                        self.check_creature_death(target)
                else:
                    opponent = self.opponent()
                    opponent.take_damage(dmg)
                    self.add_log(f"💥 {card.name} hace {dmg} daño a {opponent.name}")
            return
        
        # ============================================================
        # GANAR VIDA
        # ============================================================
        if "ganas" in text and "vida" in text:
            m = re.search(r'ganas\s*(\d+)\s*vidas?', text)
            if m:
                controller.life += int(m.group(1))
                self.add_log(f"💚 {controller.name} gana {m.group(1)} vidas")
            return
        
        # ============================================================
        # ENTRADA AL CAMPO con ganar vida
        # ============================================================
        if "entra al campo" in text and "ganas" in text:
            controller.life += 4
            self.add_log(f"💚 {controller.name} gana 4 vidas por {card.name}")
            return

    # ------------------------------------------------------------------
    # Combate
    # ------------------------------------------------------------------

    def check_creature_death(self, creature: Card):
        print(f"🔍 CHECK_CREATURE_DEATH: {creature.name} (damage={creature.damage}, toughness={creature.toughness})")
        if creature.damage < (creature.toughness or 0):
            print(f"   ✅ {creature.name} sobrevive")
            return
        
        for player in self.players:
            if creature in player.battlefield:
                player.battlefield.remove(creature)
                player.graveyard.append(creature)
                self.add_log(f"💀 {creature.name} muere")
                print(f"   💀 {creature.name} removido del campo")
                
                # Habilidad disparada: Festering Goblin
                if creature.name == "Festering Goblin":
                    all_creatures = [
                        c for p in self.players 
                        for c in p.battlefield 
                        if c.card_type == CardType.CREATURE
                    ]
                    if all_creatures:
                        self._request_target_selection(creature, all_creatures)
                    else:
                        self.add_log(f"🔧 {creature.name} muere, pero no hay criaturas objetivo")
                break  # <-- Este break debe estar indentado dentro del if, pero al mismo nivel que el código anterior

    def _ai_choose_festering_target(self, creatures: List[Card]) -> Card:
        """IA elige objetivo para Festering Goblin (prioriza las criaturas del jugador)"""
        # Primero, buscar criaturas del jugador (oponente)
        player_creatures = [c for c in creatures if c in self.players[0].battlefield]
        if player_creatures:
            # Elegir la más débil (menor resistencia)
            return min(player_creatures, key=lambda c: c.toughness or 0)
        # Si no hay criaturas del jugador, elegir cualquiera
        return creatures[0]

    def _apply_festering_goblin_effect(self, target: Card):
        """Aplica el efecto de -1/-1 al objetivo seleccionado."""
        old_power = target.power
        old_toughness = target.toughness
        target.power = max(0, (target.power or 1) - 1)
        target.toughness = max(0, (target.toughness or 1) - 1)
        self.add_log(f"🔧 Festering Goblin: {target.name} obtiene -1/-1 ({old_power}/{old_toughness} → {target.power}/{target.toughness})")
        # Verificar si la criatura objetivo muere por el -1/-1
        if target.toughness <= 0:
            target.damage = target.toughness + 1  # Forzar muerte
            self.check_creature_death(target)

    def _request_target_selection(self, source_card: Card, possible_targets: List[Card]):
        """Activa el modo de selección manual de objetivo."""
        self.pending_target_selection = {
            "source": source_card,
            "targets": possible_targets,
            "callback": self._apply_festering_goblin_effect
        }

    def _apply_festering_goblin_effect(self, target: Card):
        """Aplica -1/-1 al objetivo seleccionado."""
        old_power = target.power
        old_toughness = target.toughness
        target.power = max(0, (target.power or 1) - 1)
        target.toughness = max(0, (target.toughness or 1) - 1)
        self.add_log(f"🔧 Festering Goblin: {target.name} obtiene -1/-1 ({old_power}/{old_toughness} → {target.power}/{target.toughness})")
        # Verificar si la criatura objetivo muere por el -1/-1
        if target.toughness <= 0:
            target.damage = target.toughness + 1  # Forzar muerte
            self.check_creature_death(target)
        self.pending_target_selection = None

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
                reason = "mareo de invocación" if a.summoning_sickness else "está girada"
                self.add_log(f"⚠️ {a.name} no puede atacar ({reason})")
        self.attackers = valid
        if valid:
            self.add_log(f"⚔️ {self.current_player().name} ataca con {len(valid)} criatura(s)")
        return True

    def declare_blockers(self, blockers: Dict[Card, Card]) -> bool:
        print(f"\n🔍 DECLARE_BLOCKERS - Recibido: {[(att.name, blk.name) for att, blk in blockers.items()]}")
        
        if self.phase != "combate" or not self.attackers:
            print(f"❌ No se pueden declarar bloqueadores: phase={self.phase}, attackers={[a.name for a in self.attackers]}")
            return False
        
        # Lista de bloqueadores disponibles (por objeto, no por nombre)
        available_blockers = [c for c in self.defending_player().battlefield if c.card_type == CardType.CREATURE]
        print(f"📦 Bloqueadores disponibles: {[b.name for b in available_blockers]}")
        
        valid: Dict[Card, Card] = {}
        used_attackers = set()
        
        for att, blk in blockers.items():
            print(f"\n🔍 Procesando par: atacante={att.name}, bloqueador={blk.name}")
            
            # Buscar el bloqueador REAL en la lista de disponibles (usando el nombre y que no esté ya usado)
            real_blk = None
            for b in available_blockers:
                if b.name == blk.name and b not in valid.values():
                    real_blk = b
                    break
            
            if real_blk is None:
                print(f"❌ Bloqueador {blk.name} no está disponible")
                continue
            
            if not real_blk.can_block():
                print(f"❌ {real_blk.name} no puede bloquear")
                continue
            
            # Buscar un atacante con el mismo nombre que no haya sido usado
            real_att = None
            for a in self.attackers:
                if a.name == att.name and a not in used_attackers:
                    real_att = a
                    break
            
            if real_att is None:
                print(f"❌ No se encontró atacante {att.name} disponible")
                continue
            
            print(f"✅ Atacante encontrado: {real_att.name} (id={id(real_att)})")
            print(f"✅ Bloqueador encontrado: {real_blk.name} (id={id(real_blk)})")
            
            # Verificar Vuela
            att_flies = "vuela" in real_att.text.lower() or "flying" in real_att.text.lower()
            blk_flies = "vuela" in real_blk.text.lower() or "flying" in real_blk.text.lower()
            blk_reach = "alcance" in real_blk.text.lower() or "reach" in real_blk.text.lower()
            
            if att_flies and not blk_flies and not blk_reach:
                print(f"❌ {real_blk.name} no puede bloquear a {real_att.name} (Vuela)")
                continue
            
            # Verificar restricción de Cloud Sprite
            if "solo puede bloquear" in real_blk.text.lower():
                if not att_flies:
                    print(f"❌ {real_blk.name} solo puede bloquear criaturas con Vuela")
                    continue
            
            valid[real_att] = real_blk
            used_attackers.add(real_att)
            print(f"✅ BLOQUEO VÁLIDO: {real_blk.name} bloquea a {real_att.name}")
        
        for blk in valid.values():
            blk.tapped = True
        
        self.blockers = valid
        print(f"\n📦 self.blockers final: {[(a.name, b.name) for a, b in self.blockers.items()]}")
        if valid:
            self.add_log(f"🛡️ {self.defending_player().name} bloquea {len(valid)} atacante(s)")
        
        return True

    def deal_combat_damage(self):
        print(f"\n🔍 DEAL_COMBAT_DAMAGE - Inicio")
        print(f"📦 self.attackers: {[a.name for a in self.attackers]}")
        print(f"📦 self.blockers: {[(a.name, b.name) for a, b in self.blockers.items()]}")
        
        if not self.attackers:
            print("❌ No hay atacantes")
            return
        
        self.add_log("💢 Resolviendo daño de combate...")
        
        # Crear una lista de pares (atacante, bloqueador)
        blocker_pairs = list(self.blockers.items())
        print(f"📦 blocker_pairs inicial: {[(a.name, b.name) for a, b in blocker_pairs]}")
        
        # Primera fase: aplicar daño
        for attacker in self.attackers[:]:
            print(f"\n🔍 Procesando atacante: {attacker.name} (id={id(attacker)})")
            att_power = attacker.power or 0
            has_trample = "arrolla" in attacker.text.lower() or "trample" in attacker.text.lower()
            
            # Buscar un bloqueador para este atacante
            blocker = None
            blocker_idx = -1
            for i, (att, blk) in enumerate(blocker_pairs):
                if att.name == attacker.name:
                    blocker = blk
                    blocker_idx = i
                    print(f"   Encontrado bloqueador {blk.name} (id={id(blk)}) para atacante {attacker.name}")
                    break
            
            if blocker:
                blk_power = blocker.power or 0
                blocker_toughness = blocker.toughness or 0
                
                # Atacante daña al bloqueador
                blocker.damage += att_power
                self.add_log(f"  {attacker.name} ({att_power}) → {blocker.name}")
                print(f"   {blocker.name} recibe {att_power} daño (total: {blocker.damage}/{blocker.toughness})")
                
                # Bloqueador daña al atacante
                attacker.damage += blk_power
                self.add_log(f"  {blocker.name} ({blk_power}) → {attacker.name}")
                print(f"   {attacker.name} recibe {blk_power} daño (total: {attacker.damage}/{attacker.toughness})")
                
                # Arrolla
                if has_trample:
                    remaining_damage = max(0, att_power - blocker_toughness)
                    if remaining_damage > 0:
                        old_life = self.defending_player().life
                        self.defending_player().take_damage(remaining_damage)
                        self.add_log(f"  🌟 ARROLLA! {attacker.name} hace {remaining_damage} daño SOBRANTE a {self.defending_player().name} ({old_life} → {self.defending_player().life})")
                
                # Eliminar este par
                if blocker_idx >= 0:
                    blocker_pairs.pop(blocker_idx)
                    print(f"   Par eliminado, restan {len(blocker_pairs)} pares")
            else:
                # Daño directo
                old_life = self.defending_player().life
                self.defending_player().take_damage(att_power)
                self.add_log(f"  {attacker.name} ({att_power}) → {self.defending_player().name} ({old_life} → {self.defending_player().life})")
                print(f"   Daño directo: {attacker.name} hace {att_power} daño a {self.defending_player().name}")
        
        # Segunda fase: verificar muertes
        self.add_log("  --- Verificando muertes ---")
        
        all_creatures = set()
        for p in self.players:
            all_creatures.update([c for c in p.battlefield if c.card_type == CardType.CREATURE])
        
        print(f"\n🔍 Verificando muertes de {len(all_creatures)} criaturas:")
        for creature in all_creatures:
            if creature.damage >= (creature.toughness or 0):
                print(f"   💀 {creature.name} tiene {creature.damage}/{creature.toughness} - MUERE")
                self.check_creature_death(creature)
            else:
                print(f"   ✅ {creature.name} tiene {creature.damage}/{creature.toughness} - SOBREVIVE")
        
        self.attackers.clear()
        self.blockers.clear()
        self.combat_active = False
        self.add_log("💢 Daño de combate resuelto")
        print("🔍 DEAL_COMBAT_DAMAGE - Fin\n")

    def check_game_over(self) -> Optional[Player]:
        for player in self.players:
            if player.life <= 0:
                return player
        return None
