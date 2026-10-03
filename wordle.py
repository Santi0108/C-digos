"""Lógica del juego Wordle.

El jugador tiene seis intentos para descubrir una palabra secreta de
cinco letras. Cada intento devuelve el estado de cada una de sus
letras: correcta en su posición (verde), correcta pero desplazada
(amarillo) o inexistente en la palabra (gris).

Este módulo contiene las clases del juego y no depende de Streamlit,
por lo que se puede probar de forma independiente.
"""

import random
import sys
from enum import Enum
from typing import Dict, List, Optional, Sequence, Tuple

# Reglas de la partida.
LONGITUD = 5
INTENTOS_MAXIMOS = 6

# Colores de las casillas y del tablero.
COLOR_CORRECTA = "#538d4e"
COLOR_PRESENTE = "#b59f3b"
COLOR_AUSENTE = "#3a3a3c"
COLOR_VACIA = "#121213"
COLOR_BORDE = "#3a3a3c"
COLOR_BORDE_VACIA = "#3a3a3c"
COLOR_TECLADO = "#818384"
COLOR_TECLADO_BORDE = "#565758"

LETRAS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

# Diccionario de la partida: palabras de cinco letras sin ñ ni tildes.
PALABRAS: Tuple[str, ...] = (
    "ACERO", "ACTOR", "ACUSE", "ADOBE", "AGUAS", "AGUJA", "AHORA",
    "ALIAS", "ALDEA", "ALTAR", "ALZAR", "AMIGO", "ANCHO", "ANCLA",
    "ANUAL", "ARDOR", "AREPA", "ARENA", "ARMAR", "AROMA", "ARROZ",
    "ASILO", "ASTRO", "ATOMO", "AVEJA", "AVION", "AVISO", "AYUDA",
    "BAILE", "BAJAR", "BANCO", "BANDA", "BARCO", "BARRA", "BASTO",
    "BEBER", "BOLSA", "BOMBA", "BOTON", "BRAZO", "BUENO", "BUSCA",
    "BUSTO", "CALMA", "CALOR", "CAMPO", "CANAL", "CANJE", "CANTA",
    "CANTO", "CAPAZ", "CARGA", "CARNE", "CARPA", "CARTA", "CASCO",
    "CERDO", "CIELO", "CINCO", "CIRCO", "CIVIL", "CLARO", "CLASE",
    "CLAVO", "COCHE", "COFRE", "COLOR", "COMER", "CONDE", "CORTE",
    "CREMA", "CUEVA", "CURVA", "DEDAL", "DEUDA", "DISCO", "DOBLE",
    "DOLOR", "DORAR", "DRAMA", "DUCHA", "DUELO", "DULCE", "DUNAS",
    "DUQUE", "DURAR", "ECHAR", "ELITE", "ENANO", "ENERO", "ESTAR",
    "FABLA", "FALDA", "FALLO", "FALSO", "FAROL", "FECHA", "FELIZ",
    "FERIA", "FILME", "FINCA", "FIRME", "FLACO", "FORMA", "FORRO",
    "FRENO", "FRESA", "FRITO", "FRUTA", "FUEGO", "FUERA", "FUMAR",
    "GAFAS", "GALLO", "GANSO", "GENTE", "GESTO", "GLOBO", "GORRA",
    "GRADA", "GRANO", "GRASA", "GRITO", "GRUPO", "GUISO", "GUSTO",
    "HABER", "HACER", "HACHA", "HECHO", "HIELO", "HOGAR", "HORCA",
    "HORNO", "HUESO", "HUEVO", "HUMOR", "HURTO", "ICONO", "IDEAL",
    "IGUAL", "JARRA", "JAULA", "JUEGO", "JUGAR", "JUNCO", "JUNTO",
    "JURAR", "JUSTO", "LABIO", "LACRE", "LARGO", "LAVAR", "LECHE",
    "LECHO", "LIBRE", "LIBRO", "LINDO", "LISTA", "LITRO", "LLAMA",
    "LLANO", "LLAVE", "LLENO", "LONJA", "LUCHA", "LUCIR", "LUNES",
    "MADRE", "MAGIA", "MALVA", "MANCO", "MANSO", "MANTA", "MARCA",
    "MARCO", "MAREA", "MARZO", "MATAR", "MATIZ", "MAYOR", "MEDIA",
    "MEDIR", "MEJOR", "MENTA", "MENTE", "MESAS", "METAL", "METRO",
    "MIEDO", "MILPA", "MIMAR", "MIXTO", "MODAL", "MONTE", "MORAL",
    "MORIR", "MORRO", "MOSCA", "MOTOR", "MOVER", "MUCHO", "MUELA",
    "MUJER", "MUNDO", "MUSEO", "NACER", "NADIE", "NARIZ", "NAVAL",
    "NIEVE", "NIVEL", "NOBLE", "NOCHE", "NORTE", "NUBES", "NUCAS",
    "NUEVE", "NUNCA", "OBESO", "OLIVA", "OLIVO", "OMEGA", "OREJA",
    "PACTO", "PADRE", "PALCO", "PALMA", "PANAL", "PANEL", "PANZA",
    "PAPEL", "PARAR", "PARED", "PARIR", "PARTE", "PASAR", "PASEO",
    "PASTA", "PAUSA", "PECES", "PECHO", "PEDIR", "PEGAR", "PEINE",
    "PELAR", "PERAL", "PERLA", "PERRO", "PESCA", "PIEZA", "PILAR",
    "PINAR", "PIOJO", "PIPAS", "PISAR", "PLACA", "PLATA", "PLATO",
    "PLAYA", "PLAZA", "PLOMO", "PLUMA", "POBRE", "PODER", "POETA",
    "POLEN", "POLIO", "POLVO", "PONER", "PONTE", "POSAR", "POSTE",
    "POTRO", "PRADO", "PRISA", "PULGA", "PULIR", "PULPO", "PUNTA",
    "PUNTO", "QUESO", "QUITA", "RABIA", "RAFIA", "RANGO", "RAPTO",
    "RASGO", "RASPA", "RECTO", "REGAR", "REINA", "REINO", "RELOJ",
    "RENTA", "RESTO", "RITMO", "RIVAL", "ROBAR", "ROBLE", "RODEO",
    "RONCO", "RONDA", "ROSCA", "RUEDA", "RUGIR", "RUINA", "RUMBO",
    "SABER", "SABOR", "SACAR", "SALAS", "SALIR", "SALUD", "SALVA",
    "SANTO", "SAQUE", "SELLO", "SELVA", "SERIE", "SIETE", "SIGLO",
    "SIGNO", "SILLA", "SIMIO", "SITIO", "SOBRE", "SOCIO", "SOLAR",
    "SOLER", "SONAR", "SORDO", "SUAVE", "SUBIR", "SUCIO", "SUDOR",
    "SUELA", "SUMAR", "SURCO", "SUSTO", "TABLA", "TALCO", "TALLO",
    "TANTO", "TARDE", "TAREA", "TARJA", "TARRO", "TARSO", "TECHO",
    "TECLA", "TENER", "TENIS", "TENOR", "TESIS", "TEXTO", "TILDE",
    "TINTA", "TINTO", "TIRAR", "TOBIO", "TOCAR", "TOMAR", "TONTO",
    "TOQUE", "TORRE", "TORSO", "TOSER", "TOTAL", "TRAJE", "TRAMO",
    "TRAPO", "TRECE", "TRIGO", "TROZO", "TRUCO", "TUMBO", "TURNO",
    "VACAS", "VAGAR", "VALER", "VALOR", "VALVA", "VAPOR", "VARAR",
    "VASTO", "VECES", "VELOZ", "VERSO", "VIAJE", "VICIO", "VIDEO",
    "VIEJO", "VILLA", "VIRUS", "VISTA", "VIVAZ", "VIVIR", "VOLAR",
    "VORAZ", "VOTAR", "VOTOS", "VUELA", "VUELO", "YEGUA", "YERBA",
    "YERMO", "ZANJA", "ZARZA", "ZORRO", "ZUMOS", "ZURDO",
)


class EstadoLetra(Enum):
    """Lo que se sabe de una letra después de un intento."""

    CORRECTA = "Correcta"
    PRESENTE = "Presente"
    AUSENTE = "Ausente"


class EstadoJuego(Enum):
    """Estados posibles de una partida."""

    EN_JUEGO = "En juego"
    GANADO = "Ganaste"
    PERDIDO = "Perdiste"


# Emoji de cada estado, para la leyenda y el tablero de la consola.
INDICADORES: Dict[EstadoLetra, str] = {
    EstadoLetra.CORRECTA: "🟩",
    EstadoLetra.PRESENTE: "🟨",
    EstadoLetra.AUSENTE: "⬜",
}

# A mayor prioridad, másinfo guarda el teclado. Una letra que sale verde
# en un intento no vuelve a ser amarilla ni gris en los siguientes.
PRIORIDAD: Dict[EstadoLetra, int] = {
    EstadoLetra.CORRECTA: 2,
    EstadoLetra.PRESENTE: 1,
    EstadoLetra.AUSENTE: 0,
}


class Intento:
    """Palabra que escribió el jugador con el estado de cada letra."""

    def __init__(
        self,
        numero: int,
        palabra: str,
        estados: Tuple[EstadoLetra, ...],
    ) -> None:
        self.numero = numero
        self.palabra = palabra
        self.estados = estados

    @property
    def es_ganador(self) -> bool:
        """Indica si el intento adivinó la palabra secreta."""
        return all(estado is EstadoLetra.CORRECTA for estado in self.estados)

    @property
    def indicadores(self) -> str:
        """Emojis 🟩🟨⬜ en el mismo orden que las letras del intento."""
        return " ".join(INDICADORES[estado] for estado in self.estados)

    def __repr__(self) -> str:
        return f"Intento({self.numero}, {self.palabra!r})"


class JuegoWordle:
    """Partida con la palabra secreta, los intentos y el estado."""

    def __init__(
        self,
        palabras: Sequence[str] = PALABRAS,
        intentos_maximos: int = INTENTOS_MAXIMOS,
    ) -> None:
        self.palabras: Tuple[str, ...] = tuple(palabras)
        self.intentos_maximos = intentos_maximos
        self.intentos: List[Intento] = []
        self.teclado: Dict[str, EstadoLetra] = {}
        self.reiniciar()

    def reiniciar(self, palabra_secreta: Optional[str] = None) -> None:
        """
        Prepara una partida nueva y borra todo lo anterior.

        Args:
            palabra_secreta: Palabra fija para la partida. Si no se
                indica, se elige una al azar del diccionario.
        """
        self.palabra_secreta = palabra_secreta or random.choice(self.palabras)
        self.intentos = []
        self.teclado = {}
        self.estado = EstadoJuego.EN_JUEGO
        self.mensaje = (
            f"La palabra secreta tiene {LONGITUD} letras. ¡Suerte!"
        )
        self.tipo_mensaje = "info"

    @property
    def terminado(self) -> bool:
        """Indica si la partida ya terminó."""
        return self.estado is not EstadoJuego.EN_JUEGO

    @property
    def ganado(self) -> bool:
        """Indica si el jugador adivinó la palabra secreta."""
        return self.estado is EstadoJuego.GANADO

    @property
    def intentos_restantes(self) -> int:
        """Intentos que le quedan al jugador."""
        return max(0, self.intentos_maximos - len(self.intentos))

    @property
    def progreso(self) -> float:
        """Fracción de intentos ya usados, entre 0.0 y 1.0."""
        if not self.intentos_maximos:
            return 0.0

        return min(1.0, len(self.intentos) / self.intentos_maximos)

    @property
    def palabras_usadas(self) -> Tuple[str, ...]:
        """Palabras con las que ya se ha intentado."""
        return tuple(intento.palabra for intento in self.intentos)

    @staticmethod
    def normalizar(texto: str) -> str:
        """Pone en mayúsculas y quita los espacios sobrantes."""
        return texto.strip().upper()

    @staticmethod
    def evaluar(
        palabra: str,
        secreta: str,
    ) -> Tuple[EstadoLetra, ...]:
        """
        Devuelve el estado de cada letra de la palabra comparada con
        la secreta.

        Primero se marcan las letras en su sitio, y después se
        reparen las que sobran en otra posición. Así una letra
        repetida en el intento no se pinta de amarilla más veces que
        aparece en la palabra secreta.

        Args:
            palabra: La palabra que escribió el jugador.
            secreta: La palabra que hay que adivinar.

        Returns:
            Un estado por cada letra de la palabra.
        """
        sobrantes: Dict[str, int] = {}

        for letra in secreta:
            sobrantes[letra] = sobrantes.get(letra, 0) + 1

        estados = [EstadoLetra.AUSENTE] * LONGITUD

        for indice, letra in enumerate(palabra):
            if letra != secreta[indice]:
                continue

            estados[indice] = EstadoLetra.CORRECTA
            sobrantes[letra] -= 1

        for indice, letra in enumerate(palabra):
            if estados[indice] is EstadoLetra.CORRECTA:
                continue

            if sobrantes.get(letra, 0) <= 0:
                continue

            estados[indice] = EstadoLetra.PRESENTE
            sobrantes[letra] -= 1

        return tuple(estados)

    def intentar(self, palabra: str) -> Optional[Intento]:
        """
        Registra un intento del jugador y actualiza el estado.

        Una palabra que no cumple las reglas no se registra y no gasta
        ningún intento: solo deja un aviso en el mensaje del juego.

        Args:
            palabra: Lo que escribió el jugador.

        Returns:
            El intento registrado, o None si la palabra se rechazó.
        """
        if self.terminado:
            self._avisar("La partida ya terminó.", "aviso")
            return None

        normalizada = self.normalizar(palabra)

        if len(normalizada) != LONGITUD:
            self._avisar(
                f"La palabra debe tener {LONGITUD} letras.",
                "error",
            )
            return None

        if not all(letra in LETRAS for letra in normalizada):
            self._avisar("Usa solo letras del abecedario.", "error")
            return None

        if normalizada not in self.palabras:
            self._avisar(
                f"«{normalizada}» no está en el diccionario.",
                "error",
            )
            return None

        if normalizada in self.palabras_usadas:
            self._avisar(f"Ya intentaste {normalizada}.", "aviso")
            return None

        intento = Intento(
            len(self.intentos) + 1,
            normalizada,
            self.evaluar(normalizada, self.palabra_secreta),
        )

        self.intentos.append(intento)
        self._marcar_teclado(intento)
        self._revisar_estado(intento)

        return intento

    def _marcar_teclado(self, intento: Intento) -> None:
        """Guarda el mejor estado conocido de cada letra del intento."""
        for letra, estado in zip(intento.palabra, intento.estados):
            anterior = self.teclado.get(letra)

            if anterior is None or PRIORIDAD[estado] > PRIORIDAD[anterior]:
                self.teclado[letra] = estado

    def _revisar_estado(self, intento: Intento) -> None:
        """Decide si la partida sigue, si se ganó o si se perdió."""
        if intento.es_ganador:
            self.estado = EstadoJuego.GANADO
            self._avisar(
                f"🎉 ¡Ganaste en {intento.numero} "
                f"{self._intentos_en_texto(intento.numero)}!",
                "exito",
            )
            return

        if self.intentos_restantes == 0:
            self.estado = EstadoJuego.PERDIDO
            self._avisar(
                f"💀 Se acabaron los intentos. "
                f"La palabra era {self.palabra_secreta}.",
                "error",
            )
            return

        self._avisar(
            f"Intento {intento.numero} de {self.intentos_maximos}. "
            f"Quedan {self.intentos_restantes}.",
            "info",
        )

    def _intentos_en_texto(self, numero: int) -> str:
        """Escribe un número de intentos en singular o en plural."""
        return "intento" if numero == 1 else "intentos"

    def _avisar(self, mensaje: str, tipo: str) -> None:
        """Guarda el último mensaje y el tipo de aviso."""
        self.mensaje = mensaje
        self.tipo_mensaje = tipo


def jugar_partida(juego: JuegoWordle, palabras: Sequence[str]) -> None:
    """Envía las palabras indicadas e imprime cada intento."""
    for palabra in palabras:
        if juego.terminado:
            break

        juego.intentar(palabra)
        ultimo = juego.intentos[-1]
        print(f"  {ultimo.palabra}   {ultimo.indicadores}")

    print(f"\n  {juego.mensaje}")


def preparar_consola() -> None:
    """Permite que la consola de Windows imprima los emoji del tablero."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def main() -> None:
    """Demuestra las clases del juego jugando tres partidas."""
    preparar_consola()
    juego = JuegoWordle()

    print("\n🟩 Wordle: adivina la palabra secreta de 5 letras")
    print(f"  Diccionario: {len(juego.palabras)} palabras.")

    print("\nPalabras que se rechazan sin gastar intento:")
    for palabra in ("casa", "ñandu", "kkkkk"):
        juego.intentar(palabra)
        print(f"  {palabra:<8} -> {juego.mensaje}")

    print(f"\nIntentos restantes: {juego.intentos_restantes}")

    print("\nPartida 1: se gana en el tercer intento")
    juego.reiniciar("CASCO")
    jugar_partida(juego, ("GRUPO", "NUBES", "CASCO"))

    print("\nPartida 2: letras repetidas (SALAS contra LLAMA)")
    juego.reiniciar("LLAMA")
    jugar_partida(juego, ("SALAS", "LLAMA"))

    print("\nPartida 3: se pierden los seis intentos")
    juego.reiniciar("PERRO")
    jugar_partida(
        juego,
        ("CASCO", "NUBES", "MADRE", "LUNES", "CUEVA", "PLATO"),
    )

    juego.intentar("PERRO")
    print(f"\n  {juego.mensaje}\n")


if __name__ == "__main__":
    main()