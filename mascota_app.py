"""Interfaz de la mascota virtual con Streamlit."""

import streamlit as st

from mascota import (
    Accion,
    Estadistica,
    JuegoMascota,
    NOMBRE_POR_DEFECTO,
    UMBRAL_CRITICO,
    UMBRAL_BAJO,
    VALOR_MAXIMO,
)

ICONOS = {
    Estadistica.HAMBRE: "🍎",
    Estadistica.ENERGIA: "⚡",
    Estadistica.FELICIDAD: "💖",
}

AYUDA = f"""
- Las tres constantes vitales van de **0 a {VALOR_MAXIMO}**: hambre, energía
  y felicidad. Cuanto más alto, mejor.
- Cada turno eliges **Alimentar**, **Jugar** o **Dormir**. La acción sube
  una estadística y el paso del tiempo baja las otras dos al azar.
- A veces ocurre un **evento negativo** que castiga a la mascota.
- Si alguna constante llega a **0 o menos**, la mascota **se escapa** y la
  partida termina.
- Debajo de **{UMBRAL_CRITICO}** la mascota está en estado crítico, y por
  debajo de **{UMBRAL_BAJO}** cambia su diálogo de humor.
"""


def obtener_juego() -> JuegoMascota:
    """Devuelve la partida guardada en el estado de la sesión."""
    if "juego" not in st.session_state:
        nombre = st.session_state.get("nombre_mascota", NOMBRE_POR_DEFECTO)
        st.session_state.juego = JuegoMascota(nombre)
        st.session_state.partida = st.session_state.get("partida", 0) + 1

    return st.session_state.juego


def progreso(valor: int) -> float:
    """Convierte un valor de estadística en una fracción de 0.0 a 1.0."""
    return max(0.0, min(1.0, valor / VALOR_MAXIMO))


def mostrar_estadisticas(juego: JuegoMascota) -> None:
    """Muestra hambre, energía y felicidad con su barra y su icono."""
    mascotita = juego.mascota
    criticas = set(mascotita.estadisticas_criticas)
    columnas = st.columns(3)

    for columna, (estadistica, valor) in zip(columnas, mascotita.valores.items()):
        critico = estadistica in criticas

        with columna:
            st.metric(
                f"{ICONOS[estadistica]} {estadistica.value.capitalize()}",
                f"{valor} / {VALOR_MAXIMO}",
            )
            st.progress(progreso(valor))

            if critico:
                st.caption(f"⚠️ Por debajo de {UMBRAL_CRITICO}. Corre el peligro.")

    st.progress(
        sum(progreso(valor) for valor in mascotita.valores.values()) / 3,
        text="Bienestar general",
    )


def mostrar_dialogo(juego: JuegoMascota) -> None:
    """Muestra lo que dice la mascota y en qué estado está."""
    mascotita = juego.mascota

    with st.chat_message("assistant"):
        st.caption(f"**{mascotita.nombre}** · {mascotita.estado_actual.value}")
        st.markdown(mascotita.dialogo)


def mostrar_mensaje(juego: JuegoMascota) -> None:
    """Muestra el último mensaje de la partida con su color."""
    if juego.tipo_mensaje == "exito":
        st.success(juego.mensaje)
    elif juego.tipo_mensaje == "aviso":
        st.warning(juego.mensaje)
    elif juego.tipo_mensaje == "error":
        st.error(juego.mensaje)
    else:
        st.info(juego.mensaje)


def mostrar_evento(juego: JuegoMascota) -> None:
    """Muestra el evento negativo que tocó en el último turno, si hubo."""
    if not juego.evento_turno:
        return

    evento = juego.evento_turno

    with st.expander("Evento de este turno", expanded=True):
        st.warning(f"{evento.nombre} — {evento.resumen_efectos}")
        st.caption(evento.mensaje)


def mostrar_acciones(juego: JuegoMascota) -> None:
    """Muestra los tres botones de acción de la mascota."""
    st.subheader("⚡ ¿Qué hacemos ahora?")

    columnas = st.columns(3)

    for columna, accion in zip(columnas, Accion):
        with columna:
            if st.button(
                accion.value,
                key=f"accion_{accion.name}",
                use_container_width=True,
            ):
                juego.actuar(accion)
                st.rerun()

    st.caption(
        "Cada acción sube una estadística, pero el paso del tiempo "
        "baja las otras dos y a veces ocurre algo malo."
    )


def mostrar_resultado(juego: JuegoMascota) -> None:
    """Muestra el final de la partida cuando la mascota se escapa."""
    mascotita = juego.mascota

    st.subheader("💨 Game Over")
    st.error(juego.mensaje)
    st.markdown(mascotita.dialogo)

    columnas = st.columns(4)

    with columnas[0]:
        st.metric("⏱️ Turnos aguantados", juego.turno)

    for columna, estadistica in zip(columnas[1:], Estadistica):
        with columna:
            st.metric(ICONOS[estadistica], mascotita.valor(estadistica))

    if st.button(
        "🔄 Reiniciar y adoptar otra mascota",
        type="primary",
        use_container_width=True,
    ):
        st.session_state.juego = JuegoMascota(mascotita.nombre)
        st.session_state.partida += 1
        st.rerun()


def mostrar_historial(juego: JuegoMascota) -> None:
    """Muestra los últimos turnos jugados, del más nuevo al más viejo."""
    with st.expander("📜 Historial de la partida"):
        for linea in reversed(juego.historial):
            st.caption(linea)

        if not juego.historial:
            st.caption("Todavía no ha pasado nada.")


def mostrar_ayuda() -> None:
    """Muestra las reglas dentro de una caja desplegable."""
    with st.expander("❓ Reglas del juego"):
        st.markdown(AYUDA)


def main() -> None:
    """Punto de entrada de la aplicación."""
    st.set_page_config(
        page_title="Mascota Virtual",
        page_icon="🐾",
        layout="centered",
    )
    juego = obtener_juego()
    mascotita = juego.mascota

    st.title("🐾 Mascota Virtual")
    st.caption(
        "Aliméntala, juégale y hazla dormir. Cada turno el tiempo pasa y "
        "todo se desgaste: si alguna de sus tres constantes vitales llega "
        "a cero, se escapa."
    )

    with st.sidebar:
        st.header("🐾 Tu mascota")

        nombre = st.text_input(
            "Nombre",
            value=mascotita.nombre,
            key="nombre_mascota",
            disabled=juego.terminado,
        )

        if not juego.terminado and nombre.strip():
            mascotita.nombre = nombre.strip()

        st.metric("Estado", juego.estado.value)
        st.metric("⏱️ Turno", juego.turno)
        st.metric("🙂 Ánimo", mascotita.estado_actual.value)

        if st.button("🔄 Reiniciar", use_container_width=True):
            juego.reiniciar()
            st.session_state.partida += 1
            st.rerun()

    mostrar_estadisticas(juego)
    mostrar_dialogo(juego)
    mostrar_mensaje(juego)
    mostrar_evento(juego)

    if juego.terminado:
        st.divider()
        mostrar_resultado(juego)
    else:
        st.divider()
        mostrar_acciones(juego)

    st.divider()
    mostrar_historial(juego)
    mostrar_ayuda()


if __name__ == "__main__":
    main()