"""Lógica del juego de aventura en el castillo.

Este módulo contiene las clases del juego y no depende de Streamlit,
por lo que se puede probar de forma independiente.
"""

import random
import time
from enum import Enum
from typing import List, Optional, Tuple

# Número de habitaciones del castillo.
HABITACIONES_TOTALES = 9
HABITACIONES_MIN_ENEMIGOS = 3
HABITACIONES_MIN_TESOROS = 2

# Reglas de combate y recompensas.
VIDA_INICIAL = 100
DANO_ENEMIGO = 20
TIEMPO_LIMITE_SEGUNDOS = 20
ORO_INICIAL = 0
ORO_TESORO = 50
CURACION_TESORO = 2

NOMBRES_ENEMIGOS = [
    "Guardián de Hierro",
    "Esqueleto",
    "Goblin",
    "Bruja",
    "Araña Gigante",
    "Caballero Maldito",
]


class TipoSala(Enum):
    """Tipos de habitación que existen en el castillo."""

    TESORO = "Tesoro"
    ENEMIGO = "Enemigo"
    VACIA = "Vacía"


class EstadoJuego(Enum):
    """Estados posibles de una partida."""

    EN_JUEGO = "En juego"
    GANADO = "Ganaste"
    PERDIDO = "Perdiste"


class Enemigo:
    """Enemigo que protege una habitación y propone una operación."""

    def __init__(
        self,
        nombre: Optional[str] = None,
        dano: int = DANO_ENEMIGO,
    ) -> None:
        self.nombre = nombre or random.choice(NOMBRES_ENEMIGOS)
        self.dano = dano
        self.operacion, self.respuesta = self._crear_operacion()

    @staticmethod
    def _crear_operacion() -> Tuple[str, int]:
        """Crea una operación matemática y su respuesta correcta."""
        numero_a = random.randint(2, 20)
        numero_b = random.randint(2, 12)
        tipo = random.choice(["suma", "resta", "multiplicacion"])

        if tipo == "suma":
            return f"{numero_a} + {numero_b}", numero_a + numero_b

        if tipo == "resta":
            mayor = max(numero_a, numero_b)
            menor = min(numero_a, numero_b)
            return f"{mayor} - {menor}", mayor - menor

        return f"{numero_a} x {numero_b}", numero_a * numero_b

    def verificar(self, respuesta: str) -> bool:
        """Indica si la respuesta del jugador es correcta."""
        try:
            valor = int(str(respuesta).strip())
        except (TypeError, ValueError):
            return False

        return valor == self.respuesta


class Sala:
    """Habitación del castillo: tesoro, enemigo o vacía."""

    def __init__(
        self,
        numero: int,
        tipo: TipoSala = TipoSala.VACIA,
        enemigo: Optional[Enemigo] = None,
        recompensa_oro: int = 0,
        curacion: int = 0,
    ) -> None:
        self.numero = numero
        self.tipo = tipo
        self.enemigo = enemigo
        self.recompensa_oro = recompensa_oro
        self.curacion = curacion
        self.visitada = False
        self.resuelta = False
        self.enemigo_derrotado = False
        self.tiempo_agotado = False

    @classmethod
    def crear(cls, numero: int, tipo: TipoSala) -> "Sala":
        """Crea una sala del tipo indicado con su contenido."""
        if tipo == TipoSala.ENEMIGO:
            return cls(numero, tipo, enemigo=Enemigo())

        if tipo == TipoSala.TESORO:
            return cls(
                numero,
                tipo,
                recompensa_oro=ORO_TESORO,
                curacion=CURACION_TESORO,
            )

        return cls(numero, tipo)

    @property
    def estado_texto(self) -> str:
        """Describe el estado de la sala para mostrar en el mapa."""
        if not self.visitada:
            return "Sin explorar"

        if self.tipo == TipoSala.ENEMIGO and not self.enemigo_derrotado:
            return "Enemigo vivo"

        return "Completada"


class Castillo:
    """Conjunto de habitaciones que el jugador debe completar."""

    def __init__(self, total: int = HABITACIONES_TOTALES) -> None:
        self.total = total
        self.salas: List[Sala] = self._generar()

    def _generar(self) -> List[Sala]:
        """Crea el mapa con la entrada y el contenido mínimo garantizados."""
        tipos = [TipoSala.ENEMIGO] * HABITACIONES_MIN_ENEMIGOS
        tipos += [TipoSala.TESORO] * HABITACIONES_MIN_TESOROS
        tipos += [
            random.choice(list(TipoSala))
            for _ in range(self.total - len(tipos) - 1)
        ]
        random.shuffle(tipos)
        tipos.insert(0, TipoSala.VACIA)

        return [
            Sala.crear(numero, tipo)
            for numero, tipo in enumerate(tipos, start=1)
        ]

    def sala_actual(self, indice: int) -> Sala:
        """Devuelve la sala que ocupa la posición indicada."""
        return self.salas[indice]

    @property
    def habitaciones_visitadas(self) -> int:
        """Cantidad de salas que el jugador ya exploró."""
        return sum(1 for sala in self.salas if sala.visitada)

    @property
    def enemigos_derrotados(self) -> int:
        """Cantidad de enemigos que el jugador ya venció."""
        return sum(1 for sala in self.salas if sala.enemigo_derrotado)


class Jugador:
    """Aventurero que recorre el castillo."""

    def __init__(
        self,
        nombre: str = "Aventurero",
        vida: int = VIDA_INICIAL,
        vida_maxima: int = VIDA_INICIAL,
        oro: int = ORO_INICIAL,
    ) -> None:
        self.nombre = nombre
        self.vida = vida
        self.vida_maxima = vida_maxima
        self.oro = oro
        self.indice_sala = 0

    def perder_vida(self, cantidad: int) -> int:
        """Resta vida y devuelve cuánto perdió el jugador."""
        perdido = min(cantidad, self.vida)
        self.vida -= perdido
        return perdido

    def curar(self, cantidad: int) -> int:
        """Suma vida sin pasar el máximo y devuelve cuánto recuperó."""
        curado = min(cantidad, self.vida_maxima - self.vida)
        self.vida += curado
        return curado

    def vivo(self) -> bool:
        """Indica si el jugador todavía tiene vida."""
        return self.vida > 0


class Temporizador:
    """Cuenta regresiva para responder a un enemigo."""

    def __init__(self, limite: float = TIEMPO_LIMITE_SEGUNDOS) -> None:
        self.limite = limite
        self.inicio = time.monotonic()

    def reiniciar(self) -> None:
        """Reinicia la cuenta regresiva."""
        self.inicio = time.monotonic()

    @property
    def restante(self) -> float:
        """Segundos que quedan para responder."""
        return max(0.0, self.limite - (time.monotonic() - self.inicio))

    @property
    def progreso(self) -> float:
        """Fracción de tiempo restante entre 0.0 y 1.0."""
        if not self.limite:
            return 0.0

        return self.restante / self.limite

    @property
    def expirado(self) -> bool:
        """Indica si ya se acabó el tiempo."""
        return self.restante <= 0


class Juego:
    """Partida que une al jugador, el castillo y el temporizador."""

    def __init__(
        self,
        nombre: str = "Aventurero",
        total_habitaciones: int = HABITACIONES_TOTALES,
    ) -> None:
        self.nombre = nombre
        self.total_habitaciones = total_habitaciones
        self.reiniciar()

    def reiniciar(self) -> None:
        """Prepara una partida nueva desde la primera habitación."""
        self.jugador = Jugador(self.nombre)
        self.castillo = Castillo(self.total_habitaciones)
        self.temporizador = Temporizador()
        self.estado = EstadoJuego.EN_JUEGO
        self.mensaje = ""
        self.tipo_mensaje = "info"
        self.entrar_sala()

    @property
    def sala_actual(self) -> Sala:
        """Sala en la que se encuentra el jugador."""
        return self.castillo.sala_actual(self.jugador.indice_sala)

    @property
    def terminado(self) -> bool:
        """Indica si la partida ya terminó."""
        return self.estado != EstadoJuego.EN_JUEGO

    @property
    def en_combate(self) -> bool:
        """Indica si hay un enemigo sin resolver en la sala actual."""
        return (
            self.estado == EstadoJuego.EN_JUEGO
            and self.sala_actual.tipo == TipoSala.ENEMIGO
            and not self.sala_actual.resuelta
        )

    @property
    def puede_responder(self) -> bool:
        """Indica si el jugador todavía puede responder al enemigo."""
        return self.en_combate and not self.temporizador.expirado

    @property
    def puede_avanzar(self) -> bool:
        """Indica si el jugador puede pasar a la siguiente sala."""
        return (
            self.estado == EstadoJuego.EN_JUEGO and self.sala_actual.resuelta
        )

    def entrar_sala(self) -> None:
        """Entra en la sala actual y aplica lo que hay en ella."""
        sala = self.sala_actual

        if sala.visitada:
            return

        sala.visitada = True

        if sala.tipo == TipoSala.ENEMIGO:
            self.temporizador.reiniciar()
            self._avisar(
                f"⚔️ ¡Un {sala.enemigo.nombre} te bloquea el paso!",
                "info",
            )
            return

        sala.resuelta = True

        if sala.tipo == TipoSala.TESORO:
            self.jugador.oro += sala.recompensa_oro
            self.jugador.curar(sala.curacion)
            self._avisar(
                f"💰 ¡Tesoro! +{sala.recompensa_oro} de oro "
                f"y +{sala.curacion} de vida.",
                "exito",
            )
            return

        self._avisar("La habitación está vacía. Pasa sin riesgo.", "info")

    def responder(self, respuesta: str) -> None:
        """Resuelve el combate con la respuesta dada por el jugador."""
        if not self.puede_responder:
            return

        sala = self.sala_actual
        sala.resuelta = True

        if sala.enemigo.verificar(respuesta):
            sala.enemigo_derrotado = True
            self._avisar(
                f"✅ ¡Correcto! Derrotaste al {sala.enemigo.nombre}.",
                "exito",
            )
            return

        self._recibir_dano(
            sala.enemigo.dano,
            f"❌ ¡Respuesta incorrecta! {sala.enemigo.nombre} te atacó.",
        )

    def expirar_tiempo(self) -> None:
        """Aplica el daño cuando el tiempo para responder se agota."""
        sala = self.sala_actual
        combate_vigente = self.en_combate and self.temporizador.expirado

        if sala.tiempo_agotado or not combate_vigente:
            return

        sala.tiempo_agotado = True
        sala.resuelta = True
        self._recibir_dano(
            sala.enemigo.dano,
            f"⌛ ¡Se acabó el tiempo! {sala.enemigo.nombre} te golpeó.",
        )

    def avanzar(self) -> None:
        """Pasa a la siguiente habitación del castillo."""
        if not self.puede_avanzar:
            return

        self.jugador.indice_sala += 1

        if self.jugador.indice_sala >= self.castillo.total:
            self.estado = EstadoJuego.GANADO
            self._avisar(
                f"🏆 ¡Completaste el castillo con {self.jugador.oro} de oro!",
                "exito",
            )
            return

        self.entrar_sala()

    def _recibir_dano(self, dano: int, motivo: str) -> None:
        """Quita vida al jugador y revisa si pierde la partida."""
        perdido = self.jugador.perder_vida(dano)

        if not self.jugador.vivo():
            self.estado = EstadoJuego.PERDIDO
            self._avisar(
                f"{motivo} -{perdido} de vida. 💀 Te quedaste sin vida.",
                "error",
            )
            return

        self._avisar(f"{motivo} -{perdido} de vida.", "error")

    def _avisar(self, mensaje: str, tipo: str) -> None:
        """Guarda el último mensaje y el tipo de aviso."""
        self.mensaje = mensaje
        self.tipo_mensaje = tipo
