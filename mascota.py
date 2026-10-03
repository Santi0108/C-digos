"""Lógica de la mascota virtual.

La mascota tiene tres constantes vitales: ``hambre``, ``energia`` y
``felicidad``, todas entre 0 y 100. Cuanto más alto el valor, mejor está
la mascota; si cualquiera de ellas llega a 0 o menos, la mascota huye y
la partida termina.

Cada turno el jugador elige una acción (alimentar, jugar o dormir) que
sube una estadística. Como el tiempo sigue pasando, el resto de
estadísticas baja una cantidad aleatoria y a veces ocurre un evento
desagradable que también la castiga.

Este módulo contiene las clases del juego y no depende de Streamlit,
por lo que se puede probar de forma independiente.
"""

import random
from enum import Enum
from typing import Dict, List, Optional, Tuple

# Reglas de las constantes vitales.
VALOR_MAXIMO = 100
VALOR_INICIAL = 70
VALOR_ESCAPE = 0
UMBRAL_CRITICO = 20
UMBRAL_BAJO = 30
UMBRAL_ALTO = 70

# Reglas de cada turno.
DECAIDA_MINIMA = 4
DECAIDA_MAXIMA = 12
PORCENTAJE_EVENTO = 45
HISTORIAL_MAXIMO = 30
NOMBRE_POR_DEFECTO = "Bigotes"


class Estadistica(Enum):
    """Las tres constantes vitales de la mascota."""

    HAMBRE = "hambre"
    ENERGIA = "energia"
    FELICIDAD = "felicidad"


class Accion(Enum):
    """Lo que el jugador puede hacer en un turno."""

    ALIMENTAR = "🍎 Alimentar"
    JUGAR = "🎾 Jugar"
    DORMIR = "💤 Dormir"


class EstadoJuego(Enum):
    """Estados posibles de una partida."""

    EN_JUEGO = "En juego"
    ESCAPADA = "Escapada"


class EstadoMascota(Enum):
    """Ánimo de la mascota según sus constantes vitales."""

    ESCAPADA = "💨 Se ha escapado"
    CRITICA = "🆘 Estado crítico"
    CANSADA = "🥱 Cansada"
    CON_HAMBRE = "🍽️ Con hambre"
    TRISTE = "😢 Triste"
    FELIZ = "😄 Muy feliz"
    CONTENTA = "🙂 Contenta"


class Evento:
    """Algo malo que le pasa a la mascota durante un turno."""

    def __init__(
        self,
        nombre: str,
        mensaje: str,
        efectos: Dict[Estadistica, int],
    ) -> None:
        self.nombre = nombre
        self.mensaje = mensaje
        self.efectos = efectos

    @property
    def resumen_efectos(self) -> str:
        """Los efectos del evento en formato corto: 'energia -8'."""
        return ", ".join(
            f"{estadistica.value} {cantidad:+d}"
            for estadistica, cantidad in self.efectos.items()
        )

    def __repr__(self) -> str:
        return f"Evento({self.nombre!r})"


# Qué estadística sube cada acción, cuánto sube y las frases con las que
# se avisa al jugador.
ACCIONES: Dict[Accion, Tuple[Estadistica, int, Tuple[str, ...]]] = {
    Accion.ALIMENTAR: (
        Estadistica.HAMBRE,
        25,
        (
            "Le diste de comer y se comió todo el plato.",
            "Repitió hasta que no quedó nada en el comedero.",
            "Comió tan rápido que casi se le va por el lado equivocado.",
        ),
    ),
    Accion.JUGAR: (
        Estadistica.FELICIDAD,
        20,
        (
            "Jugaron un rato largo y no paró de reír.",
            "Persiguió la pelota hasta que se quedó sin aliento.",
            "Aprendió un truco nuevo y lo hizo tres veces seguidas.",
        ),
    ),
    Accion.DORMIR: (
        Estadistica.ENERGIA,
        30,
        (
            "Se durmió acurrucada y descansó de verdad.",
            "Roncó tranquilamente toda la siesta.",
            "Se despertó estirándose, con mejor cara.",
        ),
    ),
}

# Frases del diálogo según el ánimo de la mascota.
DIALOGOS: Dict[EstadoMascota, Tuple[str, ...]] = {
    EstadoMascota.ESCAPADA: (
        "Ya no aguanto más aquí. Me escapo, cuídate.",
        "No queda nada de mí en esta casa. Adiós.",
        "Me voy antes de que sea tarde. Suerte.",
    ),
    EstadoMascota.CRITICA: (
        "Estoy en las últimas... ¿me ayudas?",
        "Apenas me tengo en pie. Necesito algo ya.",
        "No me siento bien. De verdad.",
    ),
    EstadoMascota.CANSADA: (
        "Tengo un sueño enorme. Una siesta y estoy como nueva.",
        "Bostezo sin parar, ¿me echas una siesta?",
        "Se me cierran los ojos solos.",
    ),
    EstadoMascota.CON_HAMBRE: (
        "Mi barriga suena desde hace horas.",
        "¿Hay algo de comer? Lo que sea, pero algo.",
        "Me comería la mesa entera ahora mismo.",
    ),
    EstadoMascota.TRISTE: (
        "Llevo un rato sin hacer nada divertido.",
        "Me está faltando cariño. Del de verdad, digo.",
        "Hagamos algo juntos, porfa.",
    ),
    EstadoMascota.FELIZ: (
        "¡Estoy genial! Se siente increíble esta casa.",
        "Hoy es el mejor día del mundo.",
        "No cambiaría nada de esto. Estoy perfecta.",
    ),
    EstadoMascota.CONTENTA: (
        "Todo bien por aquí. ¿Qué hacemos ahora?",
        "Me tengo tranquila, esperando la próxima.",
        "Así está bien. Solo cuídame.",
    ),
}

# Eventos que pueden ocurrir al terminar una acción. Todos afectan
# negativamente a la mascota.
CATALOGO_EVENTOS: Tuple[Evento, ...] = (
    Evento(
        "🌧️ Lluvia repentina",
        "Empezó a llover de golpe y se metió bajo un techo goteando.",
        {Estadistica.ENERGIA: -8},
    ),
    Evento(
        "🐀 Ratón en la cocina",
        "Un ratón se comió su comida mientras no mirabas.",
        {Estadistica.FELICIDAD: -12},
    ),
    Evento(
        "🥗 Comida en mal estado",
        "El menú de hoy estaba en mal estado y no quiso ni verlo.",
        {Estadistica.HAMBRE: -15, Estadistica.FELICIDAD: -5},
    ),
    Evento(
        "🪴 Caída de maceta",
        "Se le cayó una maceta al lado y el susto fue enorme.",
        {Estadistica.FELICIDAD: -14},
    ),
    Evento(
        "🤧 Resfriada",
        "La corriente de aire le entró y ahora estornuda sin parar.",
        {Estadistica.ENERGIA: -12, Estadistica.FELICIDAD: -6},
    ),
    Evento(
        "🎉 Fiesta en la calle",
        "El ruido de la fiesta la despertó y no volvió a dormirse.",
        {Estadistica.ENERGIA: -10, Estadistica.FELICIDAD: -4},
    ),
)


class Mascota:
    """Ser vivo con hambre, energía y felicidad, y un estado de ánimo."""

    def __init__(self, nombre: str = NOMBRE_POR_DEFECTO) -> None:
        self.nombre = nombre.strip() or NOMBRE_POR_DEFECTO
        for estadistica in Estadistica:
            setattr(self, estadistica.value, VALOR_INICIAL)

    def valor(self, estadistica: Estadistica) -> int:
        """Valor actual de una estadística."""
        return getattr(self, estadistica.value)

    @property
    def valores(self) -> Dict[Estadistica, int]:
        """Todas las estadísticas con su valor actual."""
        return {
            estadistica: self.valor(estadistica)
            for estadistica in Estadistica
        }

    def bonificar(self, estadistica: Estadistica, cantidad: int) -> None:
        """Sube una estadística sin pasar de VALOR_MAXIMO."""
        self._asignar(
            estadistica,
            min(VALOR_MAXIMO, self.valor(estadistica) + cantidad),
        )

    def degradar(self, estadistica: Estadistica, cantidad: int) -> None:
        """
        Baja una estadística.

        El valor puede quedar por debajo de cero: así se ve en pantalla
        cuánto le costó a la mascota el último turno.
        """
        self._asignar(estadistica, self.valor(estadistica) - cantidad)

    def _asignar(self, estadistica: Estadistica, valor: int) -> None:
        """Guarda el valor en el atributo que tiene el mismo nombre."""
        setattr(self, estadistica.value, valor)

    def alimentar(self) -> str:
        """Le da de comer y devuelve el mensaje de lo que pasó."""
        return self._actuar(Accion.ALIMENTAR)

    def jugar(self) -> str:
        """Juega con la mascota y devuelve el mensaje de lo que pasó."""
        return self._actuar(Accion.JUGAR)

    def dormir(self) -> str:
        """Manda a la mascota a dormir y devuelve el mensaje."""
        return self._actuar(Accion.DORMIR)

    def _actuar(self, accion: Accion) -> str:
        """Sube la estadística de la acción y devuelve una frase al azar."""
        objetivo, cantidad, frases = ACCIONES[accion]
        self.bonificar(objetivo, cantidad)
        return random.choice(frases)

    def pasar_turno(self, accion: Accion) -> Dict[Estadistica, int]:
        """
        Baja al azar las estadísticas que no usa la acción.

        Returns:
            Cuánto perdió en cada estadística por el paso del tiempo.
        """
        objetivo = ACCIONES[accion][0]
        perdidas: Dict[Estadistica, int] = {}

        for estadistica in Estadistica:
            if estadistica is objetivo:
                continue

            perdida = random.randint(DECAIDA_MINIMA, DECAIDA_MAXIMA)
            self.degradar(estadistica, perdida)
            perdidas[estadistica] = perdida

        return perdidas

    def aplicar_evento(self, evento: Evento) -> None:
        """Aplica los efectos negativos de un evento."""
        for estadistica, cantidad in evento.efectos.items():
            self.degradar(estadistica, abs(cantidad))

    @property
    def fugada(self) -> bool:
        """Indica si alguna estadística llegó a cero: la mascota huye."""
        return any(valor <= VALOR_ESCAPE for valor in self.valores.values())

    @property
    def estadisticas_criticas(self) -> List[Estadistica]:
        """Estadísticas que están en las últimas."""
        return [
            estadistica
            for estadistica, valor in self.valores.items()
            if valor <= UMBRAL_CRITICO
        ]

    @property
    def estado_actual(self) -> EstadoMascota:
        """Ánimo de la mascota según el valor de sus estadísticas."""
        if self.fugada:
            return EstadoMascota.ESCAPADA

        if self.estadisticas_criticas:
            return EstadoMascota.CRITICA

        if self.valor(Estadistica.ENERGIA) <= UMBRAL_BAJO:
            return EstadoMascota.CANSADA

        if self.valor(Estadistica.HAMBRE) <= UMBRAL_BAJO:
            return EstadoMascota.CON_HAMBRE

        if self.valor(Estadistica.FELICIDAD) <= UMBRAL_BAJO:
            return EstadoMascota.TRISTE

        if all(valor >= UMBRAL_ALTO for valor in self.valores.values()):
            return EstadoMascota.FELIZ

        return EstadoMascota.CONTENTA

    @property
    def dialogo(self) -> str:
        """Lo que dice la mascota en este momento."""
        return random.choice(DIALOGOS[self.estado_actual])


class JuegoMascota:
    """Partida que lleva las cuentas y decide cuándo termina."""

    def __init__(self, nombre: str = NOMBRE_POR_DEFECTO) -> None:
        self.nombre = nombre
        self.reiniciar()

    def reiniciar(self) -> None:
        """Prepara una partida nueva con la mascota en buen estado."""
        self.mascota = Mascota(self.nombre)
        self.turno = 0
        self.estado = EstadoJuego.EN_JUEGO
        self.historial: List[str] = []
        self.evento_turno: Optional[Evento] = None
        self.mensaje = f"¡{self.mascota.nombre} acaba de llegar a casa!"
        self.tipo_mensaje = "info"

    @property
    def terminado(self) -> bool:
        """Indica si la mascota ya huyó y la partida terminó."""
        return self.estado is not EstadoJuego.EN_JUEGO

    def actuar(self, accion: Accion) -> None:
        """
        Juega un turno completo con la acción indicada.

        El turno sube una estadística, baja las otras dos por el paso
        del tiempo, lanza un evento al azar y revisa si la mascota
        escapó.

        Args:
            accion: La acción que eligió el jugador.
        """
        if self.terminado:
            return

        self.turno += 1
        self.evento_turno = None

        self._registrar_turno(self._aplicar_accion(accion))
        self._registrar_turno(self._pasar_turno(accion))
        self._registrar_turno(self._lanzar_evento())
        self._revisar_fuga()

    def _aplicar_accion(self, accion: Accion) -> str:
        """Ejecuta la acción y avisa con el mensaje de la mascota."""
        metodos = {
            Accion.ALIMENTAR: self.mascota.alimentar,
            Accion.JUGAR: self.mascota.jugar,
            Accion.DORMIR: self.mascota.dormir,
        }
        _, cantidad, _ = ACCIONES[accion]
        mensaje = metodos[accion]()
        self.mensaje = f"{accion.value}: {mensaje}"
        self.tipo_mensaje = "exito"

        return f"{accion.value} (+{cantidad}) {mensaje}"

    def _pasar_turno(self, accion: Accion) -> str:
        """Baja las estadísticas inactivas y describe el desgaste."""
        perdidas = self.mascota.pasar_turno(accion)
        detalle = ", ".join(
            f"{estadistica.value} -{cantidad}"
            for estadistica, cantidad in perdidas.items()
        )

        return f"Mientras tanto se le pasó el tiempo: {detalle}."

    def _lanzar_evento(self) -> Optional[str]:
        """Puede asignar un evento negativo al turno."""
        if random.randint(1, 100) > PORCENTAJE_EVENTO:
            return None

        evento = random.choice(CATALOGO_EVENTOS)
        self.mascota.aplicar_evento(evento)
        self.evento_turno = evento
        self.mensaje = f"{evento.nombre}: {evento.mensaje}"
        self.tipo_mensaje = "aviso"

        return f"{evento.nombre}. {evento.mensaje} ({evento.resumen_efectos})"

    def _revisar_fuga(self) -> Optional[str]:
        """Termina la partida si alguna estadística llegó a cero."""
        if not self.mascota.fugada:
            return None

        self.estado = EstadoJuego.ESCAPADA

        causal = ", ".join(
            estadistica.value
            for estadistica in self.mascota.estadisticas_criticas
        )
        self.mensaje = (
            f"💨 {self.mascota.nombre} se escapó. No aguantaba más: "
            f"le faltaron puntos de {causal}."
        )
        self.tipo_mensaje = "error"

        return self.mensaje

    def _registrar_turno(self, entrada: Optional[str]) -> None:
        """Suma una línea al historial del turno y lo recorta."""
        if not entrada:
            return

        self.historial.append(f"Turno {self.turno} · {entrada}")
        del self.historial[:-HISTORIAL_MAXIMO]