"""Lógica del juego de aventura en el castillo.

El castillo es una cuadrícula de salas. El jugador se mueve entre
celdas vecinas, algunas escondidas por la niebla de guerra y otras
bloqueadas por muros.

Este módulo contiene las clases del juego y no depende de Streamlit,
por lo que se puede probar de forma independiente.
"""

import random
import time
from collections import deque
from enum import Enum
from typing import Dict, List, NamedTuple, Optional, Set, Tuple

# Estructura del castillo.
FILAS = 5
COLUMNAS = 5
PORCENTAJE_MUROS = 15
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
    """Tipos de celda que existen en el castillo."""

    TESORO = "Tesoro"
    ENEMIGO = "Enemigo"
    VACIA = "Vacía"
    MURO = "Muro"


class EstadoJuego(Enum):
    """Estados posibles de una partida."""

    EN_JUEGO = "En juego"
    GANADO = "Ganaste"
    PERDIDO = "Perdiste"


class Posicion(NamedTuple):
    """Coordenadas de una celda del castillo."""

    fila: int
    columna: int


class Direccion(Enum):
    """Direcciones en las que el jugador puede moverse."""

    ARRIBA = "⬆️ Arriba"
    ABAJO = "⬇️ Abajo"
    IZQUIERDA = "⬅️ Izquierda"
    DERECHA = "➡️ Derecha"


DESPLAZAMIENTOS: Dict[Direccion, Posicion] = {
    Direccion.ARRIBA: Posicion(-1, 0),
    Direccion.ABAJO: Posicion(1, 0),
    Direccion.IZQUIERDA: Posicion(0, -1),
    Direccion.DERECHA: Posicion(0, 1),
}

TIPOS_ALEATORIOS = (TipoSala.VACIA, TipoSala.ENEMIGO, TipoSala.TESORO)


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
    """Celda del castillo: tesoro, enemigo, vacía o muro."""

    def __init__(
        self,
        posicion: Posicion,
        tipo: TipoSala = TipoSala.VACIA,
        enemigo: Optional[Enemigo] = None,
        recompensa_oro: int = 0,
        curacion: int = 0,
    ) -> None:
        self.posicion = posicion
        self.tipo = tipo
        self.enemigo = enemigo
        self.recompensa_oro = recompensa_oro
        self.curacion = curacion
        self.revelada = False
        self.visitada = False
        self.resuelta = False
        self.enemigo_derrotado = False
        self.tiempo_agotado = False
        self.tiempo_iniciado = False

    @classmethod
    def crear(cls, posicion: Posicion, tipo: TipoSala) -> "Sala":
        """Crea una sala del tipo indicado con su contenido."""
        if tipo == TipoSala.ENEMIGO:
            return cls(posicion, tipo, enemigo=Enemigo())

        if tipo == TipoSala.TESORO:
            return cls(
                posicion,
                tipo,
                recompensa_oro=ORO_TESORO,
                curacion=CURACION_TESORO,
            )

        return cls(posicion, tipo)

    @property
    def es_muro(self) -> bool:
        """Indica si la celda bloquea el paso."""
        return self.tipo == TipoSala.MURO

    @property
    def coordenadas(self) -> str:
        """Coordenadas de la celda en formato legible."""
        return f"{self.posicion.fila + 1},{self.posicion.columna + 1}"

    @property
    def estado_texto(self) -> str:
        """Describe el estado de la celda para mostrar en el mapa."""
        if self.es_muro:
            return "Muro"

        if not self.visitada:
            return "Sin explorar"

        if self.tipo == TipoSala.ENEMIGO and not self.enemigo_derrotado:
            return "Enemigo vivo"

        return "Completada"

    def revelar(self) -> None:
        """Aparta la niebla de guerra de esta celda."""
        self.revelada = True

    def entrar(self) -> None:
        """Registra que el jugador entró a la celda."""
        self.revelar()
        self.visitada = True

    def convertir_en_muro(self) -> None:
        """Convierte la celda en un muro y borra su contenido."""
        self.tipo = TipoSala.MURO
        self.enemigo = None
        self.recompensa_oro = 0
        self.curacion = 0
        self.resuelta = False
        self.visitada = False


class Castillo:
    """Cuadrícula de celdas que el jugador debe completar."""

    def __init__(
        self,
        filas: int = FILAS,
        columnas: int = COLUMNAS,
    ) -> None:
        self.filas = filas
        self.columnas = columnas
        self.inicio = Posicion(0, 0)
        self.salas: List[Sala] = self._generar()

    def _generar(self) -> List[Sala]:
        """Crea el mapa dejando conectadas todas las salas transitables."""
        salas = [
            Sala.crear(posicion, tipo)
            for posicion, tipo in zip(self._posiciones(), self._tipos())
        ]
        alcance = self._alcance(salas)

        for sala in salas:
            if not sala.es_muro and sala.posicion not in alcance:
                sala.convertir_en_muro()

        return salas

    def _posiciones(self) -> List[Posicion]:
        """Lista todas las coordenadas del castillo en orden de lectura."""
        return [
            Posicion(fila, columna)
            for fila in range(self.filas)
            for columna in range(self.columnas)
        ]

    def _tipos(self) -> List[TipoSala]:
        """Elige los tipos de celda con muros y contenido mínimo."""
        total = self.filas * self.columnas
        muros = round(total * PORCENTAJE_MUROS / 100)
        tipos = [TipoSala.ENEMIGO] * HABITACIONES_MIN_ENEMIGOS
        tipos += [TipoSala.TESORO] * HABITACIONES_MIN_TESOROS
        tipos += [TipoSala.MURO] * muros
        tipos += [
            random.choice(TIPOS_ALEATORIOS)
            for _ in range(total - len(tipos) - 1)
        ]
        random.shuffle(tipos)
        tipos.insert(0, TipoSala.VACIA)

        return tipos

    def _alcance(self, salas: List[Sala]) -> Set[Posicion]:
        """Celdas sin muro que se pueden recorrer desde el inicio."""
        indice = {sala.posicion: sala for sala in salas}
        alcance = {self.inicio}
        pendientes = deque([self.inicio])

        while pendientes:
            posicion = pendientes.popleft()

            for direccion in Direccion:
                destino = self.destino(posicion, direccion)

                if destino is None or destino not in indice:
                    continue
                if indice[destino].es_muro or destino in alcance:
                    continue

                alcance.add(destino)
                pendientes.append(destino)

        return alcance

    def contiene(self, posicion: Posicion) -> bool:
        """Indica si la coordenada está dentro del castillo."""
        return (
            0 <= posicion.fila < self.filas
            and 0 <= posicion.columna < self.columnas
        )

    def sala_en(self, posicion: Posicion) -> Optional[Sala]:
        """Devuelve la sala de la coordenada o None si está fuera."""
        if not self.contiene(posicion):
            return None

        indice = posicion.fila * self.columnas + posicion.columna
        return self.salas[indice]

    def destino(
        self,
        posicion: Posicion,
        direccion: Direccion,
    ) -> Optional[Posicion]:
        """Coordenada vecina en esa dirección, si existe."""
        paso = DESPLAZAMIENTOS[direccion]
        nuevo = Posicion(
            posicion.fila + paso.fila,
            posicion.columna + paso.columna,
        )

        return nuevo if self.contiene(nuevo) else None

    @property
    def salas_transitables(self) -> List[Sala]:
        """Salas en las que el jugador puede estar."""
        return [sala for sala in self.salas if not sala.es_muro]

    @property
    def salas_resueltas(self) -> List[Sala]:
        """Salas que el jugador ya completó."""
        return [sala for sala in self.salas if sala.resuelta]

    @property
    def muros_revelados(self) -> List[Sala]:
        """Muros que el jugador ya descubrió chocando con ellos."""
        return [sala for sala in self.salas if sala.es_muro and sala.revelada]

    @property
    def enemigos_derrotados(self) -> int:
        """Cantidad de enemigos que el jugador ya venció."""
        return sum(1 for sala in self.salas if sala.enemigo_derrotado)

    @property
    def niebla_restante(self) -> int:
        """Salas transitables que todavía están bajo la niebla."""
        pendientes = [
            sala for sala in self.salas_transitables if not sala.revelada
        ]
        return len(pendientes)

    @property
    def es_completado(self) -> bool:
        """Indica si todas las salas transitables están resueltas."""
        return all(sala.resuelta for sala in self.salas_transitables)


class Jugador:
    """Aventurero que recorre el castillo celda a celda."""

    def __init__(
        self,
        nombre: str = "Aventurero",
        posicion: Posicion = Posicion(0, 0),
        vida: int = VIDA_INICIAL,
        vida_maxima: int = VIDA_INICIAL,
        oro: int = ORO_INICIAL,
    ) -> None:
        self.nombre = nombre
        self.posicion = posicion
        self.vida = vida
        self.vida_maxima = vida_maxima
        self.oro = oro

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
        filas: int = FILAS,
        columnas: int = COLUMNAS,
    ) -> None:
        self.nombre = nombre
        self.filas = filas
        self.columnas = columnas
        self.reiniciar()

    def reiniciar(self) -> None:
        """Prepara una partida nueva en la celda de entrada."""
        self.castillo = Castillo(self.filas, self.columnas)
        self.jugador = Jugador(self.nombre, self.castillo.inicio)
        self.temporizador = Temporizador()
        self.estado = EstadoJuego.EN_JUEGO
        self.mensaje = ""
        self.tipo_mensaje = "info"
        self.entrar_sala()

    @property
    def sala_actual(self) -> Sala:
        """Sala en la que se encuentra el jugador."""
        return self.castillo.sala_en(self.jugador.posicion)

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

    def mover(self, direccion: Direccion) -> bool:
        """
        Intenta moverse a la celda vecina en esa dirección.

        Si la celda es un muro el jugador se queda donde está, pero
        el muro queda revelado en el mapa.

        Returns:
            True si el jugador cambió de celda.
            False si no pudo moverse.
        """
        if self.terminado:
            return False

        destino = self.castillo.destino(self.jugador.posicion, direccion)

        if destino is None:
            self._avisar("El castillo termina en este borde.", "info")
            return False

        sala = self.castillo.sala_en(destino)

        if sala.es_muro:
            sala.revelar()
            self._avisar(
                f"🧱 ¡Hay un muro en {sala.coordenadas}! No puedes pasar.",
                "error",
            )
            return False

        self.jugador.posicion = destino
        self.entrar_sala()

        return True

    def entrar_sala(self) -> None:
        """Registra la entrada a la celda actual y aplica su contenido."""
        sala = self.sala_actual
        sala.entrar()

        if sala.resuelta:
            self._avisar(
                f"La celda {sala.coordenadas} ya está resuelta.",
                "info",
            )
            return

        if sala.tipo == TipoSala.ENEMIGO:
            if not sala.tiempo_iniciado:
                sala.tiempo_iniciado = True
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
            self._revisar_victoria()
            return

        self._avisar("La celda está vacía. Pasa sin riesgo.", "info")
        self._revisar_victoria()

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
            self._revisar_victoria()
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
        self._revisar_victoria()

    def _revisar_victoria(self) -> None:
        """Gana la partida si ya resolvió todas las salas transitables."""
        if self.terminado or not self.castillo.es_completado:
            return

        self.estado = EstadoJuego.GANADO
        self._avisar(
            f"🏆 ¡Completaste el castillo con {self.jugador.oro} de oro!",
            "exito",
        )

    def _avisar(self, mensaje: str, tipo: str) -> None:
        """Guarda el último mensaje y el tipo de aviso."""
        self.mensaje = mensaje
        self.tipo_mensaje = tipo