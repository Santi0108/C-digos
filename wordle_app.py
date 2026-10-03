"""Interfaz del juego Wordle con Streamlit."""

from typing import Dict, List, Optional, Tuple

import streamlit as st

from wordle import (
    COLOR_AUSENTE,
    COLOR_BORDE,
    COLOR_BORDE_VACIA,
    COLOR_CORRECTA,
    COLOR_PRESENTE,
    COLOR_TECLADO,
    COLOR_TECLADO_BORDE,
    COLOR_VACIA,
    INTENTOS_MAXIMOS,
    LONGITUD,
    EstadoLetra,
    JuegoWordle,
)

FILAS_TECLADO: Tuple[str, ...] = (
    "QWERTYUIOP",
    "ASDFGHJKL",
    "ZXCVBNM",
)

TECLA_BORRAR = "⌫"
MAX_TECLAS = len(FILAS_TECLADO[0])

CLASES: Dict[EstadoLetra, str] = {
    EstadoLetra.CORRECTA: "casilla-correcta",
    EstadoLetra.PRESENTE: "casilla-presente",
    EstadoLetra.AUSENTE: "casilla-ausente",
}

COLORES: Dict[EstadoLetra, str] = {
    EstadoLetra.CORRECTA: COLOR_CORRECTA,
    EstadoLetra.PRESENTE: COLOR_PRESENTE,
    EstadoLetra.AUSENTE: COLOR_AUSENTE,
}

AYUDA = f"""
- Adivina la palabra secreta de **{LONGITUD} letras** en un máximo de
  **{INTENTOS_MAXIMOS} intentos**.
- 🟩 **Verde**: la letra está en su posición.
- 🟨 **Amarillo**: la letra existe, pero en otro sitio.
- ⬜ **Gris**: la letra no está en la palabra.
- Solo se aceptan palabras del diccionario, en mayúsculas y sin ñ ni
  tildes. Un intento no válido no gasta un intento.
- Las letras del teclado se van pintando con el mejor color que hayan
  tenido: el verde siempre gana al amarillo, y el amarillo al gris.
"""


def construir_estilos() -> str:
    """
    Devuelve el CSS del tablero y del teclado.

    Los colores salen de wordle.py, así que el tablero y el teclado
    usan siempre la misma paleta que la lógica del juego.
    """
    reglas_teclado = "\n".join(
        f"""
        div[class*="st-key-tecla_{estado.name.lower()}"] button,
        button[class*="st-key-tecla_{estado.name.lower()}"] {{
            background-color: {color};
            border-color: {color};
            color: #ffffff;
            font-weight: 700;
        }}"""
        for estado, color in COLORES.items()
    )

    return f"""
    <style>
    .tablero-wordle {{
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 6px;
        margin-bottom: 1rem;
    }}
    .fila-wordle {{
        display: flex;
        gap: 6px;
    }}
    .casilla-wordle {{
        width: 58px;
        height: 58px;
        border-radius: 6px;
        border: 2px solid {COLOR_BORDE};
        background-color: {COLOR_VACIA};
        color: #ffffff;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 30px;
        font-weight: 700;
    }}
    .casilla-correcta {{
        background-color: {COLOR_CORRECTA};
        border-color: {COLOR_CORRECTA};
    }}
    .casilla-presente {{
        background-color: {COLOR_PRESENTE};
        border-color: {COLOR_PRESENTE};
    }}
    .casilla-ausente {{
        background-color: {COLOR_AUSENTE};
        border-color: {COLOR_AUSENTE};
    }}
    .casilla-vacia {{
        background-color: transparent;
        border-color: {COLOR_BORDE_VACIA};
    }}
    div[class*="st-key-tecla_neutra"] button,
    button[class*="st-key-tecla_neutra"] {{
        background-color: {COLOR_TECLADO};
        border-color: {COLOR_TECLADO_BORDE};
        color: #ffffff;
        font-weight: 700;
    }}
    div[class*="st-key-borrar"] button,
    button[class*="st-key-borrar"] {{
        background-color: transparent;
        border-color: {COLOR_TECLADO_BORDE};
        color: {COLOR_TECLADO};
    }}
    {reglas_teclado}
    </style>
    """


def nueva_partida() -> None:
    """Guarda una partida nueva en el estado de la sesión."""
    st.session_state.juego = JuegoWordle()
    st.session_state.partida = st.session_state.get("partida", 0) + 1
    st.session_state.entrada = ""
    st.session_state.revision = 0


def obtener_juego() -> JuegoWordle:
    """Devuelve la partida guardada en el estado de la sesión."""
    if "juego" not in st.session_state:
        nueva_partida()

    return st.session_state.juego


def reiniciar_juego() -> None:
    """Empieza una partida nueva y limpia lo escrito por el jugador."""
    nueva_partida()
    st.rerun()


def obtener_entrada() -> str:
    """Devuelve lo que el jugador lleva escrito en el campo de texto."""
    return st.session_state.get(clave_entrada(), "")


def clave_entrada() -> str:
    """
    Devuelve el nombre de la clave del campo de texto.

    La clave lleva un número de revisión: al cambiarla Streamlit crea
    un campo nuevo y vacío, que es la forma de vaciarlo sin tocar un
    widget que ya se ha creado.
    """
    return (
        f"entrada_{st.session_state.partida}"
        f"_{st.session_state.revision}"
    )


def escribir_entrada(texto: str) -> None:
    """Guarda lo escrito y prepara un campo de texto nuevo y vacío."""
    st.session_state.entrada = texto[:LONGITUD]
    st.session_state.revision += 1


def agregar_letra(letra: str) -> None:
    """Añade una letra al final de la palabra en construcción."""
    escribir_entrada(obtener_entrada() + letra)


def borrar_letra() -> None:
    """Quita la última letra de la palabra en construcción."""
    escribir_entrada(obtener_entrada()[:-1])


def construir_fila(
    palabra: str,
    estados: Tuple[Optional[EstadoLetra], ...],
) -> str:
    """Convierte una fila de cinco letras en HTML con sus clases."""
    casillas = "".join(
        '<div class="casilla-wordle '
        f'{CLASES[estado] if estado else "casilla-vacia"}">{letra}</div>'
        for letra, estado in zip(palabra, estados)
    )

    return f'<div class="fila-wordle">{casillas}</div>'


def construir_tablero(juego: JuegoWordle) -> str:
    """Convierte el historial de la partida en el tablero completo."""
    filas = [
        construir_fila(intento.palabra, intento.estados)
        for intento in juego.intentos
    ]
    filas += [
        construir_fila(" " * LONGITUD, (None,) * LONGITUD)
        for _ in range(juego.intentos_restantes)
    ]

    return f'<div class="tablero-wordle">{"".join(filas)}</div>'


def mostrar_tablero(juego: JuegoWordle) -> None:
    """Muestra los intentos jugados y las casillas que quedan libres."""
    st.markdown(construir_tablero(juego), unsafe_allow_html=True)


def mostrar_leyenda() -> None:
    """Explica qué significa cada color del tablero."""
    st.caption(
        "🟩 Correcta en su posición · "
        "🟨 Existe pero en otro sitio · "
        "⬜ No está en la palabra"
    )


def mostrar_teclado(juego: JuegoWordle) -> None:
    """
    Muestra el teclado en pantalla.

    Cada tecla es un botón que añade su letra al campo de texto, y el
    color es el mejor estado que esa letra haya tenido en la partida.
    """
    st.subheader("⌨️ Teclado")

    for posicion, fila in enumerate(FILAS_TECLADO):
        teclas: List[str] = list(fila)

        if posicion == len(FILAS_TECLADO) - 1:
            teclas.append(TECLA_BORRAR)

        columnas = st.columns(MAX_TECLAS)
        relleno = (MAX_TECLAS - len(teclas)) // 2

        for indice, tecla in enumerate(teclas):
            with columnas[relleno + indice]:
                if tecla == TECLA_BORRAR:
                    if st.button(
                        TECLA_BORRAR,
                        key="borrar",
                        help="Borrar la última letra",
                        use_container_width=True,
                    ):
                        borrar_letra()
                        st.rerun()
                    continue

                estado = juego.teclado.get(tecla)
                nombre = estado.name.lower() if estado else "neutra"

                if st.button(
                    tecla,
                    key=f"tecla_{tecla}_{nombre}",
                    use_container_width=True,
                ):
                    agregar_letra(tecla)
                    st.rerun()


def mostrar_mensaje(juego: JuegoWordle) -> None:
    """Muestra el último mensaje de la partida con su color."""
    if juego.tipo_mensaje == "exito":
        st.success(juego.mensaje)
    elif juego.tipo_mensaje == "error":
        st.error(juego.mensaje)
    elif juego.tipo_mensaje == "aviso":
        st.warning(juego.mensaje)
    else:
        st.info(juego.mensaje)


def mostrar_entrada(juego: JuegoWordle) -> None:
    """Muestra el tablero, el campo de palabra y el teclado."""
    mostrar_tablero(juego)
    mostrar_leyenda()

    with st.form("form_intento", clear_on_submit=True):
        st.text_input(
            "Tu palabra",
            max_chars=LONGITUD,
            value=st.session_state.entrada,
            key=clave_entrada(),
        )
        enviar = st.form_submit_button(
            "🎯 Enviar palabra", use_container_width=True
        )

    if enviar:
        palabra = obtener_entrada()
        intento = juego.intentar(palabra)
        escribir_entrada(palabra if intento is None else "")
        st.rerun()

    mostrar_mensaje(juego)
    mostrar_teclado(juego)


def mostrar_resultado(juego: JuegoWordle) -> None:
    """Muestra el tablero final, el resultado y deja reiniciar."""
    mostrar_tablero(juego)
    mostrar_leyenda()
    st.divider()

    if juego.ganado:
        st.success(f"🎉 ¡Ganaste! Adivinaste {juego.palabra_secreta}.")
    else:
        st.error(
            f"💀 Perdiste. La palabra secreta era {juego.palabra_secreta}."
        )

    columnas = st.columns(2)

    with columnas[0]:
        st.metric("✅ Intentos usados", len(juego.intentos))

    with columnas[1]:
        st.metric("📖 Palabras del diccionario", len(juego.palabras))

    st.button(
        "🔄 Jugar otra vez",
        type="primary",
        use_container_width=True,
        on_click=reiniciar_juego,
    )


def mostrar_ayuda() -> None:
    """Muestra las reglas dentro de una caja desplegable."""
    with st.expander("❓ Reglas del juego"):
        st.markdown(AYUDA)


def main() -> None:
    """Punto de entrada de la aplicación."""
    st.set_page_config(
        page_title="Wordle",
        page_icon="🟩",
        layout="centered",
    )
    st.markdown(construir_estilos(), unsafe_allow_html=True)
    juego = obtener_juego()

    st.title("🟩 Wordle")
    st.caption(
        "Adivina la palabra secreta de cinco letras antes de quedarte "
        "sin intentos."
    )

    with st.sidebar:
        st.header("🎯 Partida")
        st.metric("Estado", juego.estado.value)
        st.metric(
            "🔤 Intentos",
            f"{len(juego.intentos)} / {juego.intentos_maximos}",
        )
        st.progress(juego.progreso, text="Intentos usados")

        if st.button("🔄 Reiniciar", use_container_width=True):
            reiniciar_juego()

    if juego.terminado:
        mostrar_resultado(juego)
    else:
        mostrar_entrada(juego)

    st.divider()
    mostrar_ayuda()


if __name__ == "__main__":
    main()